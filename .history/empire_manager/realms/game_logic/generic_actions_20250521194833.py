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