import json
from django.shortcuts import render, redirect, get_object_or_404
from .models import Realm, LandUnit, PopulationUnit, LandUnitType, MINERAL_SUBTYPES, RealmScale, OngoingAction
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from .forms import RealmInfoForm, TreasuryForm, ResourcesForm, LandUnitForm, PopulationUnitForm, PopulationRace
from django.forms import formset_factory, modelformset_factory
from django.urls import reverse
from django.views.decorators.http import require_POST
import random
from .game_logic import generic_actions, spring_actions, summer_actions, fall_actions, winter_actions
from .game_logic.action_definitions import SEASONAL_ACTIONS, ALL_GAME_ACTIONS, ACTION_HANDLERS
from django.core.serializers import serialize
from django.utils.safestring import mark_safe

@require_POST
def delete_realm(request, name):
    realm = get_object_or_404(Realm, name=name)
    realm.delete()  # This will cascade delete if you set up ForeignKeys with on_delete=models.CASCADE
    return redirect('realm_list')

def _assign_mineral_type():
    roll = random.randint(1, 100)
    total = 0
    for mineral, chance in MINERAL_SUBTYPES:
        total += chance
        if roll <= total:
            return mineral
    return "Iron"  # Default if no match

def get_realm_scales_json(request):
    realm_scales = RealmScale.objects.all().values('id', 'name')  # Fetch id and name
    return JsonResponse(list(realm_scales), safe=False)

def realm_create_automatic(request):
    if request.method == 'GET':
        domain_type = request.GET.get('domain')
        realm_name_input = request.GET.get('realm_name')
        ruler_name = request.GET.get('ruler_name')
        realm_scale_id = request.GET.get('realm_scale_id')  # Get the scale ID

        if domain_type in ["Standard", "Coastal", "Desert", "Forest", "Hills", "Mountains"]:
            name_prefixes = []
            starting_land_units_config = {}

            if domain_type == "Standard":
                name_prefixes = ["Central", "Green", "Prosperous"]
                starting_land_units_config = {
                    "Forest": 5,
                    "Hills - Stone": 1,
                    "Plains": 10,
                    "Mountains - Stone": 0,
                    "Ruins": 0,
                    "Swamp": 1,
                    "Wasteland": 0,
                    "Water": 2,
                    "Hills - Minerals": 1,
                    "Mountains - Minerals": 0,
                }
            elif domain_type == "Coastal":
                name_prefixes = ["Seaside", "Azure", "Port"]
                starting_land_units_config = {
                    "Forest": 2,
                    "Hills - Stone": 0,
                    "Plains": 7,
                    "Mountains - Stone": 0,
                    "Ruins": 0,
                    "Swamp": 3,
                    "Wasteland": 0,
                    "Water": 8,
                    "Hills - Minerals": 0,
                    "Mountains - Minerals": 0,
                }
            elif domain_type == "Desert":
                name_prefixes = ["Sandy", "Oasis", "Sunstone"]
                starting_land_units_config = {
                    "Forest": 2,
                    "Hills - Stone": 1,
                    "Plains": 8,
                    "Mountains - Stone": 1,
                    "Ruins": 0,
                    "Swamp": 0,
                    "Wasteland": 5,
                    "Water": 1,
                    "Hills - Minerals": 1,
                    "Mountains - Minerals": 1,
                }
            elif domain_type == "Forest":
                name_prefixes = ["Whispering", "Greenwood", "Sylvani"]
                starting_land_units_config = {
                    "Forest": 10,
                    "Hills - Stone": 1,
                    "Plains": 6,
                    "Mountains - Stone": 0,
                    "Ruins": 1,
                    "Swamp": 1,
                    "Wasteland": 0,
                    "Water": 0,
                    "Hills - Minerals": 1,
                    "Mountains - Minerals": 0,
                }
            elif domain_type == "Hills":
                name_prefixes = ["Rolling", "High", "Windy"]
                starting_land_units_config = {
                    "Forest": 4,
                    "Hills - Stone": 4,
                    "Plains": 6,
                    "Mountains - Stone": 1,
                    "Ruins": 0,
                    "Swamp": 0,
                    "Wasteland": 0,
                    "Water": 0,
                    "Hills - Minerals": 4,
                    "Mountains - Minerals": 1,
                }
            elif domain_type == "Mountains":
                name_prefixes = ["Peak", "Stonecrown", "Ironhold"]
                starting_land_units_config = {
                    "Forest": 3,
                    "Hills - Stone": 1,
                    "Plains": 4,
                    "Mountains - Stone": 3,
                    "Ruins": 1,
                    "Swamp": 0,
                    "Wasteland": 4,
                    "Water": 0,
                    "Hills - Minerals": 1,
                    "Mountains - Minerals": 3,
                }

            # Generate realm name
            if realm_name_input:
                realm_name = realm_name_input
            else:
                name_suffixes = ["Kingdom", "Empire", "Dominion", "Realm", "Hold", "Lands"]
                realm_name = f"{random.choice(name_prefixes)} {random.choice(name_suffixes)}"

            # Initialize starting resources
            starting_resources = {
                'Food': 0,
                'Wood': 0,
                'Stone': 0,
                'Adamantine': 0,
                'Copper': 0,
                'Gold': 0,
                'Iron': 0,
                'Mithral': 0,
                'Silver': 0,
            }

            # Get the realm scale object
            realm_scale = get_object_or_404(RealmScale, id=realm_scale_id) # Get by ID
            
            # Create the new realm object
            new_realm = Realm.objects.create(
                name=realm_name,
                ruler=ruler_name,
                scale=realm_scale,  # Assign the RealmScale instance
                treasury=0, # Initialize treasury to 0 for now
                resources=starting_resources.copy(), # Initialize with empty resources
            )

            # --- Generate initial Land Units and calculate starting resources ---
            for unit_type_name, quantity in starting_land_units_config.items():
                try:
                    land_unit_type = LandUnitType.objects.get(name=unit_type_name)
                    for i in range(quantity):
                        LandUnit.objects.create(
                            name=f"{land_unit_type.name} #{i+1}",
                            unit_type=land_unit_type,
                            realm=new_realm,
                        )
                        # Update starting resources based on land unit production
                        production = land_unit_type.production
                        if production:
                            produced_resource = random.choice(list(production.keys()))
                            if produced_resource == 'minerals':
                                produced_resource = _assign_mineral_type()
                            if produced_resource in starting_resources:
                                starting_resources[produced_resource] = starting_resources.get(produced_resource, 0) + 1
                            # If the produced resource is not in our list, it will be ignored.
                except LandUnitType.DoesNotExist:
                    print(f"Warning: LandUnitType '{unit_type_name}' not found.")

            # Update the realm's resources with the calculated starting amounts
            new_realm.resources = starting_resources
            new_realm.save()

            # --- Generate initial Population Units (based on food production) ---
            total_potential_food = 0
            land_units = LandUnit.objects.filter(realm=new_realm) # Get the land units we just created for this realm.

            for land_unit in land_units:
                # Get the LandUnitType instance to access production data.
                land_unit_type = land_unit.unit_type
                # Check if 'food' is a key in the production dictionary.
                if 'Food' in land_unit_type.production:
                    total_potential_food += land_unit_type.production['Food']

            num_starting_population = int(total_potential_food * 0.5)  # 50% of potential food production

            try:
                human_race = PopulationRace.objects.get(name="Humans")  # Get the Human race.
                for i in range(num_starting_population):
                    PopulationUnit.objects.create(
                        race=human_race,
                        realm=new_realm,
                    )
            except PopulationRace.DoesNotExist:
                print("Warning: PopulationRace 'Human' not found.  Creating 0 population.")
                # Handle the case where the "Human" race doesn't exist.  You might
                # want to create a default human race, or log an error and handle
                # it appropriately for your game.  For now, I'll create 0 population.

            return redirect('realm_detail', name=new_realm.name)
        else:
            return redirect('realm_list')

    elif request.method == 'POST':
        pass

    else:
        return redirect('realm_list')


# List all realms
def realm_list(request):
    realms = Realm.objects.all()  # Retrieve all realms
    return render(request, 'realms/realm_list.html', {'realms': realms})

# Create a new realm
# def create_realm(request):
#     if request.method == "POST":
#         # Get data from the form (You can add more fields)
#         realm_name = request.POST.get("name")
#         realm_ruler = request.POST.get("ruler")
        
#          # Basic validation
#         if not realm_name or not realm_ruler:
#             messages.error(request, "Both realm name and ruler name are required.")
#             return render(request, 'realms/create_realm.html')
        
#         if Realm.objects.filter(name=realm_name).exists():
#             messages.error(request, f"A realm named '{realm_name}' already exists.")
#             return render(request, 'realms/create_realm.html')
        
#         # Create and save the realm
#         new_realm = Realm(name=realm_name, ruler=realm_ruler)
#         new_realm.save()
        
#         # Redirect to the realm details page
#         messages.success(request, f"Realm '{realm_name}' created successfully!")
#         return redirect('realm_detail', name=realm_name)
    
#     return render(request, 'realms/create_realm.html')
def create_realm_start(request):
    request.session['new_realm'] = {}
    print("Starting new realm creation...")
    print(f"Session after start: {request.session.get('new_realm')}")
    return redirect('create_realm_step_1')

def create_realm_step_1(request):
    realm_scales = RealmScale.objects.all()  # Fetch all available realm scales

    if request.method == "POST":
        name = request.POST.get("name")
        ruler = request.POST.get("ruler")
        scale_id = request.POST.get("realm_scale")  # Get the selected scale ID
        
        if not name or not ruler or not scale_id:
            messages.error(request, "Name and ruler are required.")
        elif Realm.objects.filter(name=name).exists():
            messages.error(request, "A realm with that name already exists.")
        else:
            try:
                realm_scale = RealmScale.objects.get(id=scale_id)
                request.session['new_realm'] = {
                    "name": name,
                    "ruler": ruler,
                    "scale_id": scale_id,
                    "treasury": 0,
                    "resources": {},
                    "land_units": [],
                    "population_units": []
                }
                print(f"Session after step 1: {request.session.get('new_realm')}")
                return redirect('create_realm_step_2')
            except RealmScale.DoesNotExist:
                messages.error(request, "Invalid realm scale selected.")

    return render(request, 'realms/steps/step_1_name_ruler.html', {'realm_scales': realm_scales})

def create_realm_step_2(request):
    if request.method == "POST":
        treasury = request.POST.get("treasury")
        if treasury.isdigit():
            realm_data = request.session.get('new_realm', {}).copy()
            realm_data['treasury'] = int(treasury)
            request.session['new_realm'] = realm_data  # 👈 force session update
            print("Session after treasury step:", request.session['new_realm'])
            return redirect('create_realm_step_3')
        messages.error(request, "Treasury must be a number.")
    
    return render(request, 'realms/steps/step_2_treasury.html')

def create_realm_step_3(request):
    if request.method == "POST":
        form = ResourcesForm(request.POST, )
        if form.is_valid():
            data = request.session.get('new_realm', {}).copy()
            data['resources'] = form.cleaned_data
            request.session['new_realm'] = data

            print(f"Session after resources step: {request.session.get('new_realm')}")
            return redirect('create_realm_step_4')
    else:
        default_data = {
            'Food': 0,
            'Wood': 0,
            'Stone': 0,
            'Adamantine': 0,
            'Copper': 0,
            'Gold': 0,
            'Iron': 0,
            'Mithral': 0,
            'Silver': 0,
        }
        session_data = request.session.get('new_realm', {}).get('resources', {})
        default_data.update(session_data)  # session_data can override defaults
        form = ResourcesForm(initial=default_data)

    return render(request, 'realms/steps/step_3_resources.html', {'form': form})

def create_realm_step_4(request):
    # Fetch the available LandUnitType instances from the database
    unit_types = LandUnitType.objects.all()

    if request.method == "POST":
        # Initialize the form with POST data
        form = LandUnitForm(request.POST)
        if form.is_valid():
            # Extract cleaned data
            name = form.cleaned_data['name']
            unit_type = form.cleaned_data['unit_type']
            production = unit_type.production or {}
            
            # Get the session data (new_realm)
            data = request.session.get('new_realm', {}).copy()
            land_units = data.get('land_units', [])
            
            # Add the new land unit to the list in the session
            land_units.append({
                "name": name,
                "unit_type": unit_type.name,  # You can store the unit type's name or ID
                "production": production,
                "harvest": unit_type.harvest,
                "settlement_capacity": unit_type.settlement_capacity,
            })
            data['land_units'] = land_units
            request.session['new_realm'] = data

            # Debugging: Print session data for inspection
            print(f"Session after land step: {request.session.get('new_realm')}")

            # Redirect to the next step based on the button clicked
            if "next" in request.POST:
                return redirect('create_realm_step_5')  # Proceed to the next step
            else:
                return redirect('create_realm_step_4')  # Stay on the current step

    else:
        # Initialize the form
        form = LandUnitForm()
        form.fields['unit_type'].queryset = unit_types  # Dynamically populate the unit_type choices

    # Render the template with the form
    return render(request, 'realms/steps/step_4_land.html', {'form': form})



def create_realm_step_5(request):
    # Fetch the available PopulationRace instances from the database
    population_units = PopulationRace.objects.all()
    if request.method == "POST":
        form = PopulationUnitForm(request.POST)
        if form.is_valid():
            # Extract cleaned data
            race = form.cleaned_data['race']

        data = request.session.get('new_realm', {}).copy()
        pops = data.get('population_units', [])
        pops.append({"race": race.name})  # You
        data['population_units'] = pops
        request.session['new_realm'] = data

        print(f"Session after population step: {request.session.get('new_realm')}")

        if "next" in request.POST:
            return redirect('create_realm_review')
        else:
            return redirect('create_realm_step_5')
    else:
        # Initialize the form
        form = PopulationUnitForm()
        form.fields['race'].queryset = population_units  # Dynamically populate the unit_type choices
    return render(request, 'realms/steps/step_5_population.html', {'form': form})

def create_realm_review(request):
    realm_name = request.GET.get('realm_name')  # You may pass the realm name in the URL

    if realm_name:
        realm = get_object_or_404(Realm, name=realm_name)  # Fetch the realm from the database
    else:
        data = request.session.get('new_realm', {})
        realm = None  # No realm exists yet

    if request.method == "POST":
        # If editing an existing realm
        if realm_name:
            realm.ruler = realm.ruler
            realm.treasury = realm.treasury
            realm.resources = realm.resources
            realm.save()

            # Now handle land and population units
            for land in data.get('land_units', []):
                unit_type = LandUnitType.objects.get(name=land['unit_type'])  # Fetching by name
                LandUnit.objects.create(
                    realm=realm,
                    name=land['name'],
                    unit_type=unit_type,
                )

            for pop in data.get('population_units', []):
                race_name = pop['race'] if isinstance(pop['race'], str) else pop['race']['name']
                race = PopulationRace.objects.get(name=race_name)
                PopulationUnit.objects.create(
                    realm=realm,
                    race=race
                )

            # Cleanup session as we no longer need it for existing realms
            del request.session['new_realm']
            return redirect('realm_detail', name=realm.name)
        else: 
            scale_id = request.session.get('new_realm', {}).get('scale_id')
            try:
                realm_scale = RealmScale.objects.get(id=scale_id)
            except RealmScale.DoesNotExist:
                # Handle the error if the RealmScale doesn't exist (shouldn't happen if validation is correct)
                return redirect('create_realm_step_1') # Or display an error   
            realm = Realm.objects.create(
                name=data['name'],
                ruler=data['ruler'],
                scale=realm_scale,  # Assign the RealmScale here!
                treasury=data['treasury'],
                resources=data['resources']
            )

            # Create land units
            for land in data.get('land_units', []):
                unit_type = LandUnitType.objects.get(name=land['unit_type'])  # Fetching by name
                LandUnit.objects.create(
                    realm=realm,
                    name=land['name'],
                    unit_type=unit_type,  # Assign the correct LandUnitType instance
                    # You can keep settlement_capacity if needed, just uncomment the line
                    #settlement_capacity=land['settlement_capacity']  # Uncomment this if needed
                )

            # Create population units
            for pop in data.get('population_units', []):
                race_name = pop['race'] if isinstance(pop['race'], str) else pop['race']['name']
                race = PopulationRace.objects.get(name=race_name)
                PopulationUnit.objects.create(
                    realm=realm,
                    race=race
                )

            # Cleanup
            #del request.session['new_realm']
        return redirect('realm_detail', name=realm.name)

    #return render(request, 'realms/steps/review.html', {"realm": realm, "realm_name": realm_name})
    context = {
    "realm_name": realm_name
    }

    if realm:
        land_units = realm.land_units.values('unit_type__name')
        population_units = realm.population_units.values('race__name')

        land_unit_summary = {}
        for unit in land_units:
            unit_type = unit['unit_type__name']
            land_unit_summary[unit_type] = land_unit_summary.get(unit_type, 0) + 1

        population_unit_summary = {}
        for unit in population_units:
            race = unit['race__name']
            population_unit_summary[race] = population_unit_summary.get(race, 0) + 1

        context["realm"] = {
            'name': realm.name,
            'ruler': realm.ruler,
            'treasury': realm.treasury,
            'resources': realm.resources,
            'land_unit_summary': land_unit_summary,
            'population_unit_summary': population_unit_summary,
            'scale': realm.scale, # Include the scale in the context for display if needed
        }
    else:
        # context["realm"] = request.session.get('new_realm', {})
        realm_data = request.session.get('new_realm', {})
        land_units_data = realm_data.get('land_units', [])
        population_units_data = realm_data.get('population_units', [])

        land_unit_summary = {}
        for land in land_units_data:
            unit_type = land.get('unit_type')
            land_unit_summary[unit_type] = land_unit_summary.get(unit_type, 0) + 1

        population_unit_summary = {}
        for pop in population_units_data:
            race = pop.get('race') if isinstance(pop.get('race'), str) else pop.get('race', {}).get('name')
            population_unit_summary[race] = population_unit_summary.get(race, 0) + 1

        context["realm"] = realm_data
        context["land_unit_summary"] = land_unit_summary
        context["population_unit_summary"] = population_unit_summary

    return render(request, 'realms/steps/review.html', context)

# Show the details of a specific realm
def realm_detail(request, name):
    realm = get_object_or_404(Realm, name=name)  # Fetch the realm by its name
    land_units = realm.land_units.all()
    population_units = PopulationUnit.objects.filter(realm=realm)  # Get all population units for the realm

    # Summarize land units by type
    land_unit_summary = {}
    for unit in land_units:
        unit_type_name = unit.unit_type.name
        land_unit_summary[unit_type_name] = land_unit_summary.get(unit_type_name, 0) + 1

    # Summarize population units by race
    population_unit_summary = {}
    for unit in population_units:
        race_name = unit.race.name
        population_unit_summary[race_name] = population_unit_summary.get(race_name, 0) + 1

    context = {
        'realm': realm,
        'land_units': land_units, # You might be using this for a detailed list elsewhere
        'population_units': population_units, # You might be using this for a detailed list elsewhere
        'land_unit_summary': land_unit_summary,
        'population_unit_summary': population_unit_summary,
    }
    return render(request, 'realms/realm_detail.html', context)

# Add a population unit to a realm's land unit
def add_population_unit(request, realm_name):
    realm = Realm.objects.get(name=realm_name)
    if request.method == "POST":
        race = request.POST["race"]
        land_unit_name = request.POST["land_unit"]
        land_unit = LandUnit.objects.get(name=land_unit_name, realm=realm)
        population_unit = PopulationUnit.objects.create(race=race)
        population_unit.assigned_to = land_unit
        population_unit.save()
        return redirect('realm_detail', name=realm.name)
    
# Create LandUnit and associate with a Realm
def create_land_unit(request, realm_name):

    try:
        realm = Realm.objects.get(name=realm_name)
    except Realm.DoesNotExist:
        raise Http404("Realm does not exist.")

    if request.method == "POST":
        form = LandUnitForm(request.POST)
        if form.is_valid():
            land_unit = form.save(commit=False)
            land_unit.realm = realm

            # Copy attributes from type if needed
            land_unit.production = land_unit.unit_type.production
            land_unit.harvest = land_unit.unit_type.harvest
            land_unit.settlement_capacity = land_unit.unit_type.settlement_capacity 

            land_unit.save()
    
        if "done" in request.POST:
            return redirect('realm_detail', name=realm.name)  # Redirect to the realm detail page
        else:
            return redirect('create_land_unit', realm_name=realm.name)  # add another

    return render(request, 'realms/create_land_unit.html', {'realm': realm})

def create_population_unit(request, realm_name):
    realm = Realm.objects.get(name=realm_name)

    if request.method == "POST":
        race = request.POST.get("race")
        # Create PopulationUnit and associate it with the realm
        population_unit = PopulationUnit.objects.create(
            realm=realm,  # You have the realm object
            race=race
        )
        return redirect('realm_detail', name=realm_name)

    return render(request, 'realms/create_population_unit.html', {'realm': realm})

def edit_realm_info(request, realm_name=None):
    if realm_name:
        realm = get_object_or_404(Realm, name=realm_name)  # Fetch from DB if editing an existing realm
        # Initialize realm_data from the realm object (e.g., realm's fields)
        realm_data = {
            'name': realm.name,
            'ruler': realm.ruler,
        }
    else:
        realm_data = request.session.get('new_realm', {})  # Otherwise, use session data for new realm

    if request.method == 'POST':
        form = RealmInfoForm(request.POST)
        if form.is_valid():
            # Update the realm_data with the form's cleaned data
            realm_data.update(form.cleaned_data)
            if realm_name:
                realm.name = form.cleaned_data['name']
                realm.ruler = form.cleaned_data['ruler']
                realm.save()
                return redirect('realm_detail', name=realm.name)  # Go back to the realm details
            else:
                request.session['new_realm']['name'] = form.cleaned_data['name']
                request.session['new_realm']['ruler'] = form.cleaned_data['ruler']
                request.session['new_realm'] = realm_data  # Reassign the whole thing
                return redirect('create_realm_review')  # Go back to the review page
    else:
        # Pre-fill the form with current session data
        form = RealmInfoForm(initial={
            'name': realm_data.get('name', ''),
            'ruler': realm_data.get('ruler', ''),
        })
    return render(request, 'realms/edit/edit_realm_info.html', {'form': form})

def edit_treasury(request, realm_name=None):
    if realm_name:
        realm = get_object_or_404(Realm, name=realm_name)
    else:
        realm_data = request.session.get('new_realm', {})
        realm = None  # No realm exists yet
    if request.method == 'POST':
        form = TreasuryForm(request.POST)
        if form.is_valid():
            if realm_name:
                realm.treasury = form.cleaned_data['treasury']
                realm.save()
                return redirect('realm_detail', name=realm.name)  # Go back to the realm details
            else:
                request.session['new_realm']['treasury'] = form.cleaned_data['treasury']
                request.session['new_realm'] = realm_data  # Reassign the whole thing
                return redirect(reverse('create_realm_review'))
            # if realm:
            #     return redirect(f"{reverse('create_realm_review')}?realm_name={realm.name}")  # Go back to the review page
            # else:
            #     return redirect(reverse('create_realm_review'))
    else:
        if realm_name:
            initial_value = realm.treasury
        else:
            initial_value = realm_data.get('treasury', 0)
        form = TreasuryForm(initial={'treasury': initial_value})
    return render(request, 'realms/edit/edit_treasury.html', {'form': form})

def edit_resources(request, realm_name=None):
    if realm_name:
        realm = get_object_or_404(Realm, name=realm_name)
    else:
        realm_data = request.session.get('new_realm', {})
        realm = None  # No realm exists yet
    if request.method == 'POST':
        form = ResourcesForm(request.POST)
        if form.is_valid():
            if realm_name:
                realm.resources = form.cleaned_data
                realm.save()
                return redirect('realm_detail', name=realm.name)  # Go back to the realm details
            else:
                realm_data['resources'] = form.cleaned_data  # Assuming entire cleaned_data is the resource dict
                request.session['new_realm'] = realm_data
                return redirect(reverse('create_realm_review'))
    else:
        if realm_name:
            initial_value = realm.resources
        else:
            initial_value = realm_data.get('resources', {})
        form = ResourcesForm(initial= initial_value)
    return render(request, 'realms/edit/edit_resources.html', {'form': form})

def edit_land(request, realm_name=None):
    if realm_name:
        realm = get_object_or_404(Realm, name=realm_name)
        land_units = realm.land_units.all()

        LandUnitFormSet = modelformset_factory(
            LandUnit,
            form=LandUnitForm,
            extra=0,
            can_delete=True
        )
        formset = LandUnitFormSet(queryset=land_units)
    else:
        realm_data = request.session.get('new_realm', {})
        #initial_data = realm_data.get('land_units', [])
        initial_data_raw = realm_data.get('land_units', [])
        initial_data = []

        for unit in initial_data_raw:
            unit_copy = unit.copy()
            if 'unit_type' in unit and unit['unit_type']:
                try:
                    unit_copy['unit_type'] = LandUnitType.objects.get(name=unit['unit_type'])
                except LandUnitType.DoesNotExist:
                    unit_copy['unit_type'] = None
            initial_data.append(unit_copy)

        LandUnitFormSet = modelformset_factory(
            LandUnit,
            form=LandUnitForm,
            extra=max(1, len(initial_data)),  # Use initial_data length *after* it's defined
            can_delete=True
        )

        formset = LandUnitFormSet(
            queryset=LandUnit.objects.none(),
            initial=initial_data
        )

    if request.method == 'POST':
        formset = LandUnitFormSet(request.POST, queryset=land_units if realm_name else LandUnit.objects.none())
        if formset.is_valid():
            if realm_name:
                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        obj = form.save(commit=False)
                        obj.realm = realm
                        obj.save()
                    elif form.cleaned_data.get('DELETE', False) and form.instance.pk:
                        # If the form is marked for deletion, delete the instance
                        form.instance.delete()
                return redirect('realm_detail', name=realm.name)  # Go back to the realm details
            else:
                realm_data['land_units'] = [
                    {
                        'name': form.cleaned_data['name'],
                        'unit_type': form.cleaned_data['unit_type'].name if form.cleaned_data['unit_type'] else None
                    }
                    for form in formset if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
                ]
                request.session['new_realm'] = realm_data
                return redirect(reverse('create_realm_review'))

            # return redirect(
            #     f"{reverse('create_realm_review')}?realm_name={realm.name}"
            #     if realm_name else reverse('create_realm_review')
            # )

    return render(request, 'realms/edit/edit_land.html', {'formset': formset})

def edit_population(request, realm_name=None):
    if realm_name:
        # Editing an existing realm
        realm = get_object_or_404(Realm, name=realm_name)
        population_units = realm.population_units.all()

        PopulationUnitFormSet = modelformset_factory(
            PopulationUnit,
            form=PopulationUnitForm,
            extra=0,
            can_delete=True  # Enable deletion of population units
        )
        formset = PopulationUnitFormSet(queryset=population_units)
    else:
        # Creating a new realm
        realm_data = request.session.get('new_realm', {})
        initial_data_raw = realm_data.get('population_units', [])
        initial_data = []

        for unit in initial_data_raw:
            unit_copy = unit.copy()
            if 'race' in unit and unit['race']:
                try:
                    unit_copy['race'] = PopulationRace.objects.get(name=unit['race'])
                except PopulationRace.DoesNotExist:
                    unit_copy['race'] = None
            initial_data.append(unit_copy)

        PopulationUnitFormSet = modelformset_factory(
            PopulationUnit,
            form=PopulationUnitForm,
            extra=max(1, len(initial_data)),  # Set extra forms to match the initial data
            can_delete=True  # Enable deletion
        )

        formset = PopulationUnitFormSet(
            queryset=PopulationUnit.objects.none(),  # No DB objects for new realms
            initial=initial_data  # Use initial data from the session
        )

    if request.method == 'POST':
        formset = PopulationUnitFormSet(request.POST, queryset=population_units if realm_name else PopulationUnit.objects.none())
        if formset.is_valid():
            if realm_name:
                # If editing an existing realm, update or create population units
                for form in formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        obj = form.save(commit=False)
                        obj.realm = realm  # Attach the realm to the instance
                        obj.save()  # Save the updated population unit
                    elif form.cleaned_data.get('DELETE', False) and form.instance.pk:
                        # If the form is marked for deletion, delete the instance
                        form.instance.delete()
                return redirect('realm_detail', name=realm.name)  # Go back to the realm details
            else:
                # If creating a new realm, store the changes in session
                realm_data['population_units'] = [
                    {
                        'race': form.cleaned_data['race'].name if form.cleaned_data['race'] else None
                    }
                    for form in formset if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
                ]
                request.session['new_realm'] = realm_data
                return redirect(reverse('create_realm_review'))

    return render(request, 'realms/edit/edit_population.html', {'formset': formset})

# ACTION_MODULES = {
#     "Spring": spring_actions,
#     "Summer": summer_actions,
#     "Fall": fall_actions,
#     "Winter": winter_actions,
#     "All": generic_actions,
# }

MODULE_MAPPING = {
    "spring_actions": spring_actions,
    "summer_actions": summer_actions,
    "autumn_actions": fall_actions,
    "winter_actions": winter_actions,
    "generic_actions": generic_actions,
}



def player_actions(request, realm_name):
    realm = get_object_or_404(Realm, name=realm_name)
    ongoing_actions = realm.get_ongoing_actions()
    # Get action slugs for the current season and "All" actions
    available_action_display_names = SEASONAL_ACTIONS.get(realm.season, []) + SEASONAL_ACTIONS.get("All", [])
    available_actions_details = []
    for display_name in available_action_display_names:
        action_data = ALL_GAME_ACTIONS.get(display_name)
        if action_data:
            available_actions_details.append(action_data)
        else:
            print(f"Warning: Action definition not found in ALL_GAME_ACTIONS for '{display_name}'")

    # Serialize available_actions_details for JavaScript
    # Using json.dumps and mark_safe for robustness
    available_actions_json = json.dumps(available_actions_details)
    available_actions_json_safe = mark_safe(available_actions_json)
    print(f"Available actions JSON: {available_actions_json}")


    context = {
        'realm': realm,
        'ongoing_actions': ongoing_actions,
        'available_actions': available_actions_details, # Still pass this for template iteration
        'available_actions_json': available_actions_json_safe, # Pass the JSON string for JavaScript
    }

    print(f"Available actions JSON: {available_actions_json_safe}")
    return render(request, 'realms/player_actions.html', context)

def end_turn(request, realm_name):
    realm = get_object_or_404(Realm, name=realm_name)
    current_season = realm.season
    current_year = realm.year

    realm.next_season()
    next_season = realm.season
    next_year = realm.year

    ongoing_actions = OngoingAction.objects.filter(realm=realm, completed=False)

    for action_record in ongoing_actions: # Renamed 'action' to 'action_record' to avoid confusion
        if action_record.is_completed(realm.season, realm.year): # Use realm's NEW season/year
            action_record.completed = True
            action_record.save()
            
            action_slug = action_record.action_name # Use the slug from the OngoingAction

            handler_info = ACTION_HANDLERS.get(action_slug)
            if handler_info:
                module_name = handler_info['module']
                finish_func_name = handler_info['finish_func']
                
                module_obj = MODULE_MAPPING.get(module_name)

                if module_obj:
                    finish_func = getattr(module_obj, finish_func_name, None)
                    if finish_func:
                        finish_func(realm, action_record.data) # Pass realm and action_record.data
                    else:
                        print(f"Error: Finish function '{finish_func_name}' not found in module '{module_name}'.")
                else:
                    print(f"Error: Module '{module_name}' not found in MODULE_MAPPING.")
            else:
                print(f"Error: Action handler info not found for slug '{action_slug}'.")
                
    return redirect('player_actions', realm_name=realm_name)

def start_action(request, realm_name):
    realm = get_object_or_404(Realm, name=realm_name)
    if request.method == "POST":
        action_display_name = request.POST.get("action_name") # This is the display name (e.g., "Recruit Population")
        
        # Look up the action's full definition using its display name
        action_definition = ALL_GAME_ACTIONS.get(action_display_name)

        if action_definition:
            action_slug = action_definition['slug'] # Get the slug (e.g., "recruit_population")
            handler_info = ACTION_HANDLERS.get(action_slug)

            if handler_info:
                module_name = handler_info['module']
                start_func_name = handler_info['start_func']
                
                # Dynamically get the module object
                module_obj = MODULE_MAPPING.get(module_name)

                if module_obj:
                    start_func = getattr(module_obj, start_func_name, None)
                    if start_func:
                        # Pass realm and the full POST data to the start function
                        start_func(realm, request.POST)
                    else:
                        print(f"Error: Start function '{start_func_name}' not found in module '{module_name}'.")
                else:
                    print(f"Error: Module '{module_name}' not found in MODULE_MAPPING.")
            else:
                print(f"Error: Action handler info not found for slug '{action_slug}'.")
        else:
            print(f"Error: Action definition not found for display name '{action_display_name}'.")

        return redirect('player_actions', realm_name=realm_name)
    else:
        return redirect('player_actions', realm_name=realm_name)