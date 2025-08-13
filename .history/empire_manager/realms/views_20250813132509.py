import json
from django.shortcuts import render, redirect, get_object_or_404
from .models import Realm, LandUnit, PopulationUnit, LandUnitType, MINERAL_SUBTYPES, RealmScale, OngoingAction, GoodsType, Resource, RealmResource, RealmGoodsType, ActionType, StrongholdType, StrongholdInstance, StrongholdImprovementType, StrongholdImprovementInstance
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from .forms import RealmInfoForm, TreasuryForm, LandUnitForm, PopulationUnitForm, PopulationRace
from django.forms import formset_factory, modelformset_factory
from django.urls import reverse
from django.views.decorators.http import require_POST
import random
from .game_logic import generic_actions, summer_actions
from .game_logic.generic_actions import calculate_build_roads_cost, calculate_build_mine_cost, calculate_construct_stronghold_cost
#from .game_logic.action_definitions import SEASONAL_ACTIONS, ALL_GAME_ACTIONS, ACTION_HANDLERS
from .game_logic.action_definitions import ACTION_HANDLERS
from django.core.serializers import serialize
from django.utils.safestring import mark_safe
from django.db import transaction # Import for atomic operations
from django.db.models import Q, Exists, OuterRef, Count

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

            try:
                with transaction.atomic():

                    # Get the realm scale object
                    realm_scale = get_object_or_404(RealmScale, id=realm_scale_id) # Get by ID
            
                    # Create the new realm object
                    new_realm = Realm.objects.create(
                        name=realm_name,
                        ruler=ruler_name,
                        scale=realm_scale,  # Assign the RealmScale instance
                        treasury=random.randint(5, 20), # Initialize treasury to 0 for now
                    )

                    # --- Initialize a temporary dict to aggregate resources from land units ---
                    temp_initial_resources = {} # {'ResourceName': quantity}

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
                                    temp_initial_resources[produced_resource] = \
                                        temp_initial_resources.get(produced_resource, 0) + 1
                                    # If the produced resource is not in our list, it will be ignored.
                        except LandUnitType.DoesNotExist:
                            print(f"Warning: LandUnitType '{unit_type_name}' not found for automatic creation.")
                            messages.warning(request, f"Missing Land Unit Type: '{unit_type_name}'.")

                    # --- Save the calculated starting resources to the new Realm using RealmResource ---
                    for resource_name, quantity in temp_initial_resources.items():
                        if quantity > 0:
                            # Use the helper method on Realm to create/update RealmResource
                            new_realm.update_resource_quantity(resource_name, quantity)

                    # --- Initial Goods (Always empty at creation as per your rule) ---
                    # No code needed here, RealmGoodsType entries will be created via actions.

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

                     # Ensure "Human" race exists or handle gracefully
                    try:
                        human_race = PopulationRace.objects.get(name="Humans")
                        for i in range(num_starting_population):
                            PopulationUnit.objects.create(
                                race=human_race,
                                realm=new_realm,
                            )
                    except PopulationRace.DoesNotExist:
                        print("Warning: PopulationRace 'Human' not found for automatic creation. No initial population created.")
                        messages.warning(request, "Population Race 'Human' not found, no initial population created.")

                    return redirect('realm_detail', name=new_realm.name)
                
            except Exception as e:
                messages.error(request, f"An error occurred during automatic realm creation: {e}")
                print(f"Automatic realm creation error: {e}")
                import traceback
                print(traceback.format_exc())
                return redirect('realm_list') # Redirect to realm list on error

    elif request.method == 'POST':
        pass

    else:
        return redirect('realm_list')


# List all realms
def realm_list(request):
    realms = Realm.objects.all()  # Retrieve all realms
    return render(request, 'realms/realm_list.html', {'realms': realms})

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
    all_resources = Resource.objects.all().order_by('name') # Get all resource types, ordered for display

    if request.method == "POST":
        resource_quantities = []
        for resource_obj in all_resources:
            # Get the quantity for this specific resource from the POST data
            # The input name will be 'resource_<resource_id>'
            quantity_str = request.POST.get(f"resource_{resource_obj.id}", "0")
            try:
                quantity = int(quantity_str)
                if quantity < 0:
                    messages.error(request, f"Quantity for {resource_obj.name} cannot be negative.")
                    # Re-render with error and current values
                    return render(request, 'realms/steps/step_3_resources.html', {
                        'all_resources': all_resources,
                        'current_quantities': {r.id: int(request.POST.get(f"resource_{r.id}", "0")) for r in all_resources}
                    })
                if quantity > 0: # Only store resources with a positive quantity
                    resource_quantities.append({
                        'resource_id': resource_obj.id,
                        'quantity': quantity
                    })
            except ValueError:
                messages.error(request, f"Quantity for {resource_obj.name} must be a number.")
                # Re-render with error and current values
                return render(request, 'realms/steps/step_3_resources.html', {
                    'all_resources': all_resources,
                    'current_quantities': {r.id: request.POST.get(f"resource_{r.id}", "0") for r in all_resources}
                })

        realm_data = request.session.get('new_realm', {}).copy()
        realm_data['resources'] = resource_quantities # Store as a list of dicts
        request.session['new_realm'] = realm_data
        print(f"Session after resources step: {request.session.get('new_realm')}")
        return redirect('create_realm_step_4')
    else:
        # For GET request, pre-fill with 0 or existing session data
        current_quantities = {}
        session_resources = request.session.get('new_realm', {}).get('resources', [])
        for res_data in session_resources:
            current_quantities[res_data['resource_id']] = res_data['quantity']
        
        return render(request, 'realms/steps/step_3_resources.html', {
            'all_resources': all_resources,
            'current_quantities': current_quantities
        })

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
    # In this simplified view, we only expect to handle new realm creation from session data.
    # No 'realm_name_from_get' logic or fetching of existing realms here.

    # Data for the new realm should always be in the session
    realm_data_from_session = request.session.get('new_realm', {})

    # If essential data is missing from session, redirect back to the start
    if not realm_data_from_session.get('name') or not realm_data_from_session.get('ruler') or not realm_data_from_session.get('scale_id'):
        messages.error(request, "Realm creation data missing. Please start over.")
        return redirect('create_realm_step_1')


    if request.method == "POST":
        # --- POST request: Confirm and Create the NEW realm ---
        
        # Re-fetch data from session in case it was modified unexpectedly (good practice)
        data_to_create_realm = request.session.get('new_realm', {}) 
        
        # Fetch the RealmScale object
        scale_id = data_to_create_realm.get('scale_id')
        try:
            realm_scale_obj = RealmScale.objects.get(id=scale_id)
        except RealmScale.DoesNotExist:
            messages.error(request, "Invalid realm scale selected. Please restart realm creation.")
            return redirect('create_realm_step_1')

        try:
            with transaction.atomic(): # Ensure atomicity for database writes
                # Create the base Realm object
                newly_created_realm = Realm.objects.create(
                    name=data_to_create_realm['name'],
                    ruler=data_to_create_realm['ruler'],
                    scale=realm_scale_obj,
                    treasury=data_to_create_realm['treasury'],
                )

                # Create RealmResource objects from session data
                resources_data_from_session = data_to_create_realm.get('resources', [])
                for res_entry in resources_data_from_session:
                    try:
                        resource_obj = Resource.objects.get(id=res_entry['resource_id'])
                        RealmResource.objects.create(
                            realm=newly_created_realm,
                            resource=resource_obj,
                            quantity=res_entry['quantity']
                        )
                    except Resource.DoesNotExist:
                        print(f"Warning: Resource ID {res_entry['resource_id']} not found during realm creation.")
                        messages.warning(request, f"Skipping unknown resource: {res_entry['resource_id']}.")
                    except Exception as e:
                        print(f"Error creating RealmResource for {res_entry.get('resource_id')}: {e}")
                        messages.error(request, f"Error saving resource {res_entry.get('resource_id')}.")

                # Create RealmGoodsType objects from session data (should be empty if no goods step)
                goods_data_from_session = data_to_create_realm.get('goods', []) 
                for goods_entry in goods_data_from_session:
                    try:
                        goods_type_obj = GoodsType.objects.get(id=goods_entry['goods_type_id'])
                        RealmGoodsType.objects.create(
                            realm=newly_created_realm,
                            goods_type=goods_type_obj,
                            quantity=goods_entry['quantity']
                        )
                    except GoodsType.DoesNotExist:
                        print(f"Warning: GoodsType ID {goods_entry['goods_type_id']} not found during realm creation.")
                        messages.warning(request, f"Skipping unknown goods type: {goods_entry['goods_type_id']}.")
                    except Exception as e:
                        print(f"Error creating RealmGoodsType for {goods_entry.get('goods_type_id')}: {e}")
                        messages.error(request, f"Error saving goods type {goods_entry.get('goods_type_id')}.")

                # Create LandUnit objects
                for land_unit_dict in data_to_create_realm.get('land_units', []):
                    try:
                        unit_type = LandUnitType.objects.get(name=land_unit_dict['unit_type'])
                        LandUnit.objects.create(
                            realm=newly_created_realm,
                            name=land_unit_dict['name'],
                            unit_type=unit_type,
                            # Assuming other fields like assigned_population, upgrades, mineral_type
                            # are handled in default or by specific steps.
                        )
                    except LandUnitType.DoesNotExist:
                        messages.warning(request, f"Land Unit Type '{land_unit_dict.get('unit_type')}' not found.")
                        print(f"Warning: LandUnitType '{land_unit_dict.get('unit_type')}' not found during realm creation.")
                    except Exception as e:
                        print(f"Error creating LandUnit: {e}")
                        messages.error(request, f"Error saving land unit '{land_unit_dict.get('name')}'.")


                # Create PopulationUnit objects
                for pop_unit_dict in data_to_create_realm.get('population_units', []):
                    try:
                        race_name_from_pop = pop_unit_dict.get('race')
                        # Handle if 'race' is a string or a dict (from initial data load/session)
                        race_name = race_name_from_pop if isinstance(race_name_from_pop, str) else race_name_from_pop.get('name')
                        race = PopulationRace.objects.get(name=race_name)
                        PopulationUnit.objects.create(
                            realm=newly_created_realm,
                            race=race
                        )
                    except PopulationRace.DoesNotExist:
                        messages.warning(request, f"Population Race '{pop_unit_dict.get('race')}' not found.")
                        print(f"Warning: PopulationRace '{pop_unit_dict.get('race')}' not found during realm creation.")
                    except Exception as e:
                        print(f"Error creating PopulationUnit: {e}")
                        messages.error(request, f"Error saving population unit for race '{pop_unit_dict.get('race')}'.")
            
            messages.success(request, f"Realm {newly_created_realm.name} created successfully!")
            del request.session['new_realm'] # Clear session data after successful creation
            return redirect('realm_detail', name=newly_created_realm.name)

        except Exception as e:
            messages.error(request, f"An unexpected error occurred during realm creation: {e}")
            print(f"Realm creation error: {e}")
            import traceback
            print(traceback.format_exc())
            return redirect('create_realm_step_1') # Redirect to start on severe error

    else:
        # --- GET request: Display review of the NEW realm data from session ---

        # The initial validation above already checked for basic data presence.
        # Fetch components from session data for display.
        resources_data_from_session = realm_data_from_session.get('resources', [])
        resources_summary = {}
        for res_entry in resources_data_from_session:
            try:
                resource_obj = Resource.objects.get(id=res_entry['resource_id'])
                resources_summary[resource_obj.name] = res_entry['quantity']
            except Resource.DoesNotExist:
                resources_summary[f"Unknown Resource (ID: {res_entry['resource_id']})"] = res_entry['quantity']

        goods_data_from_session = realm_data_from_session.get('goods', [])
        goods_summary = {}
        for goods_entry in goods_data_from_session:
            try:
                goods_type_obj = GoodsType.objects.get(id=goods_entry['goods_type_id'])
                goods_summary[goods_type_obj.name] = goods_entry['quantity']
            except GoodsType.DoesNotExist:
                goods_summary[f"Unknown Goods Type (ID: {goods_entry['goods_type_id']})"] = goods_entry['quantity']

        land_units_data_from_session = realm_data_from_session.get('land_units', [])
        land_unit_summary = {}
        for land_unit_dict in land_units_data_from_session:
            unit_type = land_unit_dict.get('unit_type')
            if unit_type:
                land_unit_summary[unit_type] = land_unit_summary.get(unit_type, 0) + 1

        population_units_data_from_session = realm_data_from_session.get('population_units', [])
        population_unit_summary = {}
        for pop_unit_dict in population_units_data_from_session:
            race_name_from_pop = pop_unit_dict.get('race')
            # Handle if 'race' is a string or a dict (from initial data load/session)
            race = race_name_from_pop if isinstance(race_name_from_pop, str) else pop_unit_dict.get('race', {}).get('name')
            if race:
                population_unit_summary[race] = population_unit_summary.get(race, 0) + 1
        
        scale_id_from_session = realm_data_from_session.get('scale_id')
        display_scale_obj = None
        if scale_id_from_session:
            try:
                display_scale_obj = RealmScale.objects.get(id=scale_id_from_session)
            except RealmScale.DoesNotExist:
                pass

        # Prepare context for template rendering
        context = {
            "realm": { # Reconstruct realm dict for template consistency
                'name': realm_data_from_session.get('name'),
                'ruler': realm_data_from_session.get('ruler'),
                'treasury': realm_data_from_session.get('treasury'),
                'scale': display_scale_obj,
                'resources': resources_summary,
                'goods': goods_summary,
            },
            "land_unit_summary": land_unit_summary,
            "population_unit_summary": population_unit_summary,
            "realm_name": realm_data_from_session.get('name') # Pass realm_name for edit links
        }

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

     # --- NEW: Get and summarize RealmResources ---
    realm_resources_qs = RealmResource.objects.filter(realm=realm).select_related('resource')
    resources_summary = {}
    for rr in realm_resources_qs:
        resources_summary[rr.resource.name] = rr.quantity # Direct quantity from RealmResource

    # --- NEW: Get and summarize RealmGoodsTypes ---
    realm_goods_qs = RealmGoodsType.objects.filter(realm=realm).select_related('goods_type')
    goods_summary = {}
    for rg in realm_goods_qs:
        goods_summary[rg.goods_type.name] = rg.quantity # Direct quantity from RealmGoodsType

    # Fetch all strongholds for this realm.
    # select_related improves performance by fetching related objects in a single query.
    strongholds = StrongholdInstance.objects.filter(realm=realm).select_related('stronghold_type', 'land_unit')

    context = {
        'realm': realm,
        'land_units': land_units, # You might be using this for a detailed list elsewhere
        'population_units': population_units, # You might be using this for a detailed list elsewhere
        'land_unit_summary': land_unit_summary,
        'population_unit_summary': population_unit_summary,
        'resources_summary': resources_summary, # Pass new summary
        'goods_summary': goods_summary, # Pass new summary
        'strongholds': strongholds,  # Pass strongholds
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
    # Fetch all available Resource types (e.g., Food, Wood, Iron)
    all_resources = Resource.objects.all().order_by('name')

    # Determine if we're editing an existing realm or a new one in session
    realm_obj_from_db = None
    if realm_name: # If realm_name is provided in URL, it's an existing realm
        realm_obj_from_db = get_object_or_404(Realm, name=realm_name)

    if request.method == 'POST':
        # Process the submitted form data for resource quantities
        resource_quantities_from_form = []
        for resource_obj in all_resources: # Loop through all possible resource types
            # The input field name in the HTML will be 'resource_<resource_id>'
            quantity_str = request.POST.get(f"resource_{resource_obj.id}", "0")
            try:
                quantity = int(quantity_str)
                if quantity < 0: # Basic validation: quantities cannot be negative
                    messages.error(request, f"Quantity for {resource_obj.name} cannot be negative.")
                    # Re-render the form with existing data and error message
                    return render(request, 'realms/edit/edit_resources.html', {
                        'all_resources': all_resources,
                        'current_quantities': {r.id: int(request.POST.get(f"resource_{r.id}", "0")) for r in all_resources},
                        'realm_name': realm_name # Pass realm_name back for template context
                    })
                
                # Only add to list if quantity is positive (don't create RealmResource for 0s)
                # or if you specifically want to store 0s
                resource_quantities_from_form.append({
                    'resource_id': resource_obj.id,
                    'quantity': quantity
                })
            except ValueError: # If input is not a valid number
                messages.error(request, f"Quantity for {resource_obj.name} must be a number.")
                # Re-render the form with existing data and error message
                return render(request, 'realms/edit/edit_resources.html', {
                    'all_resources': all_resources,
                    'current_quantities': {r.id: request.POST.get(f"resource_{r.id}", "0") for r in all_resources}, # Pass back string to preserve user input
                    'realm_name': realm_name # Pass realm_name back for template context
                })

        # Decide whether to save to database (existing realm) or session (new realm)
        if realm_obj_from_db:
            # --- Saving resources for an EXISTING realm to the database ---
            try:
                with transaction.atomic(): # Ensure database operations are atomic
                    # Strategy: Delete all existing RealmResource objects for this realm
                    # and then re-create them based on the submitted form data.
                    # This is simpler than trying to update individual quantities or diffing.
                    RealmResource.objects.filter(realm=realm_obj_from_db).delete()
                    
                    for res_data in resource_quantities_from_form:
                        if res_data['quantity'] > 0: # Only create entries for positive quantities
                            resource_obj = Resource.objects.get(id=res_data['resource_id']) # Fetch Resource object
                            RealmResource.objects.create(
                                realm=realm_obj_from_db,
                                resource=resource_obj,
                                quantity=res_data['quantity']
                            )
                messages.success(request, f"Resources for {realm_obj_from_db.name} updated successfully!")
                return redirect('realm_detail', name=realm_obj_from_db.name) # Redirect to realm detail page
            except Resource.DoesNotExist:
                messages.error(request, "One of the submitted resources does not exist. Please check your data.")
            except Exception as e:
                messages.error(request, f"An unexpected error occurred during resource update: {e}")
                print(f"Error updating resources for {realm_name}: {e}")
                import traceback # For detailed server logging
                print(traceback.format_exc())
            # Fallback to render form with errors if any exception occurs during DB save
            return render(request, 'realms/edit/edit_resources.html', {
                'all_resources': all_resources,
                'current_quantities': {r['resource_id']: r['quantity'] for r in resource_quantities_from_form},
                'realm_name': realm_name
            })
        else:
            # --- Saving resources for a NEW realm to the SESSION ---
            realm_data = request.session.get('new_realm', {}).copy()
            realm_data['resources'] = resource_quantities_from_form # Update resources list in session
            request.session['new_realm'] = realm_data
            messages.success(request, "Resources saved to session. Continue realm creation.")
            # Redirect to the next step in the manual creation wizard (likely create_realm_step_4 for Land)
            return redirect('create_realm_step_4')
    else:
        # --- GET request: Load initial data for the form ---
        current_quantities = {}
        if realm_obj_from_db:
            # For existing realm, load quantities from RealmResource objects in the database
            existing_realm_resources = RealmResource.objects.filter(realm=realm_obj_from_db).select_related('resource')
            for rr in existing_realm_resources:
                current_quantities[rr.resource.id] = rr.quantity
        else:
            # For new realm (data in session), load quantities from session data
            session_resources = request.session.get('new_realm', {}).get('resources', [])
            for res_data in session_resources:
                current_quantities[res_data['resource_id']] = res_data['quantity']
        
        return render(request, 'realms/edit/edit_resources.html', {
            'all_resources': all_resources, # All available resource types
            'current_quantities': current_quantities, # Quantities for current realm/session
            'realm_name': realm_name # Pass realm_name for template logic (e.g., back buttons, messages)
        })

# def edit_resources(request, realm_name=None):
#     all_resources = Resource.objects.all().order_by('name')

#     if realm_name:
#         realm = get_object_or_404(Realm, name=realm_name)
#     else:
#         realm_data = request.session.get('new_realm', {})
#         realm = None  # No realm exists yet
#     if request.method == 'POST':
#         form = ResourcesForm(request.POST)
#         if form.is_valid():
#             if realm_name:
#                 realm.resources = form.cleaned_data
#                 realm.save()
#                 return redirect('realm_detail', name=realm.name)  # Go back to the realm details
#             else:
#                 realm_data['resources'] = form.cleaned_data  # Assuming entire cleaned_data is the resource dict
#                 request.session['new_realm'] = realm_data
#                 return redirect(reverse('create_realm_review'))
#     else:
#         if realm_name:
#             initial_value = realm.resources
#         else:
#             initial_value = realm_data.get('resources', {})
#         form = ResourcesForm(initial= initial_value)
#     return render(request, 'realms/edit/edit_resources.html', {'form': form})

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

MODULE_MAPPING = {
    #"spring_actions": spring_actions,
    "summer_actions": summer_actions,
    #"autumn_actions": fall_actions,
    #"winter_actions": winter_actions,
    "generic_actions": generic_actions,
}

def player_actions(request, realm_name):
    realm = get_object_or_404(Realm, name=realm_name)
    
    # Get actions available this season OR in all seasons (empty available_seasons)
    available_actions = ActionType.objects.filter(
        Q(available_seasons=realm.season) | Q(available_seasons__isnull=True)
    ).distinct()

    # Convert the QuerySet to a list of dictionaries for the template's JSON.
    # Note: We now use 'action_key' which is the primary key of ActionType.
    available_actions_details = list(available_actions.values(
        'action_key', 'name', 'description', 'duration', 'submit_text', 'inputs'
    ))
    active_ongoing_actions = OngoingAction.objects.filter(realm=realm, completed=False)
    
    ongoing_actions_for_display = []
    for action_record in active_ongoing_actions:
        # You'll need a way to get the display name. We can query ActionType for it.
        try:
            action_def = ActionType.objects.get(action_key=action_record.action_name)
            display_name = action_def.name
        except ActionType.DoesNotExist:
            display_name = action_record.action_name # Fallback
            
        ongoing_actions_for_display.append({
            'display_name': display_name,
            'start_season': action_record.start_season.name, # Use .name now
            'start_year': action_record.start_year,
            'duration': action_record.duration,
            'id': action_record.id,
        })

    available_actions_json = json.dumps(available_actions_details)
    available_actions_json_safe = mark_safe(available_actions_json)

    context = {
        'realm': realm,
        'ongoing_actions': ongoing_actions_for_display,
        'available_actions_json': available_actions_json_safe,
        'available_actions': available_actions_details,
    }

    return render(request, 'realms/player_actions.html', context)
    # active_ongoing_actions = OngoingAction.objects.filter(realm=realm, completed=False)

    # # 2. Prepare ongoing actions for display with their proper display names
    # ongoing_actions_for_display = []
    # for action_record in active_ongoing_actions:
    #     # Find the action definition using the slug stored in action_record.action_type
    #     action_definition = None
    #     for key, definition in ALL_GAME_ACTIONS.items():
    #         if definition['slug'] == action_record.action_name:
    #             action_definition = definition
    #             break

    #     if action_definition:
    #         # Calculate remaining duration if needed, or pass the total duration and let template calculate
    #         # For simplicity, let's just pass the duration for now.
    #         ongoing_actions_for_display.append({
    #             'display_name': action_definition['name'], # Get the readable name
    #             'start_season': action_record.start_season,
    #             'start_year': action_record.start_year,
    #             'duration': action_record.duration,
    #             'id': action_record.id, # Keep ID for potential future use (e.g., cancelling)
    #             # You can add remaining_seasons here if you calculate it in Python
    #         })
    #     else:
    #         print(f"Warning: Action definition not found for ongoing action slug: {action_record.action_name}")
    #         # Fallback for display if definition is missing
    #         ongoing_actions_for_display.append({
    #             'display_name': action_record.action_name, # Use slug as fallback
    #             'start_season': action_record.start_season,
    #             'start_year': action_record.start_year,
    #             'duration': action_record.duration,
    #             'id': action_record.id,
    #         })

    # # Get action slugs for the current season and "All" actions
    # available_action_display_names = SEASONAL_ACTIONS.get(realm.season, []) + SEASONAL_ACTIONS.get("All", [])
    # available_actions_details = []
    # for display_name in available_action_display_names:
    #     action_data = ALL_GAME_ACTIONS.get(display_name)
    #     if action_data:
    #         available_actions_details.append(action_data)
    #     else:
    #         print(f"Warning: Action definition not found in ALL_GAME_ACTIONS for '{display_name}'")

    # # Serialize available_actions_details for JavaScript
    # # Using json.dumps and mark_safe for robustness
    # available_actions_json = json.dumps(available_actions_details)
    # available_actions_json_safe = mark_safe(available_actions_json)

    # context = {
    #     'realm': realm,
    #     'ongoing_actions': ongoing_actions_for_display,
    #     'available_actions': available_actions_details, # Still pass this for template iteration
    #     'available_actions_json': available_actions_json_safe, # Pass the JSON string for JavaScript
    # }

    # return render(request, 'realms/player_actions.html', context)

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
                        finish_func(realm, action_record.data or {}, completed_action=action_record) # Pass realm and action_record.data
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
        # The form now submits the 'action_key' as 'action_name'
        action_key = request.POST.get("action_name")

        try:
            # Verify the action exists in the database
            action_type = ActionType.objects.get(pk=action_key)
        except ActionType.DoesNotExist:
            messages.error(request, f"Action '{action_key}' not found.")
            return redirect('player_actions', realm_name=realm_name)
        
        # Look up the handler for this action key
        handler_info = ACTION_HANDLERS.get(action_key)

        if not handler_info:
            messages.error(request, f"Handler for action '{action_type.name}' not configured.")
            return redirect('player_actions', realm_name=realm_name)


        module_name = handler_info['module']
        start_func_name = handler_info['start_func']
        # No need to get finish_func_name here, as it's handled only for duration > 0 actions in end_turn
        
        module_obj = MODULE_MAPPING.get(module_name)

        if not module_obj:
            messages.error(request, f"Internal error: Module '{module_name}' not found in MODULE_MAPPING.")
            return redirect('player_actions', realm_name=realm_name)

        start_func = getattr(module_obj, start_func_name, None)
        if not start_func:
            messages.error(request, f"Internal error: Start function '{start_func_name}' not found in '{module_name}'.")
            return redirect('player_actions', realm_name=realm_name)
        
        # --- Call the start function and handle its return value ---
        # start_func should now return (success_boolean, message_string, action_data_dict_or_None)
        success, message, action_data_for_ongoing = start_func(realm, request.POST)

        if success:
            if action_type.duration == 0 and not (action_data_for_ongoing and 'final_duration' in action_data_for_ongoing):
                messages.success(request, message)
            else:
                with transaction.atomic():
                    duration = action_data_for_ongoing.get('final_duration', action_type.duration)
                    new_action = OngoingAction.objects.create(
                        realm=realm,
                        action_name=action_key,
                        start_season=realm.season,
                        start_year=realm.year,
                        duration=duration,
                        data=action_data_for_ongoing
                    )

                    # If population was assigned, link them to the action
                    if 'assigned_pop_ids' in action_data_for_ongoing:
                        pop_units = PopulationUnit.objects.filter(id__in=action_data_for_ongoing['assigned_pop_ids'])
                        new_action.assigned_population.set(pop_units)
                    messages.success(request, message)
                    messages.info(request, f"Action '{action_type.name}' started. It will complete in {duration} season(s).")
        else:
            # Action failed, display error message from start_func
            messages.error(request, message)
        
        return redirect('player_actions', realm_name=realm_name)
    else:
        messages.error(request, "Invalid request method for starting an action.")
        return redirect('player_actions', realm_name=realm_name)
    
def get_population_races_json(request):
    population_races = PopulationRace.objects.all().values('id', 'name')
    return JsonResponse(list(population_races), safe=False)

def get_goods_types_json(request):
    goods_types = GoodsType.objects.all().values('id', 'name', 'value')
    return JsonResponse(list(goods_types), safe=False)

def get_resource_types_json(request):
    resource_types = Resource.objects.all().values('id', 'name', 'value')
    return JsonResponse(list(resource_types), safe=False)

def get_stronghold_types_json(request):
    """
    Returns a list of all available StrongholdType objects for form dropdowns.
    """
    stronghold_types = StrongholdType.objects.all().values('id', 'name')
    return JsonResponse(list(stronghold_types), safe=False)

def get_land_units_json(request, realm_name):
    """
    Returns a list of land units for a specific realm that DO NOT already have a stronghold.
    """
    realm = get_object_or_404(Realm, name=realm_name)
    # Exclude land units that already have a stronghold instance linked to them
    land_units = LandUnit.objects.filter(realm=realm, stronghold__isnull=True).values('id', 'name')
    return JsonResponse(list(land_units), safe=False)

def get_stronghold_type_details_json(request, stronghold_type_id):
    """
    Returns details for a single StrongholdType, like its population cost.
    """
    stronghold_type = get_object_or_404(StrongholdType, id=stronghold_type_id)
    data = {
        'id': stronghold_type.id,
        'name': stronghold_type.name,
        'population_cost': stronghold_type.population_cost
        # Add any other details you might need on the frontend
    }
    return JsonResponse(data)

def get_idle_population_json(request, realm_name):
    """
    Returns a list of idle population units for a specific realm.
    """
    realm = get_object_or_404(Realm, name=realm_name)
    idle_population = PopulationUnit.objects.filter(realm=realm, status='idle').values('id', 'race__name')
    
    # Format the data for easier display (e.g., "Human #123")
    formatted_pop = [
        {'id': pop['id'], 'display_name': f"{pop['race__name']} (ID: {pop['id']})"} 
        for pop in idle_population
    ]
    return JsonResponse(formatted_pop, safe=False)

def get_road_eligible_land_units_json(request, realm_name):
    """
    Returns a list of land units that do not already have roads.
    """
    realm = get_object_or_404(Realm, name=realm_name)
    # Annotate each LandUnit with a boolean indicating if a related StrongholdInstance exists
    land_units_with_stronghold_info = LandUnit.objects.filter(
        realm=realm, 
        has_roads=False
    ).annotate(
        has_stronghold=Exists(StrongholdInstance.objects.filter(land_unit=OuterRef('pk')))
    ).values('id', 'name', 'has_stronghold') # <-- Include has_stronghold in the values

    return JsonResponse(list(land_units_with_stronghold_info), safe=False)

def get_mine_eligible_land_units_json(request, realm_name):
    """
    Returns a list of land units that can have a mine built on them.
    (No mine exists, and produces stone or minerals).
    """
    realm = get_object_or_404(Realm, name=realm_name)
    mineral_producing_types = LandUnitType.objects.filter(
        Q(production__has_key='Stone') | Q(production__has_key='minerals')
    )
    land_units = LandUnit.objects.filter(
        realm=realm, 
        has_mine=False,
        unit_type__in=mineral_producing_types
    ).values('id', 'name')
    return JsonResponse(list(land_units), safe=False)

def preview_action_cost(request, realm_name):
    if request.method == 'POST':
        realm = get_object_or_404(Realm, name=realm_name)
        data = json.loads(request.body)
        action_key = data.get('action_key')
        
        costs = {}
        
        if action_key == 'build_roads':
            land_unit_ids = data.get('land_unit_ids', [])
            # We will call a dedicated function to calculate the cost
            costs = calculate_build_roads_cost(realm, land_unit_ids)
        elif action_key == 'build_mine':
            # We will call a dedicated function to calculate the cost
            costs = calculate_build_mine_cost()
        elif action_key == 'construct_stronghold':
            stronghold_type_id = data.get('stronghold_type_id')
            if stronghold_type_id:
                costs = calculate_construct_stronghold_cost(realm, stronghold_type_id)
            
        # Add 'else if' blocks here for other actions with dynamic costs
            
        return JsonResponse(costs)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_production_strongholds_json(request, realm_name):
    """
    Returns a list of strongholds that have at least one improvement,
    making them eligible for production actions.
    """
    realm = get_object_or_404(Realm, name=realm_name)
    
    # Find strongholds in this realm that have one or more improvements
    production_strongholds = StrongholdInstance.objects.annotate(
        num_improvements=Count('improvements')
    ).filter(
        realm=realm,
        num_improvements__gt=0
    )
    
    # Format the data for the dropdown
    data = [
        {'id': sh.id, 'name': f"{sh.name} ({sh.land_unit.name})"} 
        for sh in production_strongholds
    ]
    
    return JsonResponse(data, safe=False)

def get_producible_goods_json(request, stronghold_instance_id):
    """
    Returns a list of GoodsTypes that can be produced at a given stronghold.
    This logic can be expanded later with specific game rules.
    """
    stronghold = get_object_or_404(StrongholdInstance, id=stronghold_instance_id)
    
    # This is where your game rules go.
    producible_goods = GoodsType.objects.none() # Start with an empty queryset
    
    if stronghold.improvements.filter(improvement_type__name="Craftsmen's Guild").exists():
        # This stronghold can produce non-magical items
        producible_goods = GoodsType.objects.filter(name__in=["Exotic Goods", "Weapons and Armor", "Wooden Goods"])

    if stronghold.improvements.filter(improvement_type__name="Wizard's Academy").exists():
        producible_goods = producible_goods | GoodsType.objects.filter(name="Magic Items")
        
    data = list(producible_goods.values('id', 'name'))
    return JsonResponse(data, safe=False)

def get_existing_strongholds_json(request, realm_name):
    """Returns a list of all strongholds in a given realm."""
    realm = get_object_or_404(Realm, name=realm_name)
    strongholds = StrongholdInstance.objects.filter(realm=realm)
    data = [{'id': sh.id, 'name': f"{sh.name} ({sh.land_unit.name})"} for sh in strongholds]
    return JsonResponse(data, safe=False)

def get_available_upgrades_json(request, stronghold_instance_id):
    """
    Returns a list of improvements that can be built in a specific stronghold.
    It filters based on the stronghold's type and excludes improvements already built.
    """
    stronghold = get_object_or_404(StrongholdInstance, id=stronghold_instance_id)
    
    # Get IDs of improvements already built in this stronghold
    existing_improvement_ids = stronghold.improvements.values_list('improvement_type_id', flat=True)
    
    # Find all possible upgrades that are compatible with this stronghold's type
    # and are not already built
    available_upgrades = StrongholdImprovementType.objects.filter(
        prerequisite_stronghold_types=stronghold.stronghold_type
    ).exclude(
        id__in=existing_improvement_ids
    ).values('id', 'name')
    
    return JsonResponse(list(available_upgrades), safe=False)

def get_upgrade_details_json(request, upgrade_type_id):
    """Returns the specific costs and duration for a selected upgrade."""
    upgrade = get_object_or_404(StrongholdImprovementType, id=upgrade_type_id)
    data = {
        'id': upgrade.id,
        'name': upgrade.name,
        'population_cost': upgrade.population_cost,
        'gold_cost': upgrade.gold_cost,
        'resource_costs': upgrade.resource_costs,
        'duration': upgrade.duration_seasons
    }
    return JsonResponse(data)