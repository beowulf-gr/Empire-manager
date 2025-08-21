from ..models import Realm, OngoingAction, PopulationRace, PopulationUnit, Resource, RealmResource, GoodsType, RealmGoodsType, ActionType, StrongholdType, StrongholdInstance, LandUnit
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
    
def start_construct_stronghold(realm: Realm, post_data):
    """
    Starts the process of constructing a stronghold.
    Validates costs and prerequisites before creating an OngoingAction.
    """
    stronghold_type_id = post_data.get('stronghold_type')
    land_unit_id = post_data.get('land_unit')
    assigned_pop_ids = post_data.getlist('assigned_population')

    if not all([stronghold_type_id, land_unit_id, assigned_pop_ids]):
        return False, "You must select a type, location, and assign population units.", None

    try:
        stronghold_type = StrongholdType.objects.get(id=stronghold_type_id)
        land_unit = LandUnit.objects.get(id=land_unit_id, realm=realm)

        # --- 1. Validate Population Selection ---
        required_pop = stronghold_type.population_cost
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
        if realm.treasury < stronghold_type.gold_cost:
            return False, f"Not enough gold. Requires {stronghold_type.gold_cost}.", None
        
        for resource, cost in stronghold_type.resource_costs.items():
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
            realm.treasury -= stronghold_type.gold_cost
            for resource, cost in stronghold_type.resource_costs.items():
                realm.update_resource_quantity(resource, -cost)
            realm.save()

            # Create the OngoingAction
            action_data = {
                'stronghold_type_id': stronghold_type.id,
                'land_unit_id': land_unit.id
            }

            new_action = OngoingAction.objects.create(
                realm=realm,
                action_name='construct_stronghold',
                start_season=realm.season,
                start_year=realm.year,
                duration=duration,
                data=action_data
            )

            # Assign the user-selected population units
            new_action.assigned_population.set(units_to_assign)
            
            # Set their status to busy
            units_to_assign.update(status='busy')

        # --- 3. Return Success and Data for OngoingAction ---
        message = f"Construction of {stronghold_type.name} has begun at {land_unit.name}, assigning {required_pop} selected population unit(s) and will be finished in {duration} seasons."       
        return True, message, None
        
    except (StrongholdType.DoesNotExist, LandUnit.DoesNotExist):
        return False, "Invalid stronghold type or land unit selected.", None


def finish_construct_stronghold(realm: Realm, action_data: dict):
    """
    Finishes the construction, creating a new StrongholdInstance.
    """
    stronghold_type_id = action_data.get('stronghold_type_id')
    land_unit_id = action_data.get('land_unit_id')

    try:
        stronghold_type = StrongholdType.objects.get(id=stronghold_type_id)
        land_unit = LandUnit.objects.get(id=land_unit_id, realm=realm)
        
        # Create the stronghold instance
        StrongholdInstance.objects.create(
            land_unit=land_unit,
            stronghold_type=stronghold_type,
            realm=realm
        )
        print(f"Completed stronghold '{stronghold_type.name}' for realm '{realm.name}'.")

    except (StrongholdType.DoesNotExist, LandUnit.DoesNotExist):
        print(f"ERROR: Could not complete stronghold for realm '{realm.name}'. Invalid type or land unit ID.")
