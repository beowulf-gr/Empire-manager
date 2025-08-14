from ..models import Realm, OngoingAction, PopulationRace, PopulationUnit, Resource, RealmResource, GoodsType, RealmGoodsType, ActionType, StrongholdType, StrongholdInstance, LandUnit, StrongholdImprovementInstance, StrongholdImprovementType
from django.db import transaction
import random
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP
from django.contrib import messages # For messages within game logic functions

# def get_recruit_population_details():
#     return {
#         "name": "Recruit Population",
#         "slug": "recruit_population", # Add slug here for consistency
#         "description": "Recruit new population units of a chosen race. Success depends on the recruiter's charisma.",
#         "duration": 0, # Example duration, adjust as needed
#         "submit_text": "Start Recruitment",
#         "inputs": [
#             {"name": "target_race", "label": "Target Race:", "type": "select", "required": True, "options_url": "/realm/get_population_races_json/"},
#             {"name": "charisma_modifier", "label": "Charisma Modifier:", "type": "number", "required": True, "default": 0}
#         ]
#     }

def start_recruit_population(realm: Realm, post_data):
    # This action is instant (duration = 0), so all effects happen here.
    # It does NOT create an OngoingAction.
    target_race_id = post_data.get('target_race')
    # Use 0 as default if not a valid integer or missing
    charisma_modifier = int(post_data.get('charisma_modifier', 0) or 0)

    if not target_race_id:
        return False, "Target Race is required for recruitment.", None # Return failure tuple

    try:
        target_race_obj = PopulationRace.objects.get(id=target_race_id)

        # Example recruitment logic:
        # Number of recruits could depend on charisma, races, etc.
        # Ensure num_recruits is at least 0
        roll = random.randint(1, 20) # Simulate a d20 roll
        num_recruits = max(0, int((random.randint(1, 20) + charisma_modifier)/5))
        total_roll = roll + charisma_modifier

        with transaction.atomic():
            for _ in range(num_recruits):
                PopulationUnit.objects.create(
                    realm=realm,
                    race=target_race_obj,
                    assigned_to=None # Initially unassigned
                )
        
        if num_recruits > 0:
            # message = f"Successfully recruited {num_recruits} {target_race_obj.name}!"
            message = f" (Roll: {roll} + {charisma_modifier} = {total_roll}). You successfully recruited {num_recruits} {target_race_obj.name} units!"
            return True, message, None # Indicate success with message
        else:
            message = f"Recruitment attempt for {target_race_obj.name} yielded no new population (Charisma: {charisma_modifier})."
            return True, message, None # Still a success, but with 0 recruits

    except PopulationRace.DoesNotExist:
        return False, "Specified target race not found.", None # Indicate failure
    except ValueError:
        return False, "Charisma modifier must be a valid number.", None # Indicate failure
    except Exception as e:
        return False, f"An unexpected error occurred during recruitment: {e}", None # Indicate failure
    
def start_buy_resources(realm: Realm, post_data):
     # This action is instant (duration = 0), so all effects happen here.
    # It does NOT create an OngoingAction.
    print("--- STARTING BUY RESOURCES ACTION ---")
    print("Full POST data:", post_data) # <--- ADD THIS LINE FOR DEBUGGING
    resource_id = post_data.get('resource_id')
    quantity_str = post_data.get('quantity')
    knowledge_economics_modifier_str = post_data.get('knowledge_economics_modifier')

    print("Resource ID:", resource_id) # <--- ADD THIS LINE FOR DEBUGGING
    print("Quantity:", quantity_str) # <--- ADD THIS LINE FOR DEBUGGING 
    print("Knowledge Economics Modifier:", knowledge_economics_modifier_str) # <--- ADD THIS LINE FOR DEBUGGING

    if not resource_id or not quantity_str or knowledge_economics_modifier_str is None:
        return False, "All fields (Goods Type, Quantity, Knowledge Modifier) are required.", None

    try:
        quantity = int(quantity_str)
        if quantity <= 0:
            return False, "Quantity must be a positive number.", None

        knowledge_economics_modifier = int(knowledge_economics_modifier_str)

        resource_type_obj = Resource.objects.get(id=resource_id)

        # Calculate total cost in Gold for the goods (based on GoodsType.value)
        precise_total_cost_decimal = resource_type_obj.value * Decimal(quantity)
        total_gold_cost = int(min(precise_total_cost_decimal.quantize(Decimal('1.'), rounding=ROUND_HALF_UP), 1))
        #total_gold_cost = precise_total_cost_decimal
        print("Total cost:", total_gold_cost)
        
        # Check if realm has enough Gold in treasury
        current_gold_in_treasury = realm.treasury
        print("Gold:", current_gold_in_treasury)
        if Decimal(current_gold_in_treasury) < total_gold_cost:
            max_affordable_quantity = 0
            if resource_type_obj.value > 0:
                max_affordable_quantity = int(Decimal(current_gold_in_treasury) / Decimal(resource_type_obj.value).quantize(Decimal('1.'), rounding=ROUND_FLOOR))
            
            return False, (
                f"Not enough Gold in treasury to buy {quantity} {resource_type_obj.name}. "
                f"You need {total_gold_cost.quantize(Decimal('1.00'))} Gold but have {current_gold_in_treasury}. "
                f"Max you can buy is {max_affordable_quantity}."
            ), None

        # --- Perform success chance roll (immediately) ---
        success_threshold = 10
        bonus_threshold = 20

        if realm.season == "Winter":
            success_threshold = 15
            bonus_threshold = 25
        # Add other seasonal modifications here if needed

        roll = random.randint(1, 20)
        total_roll = roll + knowledge_economics_modifier

        message_suffix = ""
        acquired_quantity = 0 # Initialize acquired quantity to 0

        with transaction.atomic(): # Ensure atomicity for treasury deduction and goods addition
            # Deduct Gold from Treasury
            # realm.treasury -= total_gold_cost
            # print("Gold:", realm.treasury)
            # realm.save() # Save realm to update treasury

            if total_roll >= success_threshold:
                # Success
                realm.treasury -= total_gold_cost # <--- GOLD DEDUCTION MOVED HERE
                print("Gold:", realm.treasury)
                realm.save() # Save realm to update treasury
                acquired_quantity = quantity # Base quantity
                if total_roll >= bonus_threshold:
                    # Bonus unit
                    acquired_quantity += 1
                    message_suffix = f" (Roll: {roll} + {knowledge_economics_modifier} = {total_roll}). You successfully bought {acquired_quantity} units, with 1 bonus unit!"
                else:
                    message_suffix = f" (Roll: {roll} + {knowledge_economics_modifier} = {total_roll}). You successfully bought {acquired_quantity} units."
                
                # Add the acquired goods
                realm.update_resource_quantity(resource_type_obj.name, acquired_quantity)
                return True, f"Purchase of {resource_type_obj.name} completed." + message_suffix, None
            else:
                # Failure
                message_suffix = f" (Roll: {roll} + {knowledge_economics_modifier} = {total_roll}). The purchase failed. No goods acquired."
                # Gold is still deducted even on failure (cost of trying)
                return False, f"Purchase of {resource_type_obj.name} failed." + message_suffix, None

    except ValueError:
        return False, "Quantity and Knowledge Modifier must be numbers.", None
    except GoodsType.DoesNotExist:
        return False, "Specified Resource Type not found.", None
    except Exception as e:
        print(f"Error during instant buy_resources action: {e}")
        return False, f"An unexpected error occurred: {e}", None

def start_buy_goods(realm: Realm, post_data):
     # This action is instant (duration = 0), so all effects happen here.
    # It does NOT create an OngoingAction.
    print("--- STARTING BUY RESOURCES ACTION ---")
    print("Full POST data:", post_data) # <--- ADD THIS LINE FOR DEBUGGING
    good_id = post_data.get('goods_type_id')
    quantity_str = post_data.get('quantity')
    knowledge_economics_modifier_str = post_data.get('knowledge_economics_modifier')

    print("Resource ID:", good_id) # <--- ADD THIS LINE FOR DEBUGGING
    print("Quantity:", quantity_str) # <--- ADD THIS LINE FOR DEBUGGING 
    print("Knowledge Economics Modifier:", knowledge_economics_modifier_str) # <--- ADD THIS LINE FOR DEBUGGING

    if not good_id or not quantity_str or knowledge_economics_modifier_str is None:
        return False, "All fields (Goods Type, Quantity, Knowledge Modifier) are required.", None

    try:
        quantity = int(quantity_str)
        if quantity <= 0:
            return False, "Quantity must be a positive number.", None

        knowledge_economics_modifier = int(knowledge_economics_modifier_str)

        good_type_obj = GoodsType.objects.get(id=good_id)

        # Calculate total cost in Gold for the goods (based on GoodsType.value)
        precise_total_cost_decimal = good_type_obj.value * Decimal(quantity)
        total_gold_cost = int(min(precise_total_cost_decimal.quantize(Decimal('1.'), rounding=ROUND_HALF_UP), 1))
        
        # Check if realm has enough Gold in treasury
        current_gold_in_treasury = realm.treasury
        if Decimal(current_gold_in_treasury) < total_gold_cost:
            max_affordable_quantity = 0
            if good_type_obj.value > 0:
                max_affordable_quantity = int(Decimal(current_gold_in_treasury) / Decimal(good_type_obj.value).quantize(Decimal('1.'), rounding=ROUND_FLOOR))
            
            return False, (
                f"Not enough Gold in treasury to buy {quantity} {good_type_obj.name}. "
                f"You need {total_gold_cost.quantize(Decimal('1.00'))} Gold but have {current_gold_in_treasury}. "
                f"Max you can buy is {max_affordable_quantity}."
            ), None

        # --- Perform success chance roll (immediately) ---
        success_threshold = 10
        bonus_threshold = 20

        if realm.season == "Winter":
            success_threshold = 15
            bonus_threshold = 25
        # Add other seasonal modifications here if needed

        roll = random.randint(1, 20)
        total_roll = roll + knowledge_economics_modifier

        message_suffix = ""
        acquired_quantity = 0 # Initialize acquired quantity to 0

        with transaction.atomic(): # Ensure atomicity for treasury deduction and goods addition
            # # Deduct Gold from Treasury
            # realm.treasury -= total_gold_cost
            # realm.save() # Save realm to update treasury

            if total_roll >= success_threshold:
                # Success
                realm.treasury -= total_gold_cost # <--- GOLD DEDUCTION MOVED HERE
                realm.save() # Save realm to update treasury
                acquired_quantity = quantity # Base quantity
                if total_roll >= bonus_threshold:
                    # Bonus unit
                    acquired_quantity += 1
                    message_suffix = f" (Roll: {roll} + {knowledge_economics_modifier} = {total_roll}). You successfully bought {acquired_quantity} units, with 1 bonus unit!"
                else:
                    message_suffix = f" (Roll: {roll} + {knowledge_economics_modifier} = {total_roll}). You successfully bought {acquired_quantity} units."
                
                # Add the acquired goods
                realm.update_goods_quantity(good_type_obj.name, acquired_quantity)
                return True, f"Purchase of {good_type_obj.name} completed." + message_suffix, None
            else:
                # Failure
                message_suffix = f" (Roll: {roll} + {knowledge_economics_modifier} = {total_roll}). The purchase failed. No goods acquired."
                # Gold is still deducted even on failure (cost of trying)
                return False, f"Purchase of {good_type_obj.name} failed." + message_suffix, None

    except ValueError:
        return False, "Quantity and Knowledge Modifier must be numbers.", None
    except GoodsType.DoesNotExist:
        return False, "Specified Good Type not found.", None
    except Exception as e:
        print(f"Error during instant buy_goods action: {e}")
        return False, f"An unexpected error occurred: {e}", None

def calculate_construct_stronghold_cost(realm, stronghold_type_id):
    """
    Calculates the cost for the Construct Stronghold action.
    This is the SINGLE SOURCE OF TRUTH for this action's cost.
    """
    try:
        stronghold_type = StrongholdType.objects.get(id=stronghold_type_id)
        costs = {
            'population': stronghold_type.population_cost,
            'gold': stronghold_type.gold_cost,
            **stronghold_type.resource_costs  # Unpacks the JSON field into the dict
        }
        return costs
    except StrongholdType.DoesNotExist:
        return {} # Return empty dict if the type is invalid
    
def start_construct_stronghold(realm: Realm, post_data):
    """
    Starts the process of constructing a stronghold.
    Validates costs and prerequisites before creating an OngoingAction.
    """
    stronghold_type_id = post_data.get('stronghold_type')
    land_unit_id = post_data.get('land_unit')
    assigned_pop_ids = post_data.getlist('assigned_population')
    stronghold_name = post_data.get('stronghold_name', '')
    land_unit = LandUnit.objects.get(id=land_unit_id, realm=realm)
    stronghold_type = StrongholdType.objects.get(id=stronghold_type_id)

    if not all([stronghold_type_id, land_unit_id, assigned_pop_ids]):
        return False, "You must select a type, location, and assign population units.", None

    try:
        # --- 1. Get Authoritative Cost ---
        # Call the single source of truth to get the definitive cost.
        costs = calculate_construct_stronghold_cost(realm, stronghold_type_id)
        if not costs:
             return False, "Invalid stronghold type selected.", None
        
        required_pop = costs.get("population", 0)
        gold_cost = costs.get("gold", 0)

        if len(assigned_pop_ids) != required_pop:
            return False, f"Incorrect number of population units assigned. This construction requires {required_pop}.", None

        # Fetch the actual PopulationUnit objects to ensure they are valid
        units_to_assign = PopulationUnit.objects.filter(
            id__in=assigned_pop_ids, 
            realm=realm, 
            status='idle'
        )

        # If the query returned fewer units than selected, it means some were invalid
        if units_to_assign.count() != required_pop:
            return False, "Invalid or busy population units selected. Please refresh and try again.", None

        
        # --- 1. Check Prerequisites ---
        if realm.treasury < gold_cost:
            return False, f"Not enough gold. Requires {gold_cost}.", None
        
        for resource, cost in costs.items():
            if resource not in ['population', 'gold']:
                if realm.get_resource_quantity(resource) < cost:
                    return False, f"Not enough {resource}. Requires {cost}.", None
            
        # --- 2 DYNAMIC DURATION LOGIC ---
        # 1. Get the base duration from the selected StrongholdType
        duration = stronghold_type.duration_seasons

        # 2. Check for seasonal modifications from the ActionType
        # We need the ActionType object for 'construct_stronghold'
        action_type = ActionType.objects.get(action_key='construct_stronghold')
        current_season_name = realm.season.name
        
        if current_season_name in action_type.seasonal_modifications:
            mods = action_type.seasonal_modifications[current_season_name]
            duration += mods.get('duration_add', 0) # Add the extra duration
        # -----------------------------
        
        # --- 2. Pay Costs ---
        with transaction.atomic():
            realm.treasury -= gold_cost
            for resource, cost in costs.items():
                if resource not in ['population', 'gold']:
                    realm.update_resource_quantity(resource, -cost)

            units_to_assign.update(status='busy')
            realm.save()
            

        # --- 3. Return Success and Data for OngoingAction ---
        message = f"Construction of {stronghold_type.name} has begun at {land_unit.name}, assigning {required_pop} selected population unit(s) and will be finished in {duration} seasons."       
        action_data = {
            'stronghold_type_id': stronghold_type.id,
            'land_unit_id': int(land_unit_id),
            'assigned_pop_ids': [int(pid) for pid in assigned_pop_ids],
            'final_duration': duration, # Pass the correct duration
            'stronghold_name': stronghold_name # <-- Pass the name along
        }
        
        return True, message, action_data
        
    except (StrongholdType.DoesNotExist, LandUnit.DoesNotExist):
        return False, "Invalid stronghold type or land unit selected.", None


def finish_construct_stronghold(realm: Realm, action_data: dict, completed_action: OngoingAction):
    """
    Finishes the construction, creating a new StrongholdInstance.
    """
    stronghold_type_id = action_data.get('stronghold_type_id')
    land_unit_id = action_data.get('land_unit_id')
    stronghold_name = action_data.get('stronghold_name', '')

    try:
        stronghold_type = StrongholdType.objects.get(id=stronghold_type_id)
        land_unit = LandUnit.objects.get(id=land_unit_id, realm=realm)
        
        # Create the stronghold instance
        StrongholdInstance.objects.create(
            land_unit=land_unit,
            stronghold_type=stronghold_type,
            realm=realm,
            name=stronghold_name # <-- Use the captured name here
        )

        for unit in completed_action.assigned_population.all():
            unit.status = 'idle'
            unit.save()

        print(f"Completed stronghold '{stronghold_name or stronghold_type.name}' for realm '{realm.name}'.")

    except (StrongholdType.DoesNotExist, LandUnit.DoesNotExist):
        print(f"ERROR: Could not complete stronghold for realm '{realm.name}'. Invalid type or land unit ID.")

def calculate_build_roads_cost(realm, land_unit_ids):
    """
    Calculates the cost for the Build Roads action.
    This is the SINGLE SOURCE OF TRUTH for this action's cost.
    """
    land_units = LandUnit.objects.filter(id__in=land_unit_ids, realm=realm)
    
    costs = {"population": 1, "Stone": 1, "Wood": 2}
    
    for unit in land_units:
        if not hasattr(unit, 'stronghold') or not unit.stronghold:
            costs["population"] += 1
            costs["Wood"] += 1
            
    return costs

def start_build_roads(realm: Realm, post_data):
    selected_land_ids = post_data.getlist('land_units_for_roads')
    assigned_pop_ids = post_data.getlist('assigned_population') # <-- Get user selection
    if not selected_land_ids or len(selected_land_ids) > 4:
        return False, "You must select between 1 and 4 land units.", None

    land_units = LandUnit.objects.filter(id__in=selected_land_ids, realm=realm, has_roads=False)
    if land_units.count() != len(selected_land_ids):
        return False, "One or more selected land units are invalid or already have roads.", None
    
    # Call the single source of truth to get the authoritative cost
    costs = calculate_build_roads_cost(realm, selected_land_ids)

    required_pop = costs.get("population", 0)
    wood_cost = costs.get("Wood", 0)
    stone_cost = costs.get("Stone", 0)

    # Validate the user's selection
    if len(assigned_pop_ids) != required_pop:
        return False, f"Incorrect number of population units assigned. This action requires {required_pop}.", None
    
    units_to_assign = PopulationUnit.objects.filter(id__in=assigned_pop_ids, realm=realm, status='idle')
    if units_to_assign.count() != required_pop:
        return False, "Invalid or busy population units were selected.", None
    
    # Check resource costs
    # wood_cost = 2 + (len(land_units) - land_units.filter(stronghold__isnull=False).count())
    # stone_cost = 1
    if realm.get_resource_quantity("Wood") < wood_cost or realm.get_resource_quantity("Stone") < stone_cost:
        return False, "Not enough resources.", None

    with transaction.atomic():
        realm.update_resource_quantity("Wood", -wood_cost)
        realm.update_resource_quantity("Stone", -stone_cost)
        units_to_assign.update(status='busy')

    action_data = {
        'land_unit_ids': [int(uid) for uid in selected_land_ids],
        'assigned_pop_ids': [unit.id for unit in units_to_assign]
    }
    return True, f"Road construction has begun, assigning {required_pop} population unit(s).", action_data

def finish_build_roads(realm: Realm, action_data: dict, completed_action: OngoingAction):
    land_unit_ids = action_data.get('land_unit_ids', [])
    LandUnit.objects.filter(id__in=land_unit_ids, realm=realm).update(has_roads=True)
    
    # Release population
    completed_action.assigned_population.all().update(status='idle')
    print(f"Finished building roads for realm {realm.name}.")

def calculate_build_mine_cost():
    """
    Calculates the cost for the Build Mine action.
    This is the SINGLE SOURCE OF TRUTH for this action's cost.
    """    
    costs = {"population": 1, "Stone": 4, "Wood": 3, "Gold": 3}
            
    return costs


def start_build_mine(realm: Realm, post_data):
    land_unit_id = post_data.get('land_unit_for_mine')
    assigned_pop_ids = post_data.getlist('assigned_population') # <-- Get user selection
    if not land_unit_id:
        return False, "You must select a land unit.", None

    try:
        land_unit = LandUnit.objects.get(id=land_unit_id, realm=realm, has_mine=False)
    except LandUnit.DoesNotExist:
        return False, "Invalid land unit selected.", None

    # Costs
    costs = calculate_build_mine_cost()
    stone_cost, gold_cost, wood_cost = costs.get("Stone", 0), costs.get("Gold", 0), costs.get("Wood", 0)

    # Check population and resources
    required_pop = costs.get("population", 0)
    if len(assigned_pop_ids) != required_pop:
        return False, "You must assign exactly one population unit to build a mine.", None

    units_to_assign = PopulationUnit.objects.filter(id__in=assigned_pop_ids, realm=realm, status='idle')
    if units_to_assign.count() != required_pop:
        return False, "The selected population unit is invalid or busy.", None
    if realm.get_resource_quantity("Stone") < stone_cost or realm.treasury < gold_cost or realm.get_resource_quantity("Wood") < wood_cost:
        return False, "Not enough resources.", None

    with transaction.atomic():
        # Pay costs
        realm.treasury -= gold_cost
        realm.update_resource_quantity("Stone", -stone_cost)
        realm.update_resource_quantity("Wood", -wood_cost)
        
        # Assign population
        units_to_assign.update(status='busy')

    action_data = {
        'land_unit_id': land_unit.id,
        'assigned_pop_ids': [unit.id for unit in units_to_assign]
    }
    return True, f"Mine construction has begun on {land_unit.name}.", action_data

def finish_build_mine(realm: Realm, action_data: dict, completed_action: OngoingAction):
    land_unit_id = action_data.get('land_unit_id')
    try:
        land_unit = LandUnit.objects.get(id=land_unit_id, realm=realm)
        
        # Increase production (this is a simplified example)
        # A more robust solution would modify the LandUnit's production JSON field
        # For now, we'll just mark it as having a mine.
        land_unit.has_mine = True
        land_unit.save()

        # Release population
        completed_action.assigned_population.all().update(status='idle')
        print(f"Finished building mine on {land_unit.name}.")
    except LandUnit.DoesNotExist:
        print(f"ERROR: Could not finish mine for realm {realm.name}, land unit not found.")

def start_upgrade_stronghold(realm: Realm, post_data):
    stronghold_id = post_data.get('stronghold_to_upgrade')
    upgrade_id = post_data.get('upgrade_type')
    assigned_pop_ids = post_data.getlist('assigned_population')

    if not all([stronghold_id, upgrade_id, assigned_pop_ids]):
        return False, "You must select a stronghold, an upgrade, and assign population.", None

    try:
        stronghold = StrongholdInstance.objects.get(id=stronghold_id, realm=realm)
        upgrade = StrongholdImprovementType.objects.get(id=upgrade_id)

        # Validate prerequisites (costs, population, etc.)
        required_pop = upgrade.population_cost
        if len(assigned_pop_ids) != required_pop:
            return False, f"Incorrect number of population units assigned. Requires {required_pop}.", None
        
        # ... (Add similar checks for gold and resource costs against realm's treasury/stockpiles) ...

        units_to_assign = PopulationUnit.objects.filter(id__in=assigned_pop_ids, realm=realm, status='idle')
        if units_to_assign.count() != required_pop:
            return False, "Invalid or busy population units were selected.", None
            
        with transaction.atomic():
            # Pay costs
            realm.treasury -= upgrade.gold_cost
            for resource, cost in upgrade.resource_costs.items():
                realm.update_resource_quantity(resource, -cost)
            
            # Assign population
            units_to_assign.update(status='busy')
            realm.save()

        action_data = {
            'stronghold_instance_id': stronghold.id,
            'upgrade_type_id': upgrade.id,
            'assigned_pop_ids': [unit.id for unit in units_to_assign],
            'final_duration': upgrade.duration_seasons
        }
        return True, f"Upgrade has begun on {stronghold.name}.", action_data
        
    except (StrongholdInstance.DoesNotExist, StrongholdImprovementType.DoesNotExist, ValueError):
        return False, "Invalid data submitted.", None

def finish_upgrade_stronghold(realm: Realm, action_data: dict, completed_action: OngoingAction):
    stronghold_id = action_data.get('stronghold_instance_id')
    upgrade_id = action_data.get('upgrade_type_id')

    try:
        stronghold = StrongholdInstance.objects.get(id=stronghold_id, realm=realm)
        upgrade = StrongholdImprovementType.objects.get(id=upgrade_id)
        
        with transaction.atomic():
            # Create the new improvement instance
            StrongholdImprovementInstance.objects.create(
                stronghold_instance=stronghold,
                improvement_type=upgrade
            )
            # Release population
            completed_action.assigned_population.all().update(status='idle')
        print(f"Finished upgrade '{upgrade.name}' for stronghold '{stronghold.name}'.")
    except (StrongholdInstance.DoesNotExist, StrongholdImprovementType.DoesNotExist):
        print(f"ERROR: Could not finish upgrade for realm '{realm.name}'.")

def calculate_produce_goods_cost(realm, good_type_id, resource_id=None, quantity=1):
    """Calculates the dynamic cost for the Produce Goods action."""
    try:
        good_type = GoodsType.objects.get(id=good_type_id)
        costs = {'population': 1 * quantity} # Base population cost
        is_overpaying = False # Default to false

        resource_to_use = None
        if good_type.required_resource_specific:
            resource_to_use = good_type.required_resource_specific
        elif resource_id:
            resource_to_use = Resource.objects.get(id=resource_id)

        if resource_to_use:
            if resource_to_use.value <= 0: return {} # Avoid division by zero
            total_gold_value_needed = Decimal(good_type.cost_in_gold) * Decimal(quantity)
            calculated_quantity = int(total_gold_value_needed / resource_to_use.value)
            quantity_needed = max(1, calculated_quantity)
            if Decimal(quantity_needed) * resource_to_use.value > total_gold_value_needed:
                is_overpaying = True
            costs[resource_to_use.name] = quantity_needed
        
        return {'costs': costs, 'is_overpaying': is_overpaying}
    except (GoodsType.DoesNotExist, Resource.DoesNotExist):
        return {}
    
def start_produce_goods(realm: Realm, post_data):
    """
    Starts the production of a trade good, validating all costs and assignments.
    """
    good_id = post_data.get('good_to_produce')
    stronghold_id = post_data.get('production_stronghold')
    resource_id = post_data.get('resource_to_use') # Will be present if a category was required
    assigned_pop_ids = post_data.getlist('assigned_population')

    quantity = int(post_data.get('quantity', 1))

    if not all([good_id, stronghold_id, assigned_pop_ids]):
        return False, "You must select a good, a location, and assign population.", None

    try:
        good_type = GoodsType.objects.get(id=good_id)
        stronghold = StrongholdInstance.objects.get(id=stronghold_id, realm=realm)
        
        # --- 1. Determine and Validate the Resource Cost ---
        required_pop = 1 # Assuming a static population cost of 1 for now
        resource_to_consume = None
        
        if good_type.required_resource_specific:
            resource_to_consume = good_type.required_resource_specific
        elif good_type.required_resource_category:
            if not resource_id:
                return False, "You must select a resource to produce this good.", None
            resource_to_consume = Resource.objects.get(id=resource_id, category=good_type.required_resource_category)
        
        if not resource_to_consume:
            return False, "A valid resource cost could not be determined for this good.", None

        # Calculate the required quantity of the chosen resource
        # cost_in_gold / resource_value = quantity needed
        if resource_to_consume.value <= 0:
            return False, "Cannot calculate cost for a resource with zero value.", None
        
        total_gold_value_needed = Decimal(good_type.cost_in_gold) * Decimal(quantity)
        calculated_quantity = int(total_gold_value_needed / resource_to_consume.value)
        required_quantity = max(1, calculated_quantity)
        
        if realm.get_resource_quantity(resource_to_consume.name) < required_quantity:
            return False, f"Not enough {resource_to_consume.name}. Requires {required_quantity}.", None
            
        # --- 2. Validate Population ---
        units_to_assign = PopulationUnit.objects.filter(id__in=assigned_pop_ids, realm=realm, status='idle')
        if units_to_assign.count() != required_pop:
            return False, "Invalid or busy population units were selected.", None

        # --- 3. Pay Costs & Assign Population ---
        with transaction.atomic():
            realm.update_resource_quantity(resource_to_consume.name, -required_quantity)
            units_to_assign.update(status='busy')

        # --- 4. Return Data for OngoingAction ---
        message = f"Production of {good_type.name} has begun at {stronghold.name}."
        action_data = {
            'good_type_id': good_type.id,
            'assigned_pop_ids': [unit.id for unit in units_to_assign],
            'final_duration': good_type.duration
        }
        
        return True, message, action_data

    except (GoodsType.DoesNotExist, StrongholdInstance.DoesNotExist, Resource.DoesNotExist, ValueError):
        return False, "Invalid data submitted.", None


def finish_produce_goods(realm: Realm, action_data: dict, completed_action: OngoingAction):
    """
    Finishes the production, adding the good and releasing the population.
    """
    good_id = action_data.get('good_type_id')
    if not good_id:
        print(f"ERROR: No good_type_id in action_data for realm {realm.name}")
        return

    try:
        good_type = GoodsType.objects.get(id=good_id)
        with transaction.atomic():
            # Add one unit of the completed good to the realm's inventory
            realm.update_goods_quantity(good_type.name, 1)

            # Release the assigned population
            completed_action.assigned_population.all().update(status='idle')
        
        print(f"Finished producing '{good_type.name}' for realm '{realm.name}'.")

    except GoodsType.DoesNotExist:
        print(f"ERROR: Could not finish production for realm '{realm.name}'. Invalid good_type_id.")
