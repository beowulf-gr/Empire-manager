from ..models import Realm, OngoingAction, PopulationRace, PopulationUnit, Resource, RealmResource, GoodsType, RealmGoodsType
from django.db import transaction
import random
from decimal import Decimal, ROUND_FLOOR
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
        num_recruits = max(0, int((random.randint(1, 20) + charisma_modifier)/5))

        with transaction.atomic():
            for _ in range(num_recruits):
                PopulationUnit.objects.create(
                    realm=realm,
                    race=target_race_obj,
                    assigned_to=None # Initially unassigned
                )
        
        if num_recruits > 0:
            message = f"Successfully recruited {num_recruits} {target_race_obj.name}!"
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
    
def start_buy_resources():
     # This action is instant (duration = 0), so all effects happen here.
    # It does NOT create an OngoingAction.
    goods_type_id = post_data.get('goods_type_id')
    quantity_str = post_data.get('quantity')
    knowledge_economics_modifier_str = post_data.get('knowledge_economics_modifier')

    if not goods_type_id or not quantity_str or knowledge_economics_modifier_str is None:
        return False, "All fields (Goods Type, Quantity, Knowledge Modifier) are required.", None

    try:
        quantity = int(quantity_str)
        if quantity <= 0:
            return False, "Quantity must be a positive number.", None

        knowledge_economics_modifier = int(knowledge_economics_modifier_str)

        goods_type_obj = GoodsType.objects.get(id=goods_type_id)

        # Calculate total cost in Gold for the goods (based on GoodsType.value)
        total_gold_cost = Decimal(goods_type_obj.value) * Decimal(quantity)
        
        # Check if realm has enough Gold in treasury
        current_gold_in_treasury = realm.treasury
        if Decimal(current_gold_in_treasury) < total_gold_cost:
            max_affordable_quantity = 0
            if goods_type_obj.value > 0:
                max_affordable_quantity = int(Decimal(current_gold_in_treasury) / Decimal(goods_type_obj.value).quantize(Decimal('1.'), rounding=ROUND_FLOOR))
            
            return False, (
                f"Not enough Gold in treasury to buy {quantity} {goods_type_obj.name}. "
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
            realm.treasury -= total_gold_cost
            realm.save() # Save realm to update treasury

            if total_roll >= success_threshold:
                # Success
                acquired_quantity = quantity # Base quantity
                if total_roll > bonus_threshold:
                    # Bonus unit
                    acquired_quantity += 1
                    message_suffix = f" (Roll: {roll} + {knowledge_economics_modifier} = {total_roll}). You successfully bought {acquired_quantity} units, with 1 bonus unit!"
                else:
                    message_suffix = f" (Roll: {roll} + {knowledge_economics_modifier} = {total_roll}). You successfully bought {acquired_quantity} units."
                
                # Add the acquired goods
                realm.update_goods_quantity(goods_type_obj.name, acquired_quantity)
                return True, f"Purchase of {goods_type_obj.name} completed." + message_suffix, None
            else:
                # Failure
                message_suffix = f" (Roll: {roll} + {knowledge_economics_modifier} = {total_roll}). The purchase failed. No goods acquired."
                # Gold is still deducted even on failure (cost of trying)
                return False, f"Purchase of {goods_type_obj.name} failed." + message_suffix, None

    except ValueError:
        return False, "Quantity and Knowledge Modifier must be numbers.", None
    except GoodsType.DoesNotExist:
        return False, "Specified Goods Type not found.", None
    except Exception as e:
        print(f"Error during instant buy_goods action: {e}")
        return False, f"An unexpected error occurred: {e}", None

# finish_buy_goods is no longer used for this action and can be removed from this file.
# If you remove it, also remove its entry from ACTION_HANDLERS.
# For clarity, I'll comment it out here.
# def finish_buy_goods(realm: Realm, action_data):
#     # This function is not called for instant actions like "Buy Goods"
#     print("WARNING: finish_buy_goods was called for an instant action. This should not happen.")
#     pass