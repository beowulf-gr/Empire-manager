from ..models import Realm, OngoingAction, PopulationRace, PopulationUnit 
from django.db import transaction
import random

def get_recruit_population_details():
    return {
        "name": "Recruit Population",
        "slug": "recruit_population", # Add slug here for consistency
        "description": "Recruit new population units of a chosen race. Success depends on the recruiter's charisma.",
        "duration": 0, # Example duration, adjust as needed
        "submit_text": "Start Recruitment",
        "inputs": [
            {"name": "target_race", "label": "Target Race:", "type": "select", "required": True, "options_url": "/realm/get_population_races_json/"},
            {"name": "charisma_modifier", "label": "Charisma Modifier:", "type": "number", "required": True, "default": 0}
        ]
    }

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
        num_recruits = max(0, int((random.randint(1, 10) + charisma_modifier)/5))

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

# def start_recruit_population(realm: Realm, post_data):
#     target_race_id = post_data.get('target_race')
#     charisma_modifier = int(post_data.get('charisma_modifier', 0))
#     duration = int(post_data.get('duration', 1)) # Get duration from form or use default

#     if not target_race_id:
#         # You might want to return an error message or raise an exception here
#         print("Error: Target race is required for Recruit Population action.")
#         return False

#     try:
#         target_race_obj = PopulationRace.objects.get(id=target_race_id)

#         # Store IDs and charisma in action_data
#         action_data = {
#             'target_race_id': target_race_id,
#             'charisma_modifier': charisma_modifier,
#         }

#         OngoingAction.objects.create(
#             realm=realm,
#             action_name="recruit_population",
#             start_season=realm.season,
#             start_year=realm.year,
#             duration=duration,
#             data=action_data
#         )

#         num_recruits = int((random.randint(1, 10) + charisma_modifier)/5) # Example logic for number of recruits
#         print(f"Recruiting {num_recruits} {target_race_obj.name} for {realm.name} with charisma modifier {charisma_modifier}")
#         return True
         
#     except PopulationRace.DoesNotExist:
#         print("Error: Specified race not found.")
#         return False

# def finish_recruit_population(realm: Realm, action_data):
#     # This is where the recruitment effect happens when the action is completed
#     target_race_id = action_data.get('target_race_id')
#     charisma_modifier = action_data.get('charisma_modifier', 0)

#     try:
#         target_race_obj = PopulationRace.objects.get(id=target_race_id)

#         # Number of recruits could depend on charisma, scale, target_race, etc.

#         num_recruits = int((random.randint(1, 10) + charisma_modifier)/5) # Example logic for number of recruits
#         print(f"Recruiting {num_recruits} {target_race_obj.name} for {realm.name} with charisma modifier {charisma_modifier}")

#         with transaction.atomic(): # Use a transaction for multiple object creation
#             for _ in range(num_recruits):
#                 PopulationUnit.objects.create(
#                     realm=realm,
#                     race=target_race_obj,
#                     assigned_to=None
#                 )
#         print(f"Recruited {num_recruits} {target_race_obj.name}s for {realm.name}")
#     except PopulationRace.DoesNotExist:
#         print(f"Error: Target race (ID: {target_race_id}) not found during recruitment completion.")
#     except Exception as e:
#         print(f"An error occurred during recruitment completion: {e}")