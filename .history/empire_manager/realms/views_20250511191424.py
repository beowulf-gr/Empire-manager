from django.shortcuts import render, redirect, get_object_or_404
from .models import Realm, LandUnit, PopulationUnit, LandUnitType
from django.http import HttpResponse, Http404
from django.contrib import messages
from .forms import RealmInfoForm, TreasuryForm, ResourcesForm, LandUnitForm, PopulationUnitForm, PopulationRace
from django.forms import formset_factory, modelformset_factory
from django.urls import reverse

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
    if request.method == "POST":
        name = request.POST.get("name")
        ruler = request.POST.get("ruler")
        
        if not name or not ruler:
            messages.error(request, "Name and ruler are required.")
        elif Realm.objects.filter(name=name).exists():
            messages.error(request, "A realm with that name already exists.")
        else:
            request.session['new_realm'] = {
                "name": name,
                "ruler": ruler,
                "treasury": 0,
                "resources": {},
                "land_units": [],
                "population_units": []
            }
            print(f"Session after step 1: {request.session.get('new_realm')}")
            return redirect('create_realm_step_2')

    return render(request, 'realms/steps/step_1_name_ruler.html')

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
        form = ResourcesForm(request.POST)
        if form.is_valid():
            data = request.session.get('new_realm', {}).copy()
            data['resources'] = form.cleaned_data
            request.session['new_realm'] = data

            print(f"Session after resources step: {request.session.get('new_realm')}")
            return redirect('create_realm_step_4')
    else:
        # Pre-fill form with session data if available
        initial_data = request.session.get('new_realm', {}).get('resources', {})
        form = ResourcesForm(initial=initial_data)

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
                PopulationUnit.objects.create(
                    realm=realm,
                    race=pop['race']
                )

            # Cleanup session as we no longer need it for existing realms
            del request.session['new_realm']
        else:    
            realm = Realm.objects.create(
                name=data['name'],
                ruler=data['ruler'],
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
        print(f"This one is triggered")
        context["realm"] = {
            'name': realm.name,
            'ruler': realm.ruler,
            'treasury': realm.treasury,
            'resources': realm.resources,
            'land_units': list(realm.land_units.values('name', 'unit_type__name')),
            'population_units': list(realm.population_units.values('race__name'))
        }
    else:
        print(f"This is triggered")
        context["realm"] = request.session.get('new_realm', {})

    return render(request, 'realms/steps/review.html', context)

# Show the details of a specific realm
def realm_detail(request, name):
    realm = get_object_or_404(Realm, name=name)  # Fetch the realm by its name
    land_units = realm.land_units.all()
    population_units = PopulationUnit.objects.filter(realm=realm)  # Get all population units for the realm
    return render(request, 'realms/realm_detail.html', {'realm': realm, 'land_units': land_units, 'population_units': population_units})

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
            extra=1,
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