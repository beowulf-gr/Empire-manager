from ..models import Realm, OngoingAction, PopulationRace
from django.db import transaction
import random

def get_recruit_population_details():
    return {
        "name": "Recruit Population",
        "description": "Recruit new population units of a chosen race. Success depends on the recruiter's charisma.",
        "duration": 2 # Example duration, adjust as needed
    }

def start_recruit_population(realm: Realm, post_data):
    target_race_id = post_data.get('target_race')
    recruiter_race_id = post_data.get('recruiter_race')
    charisma_modifier = int(post_data.get('charisma_modifier', 0))
    duration = int(post_data.get('duration', 1)) # Get duration from form or use default

    if not target_race_id or not recruiter_race_id:
        # You might want to return an error message or raise an exception here
        print("Error: Target race and Recruiter race are required for Recruit Population action.")
        return False

    try:
        target_race_obj = PopulationRace.objects.get(id=target_race_id)
        recruiter_race_obj = PopulationRace.objects.get(id=recruiter_race_id)

        # Store IDs and charisma in action_data
        action_data = {
            'target_race_id': target_race_id,
            'recruiter_race_id': recruiter_race_id,
            'charisma_modifier': charisma_modifier,
        }

        OngoingAction.objects.create(
            realm=realm,
            action_name="recruit_population", # Use a consistent internal action_type key
            start_season=realm.season,
            start_year=realm.year,
            duration=duration,
            data=action_data
        )
        return True
    except PopulationRace.DoesNotExist:
        print("Error: One or both specified races not found.")
        return False

def finish_recruit_population(realm: Realm, action_data):
    # This is where the recruitment effect happens when the action is completed
    target_race_id = action_data.get('target_race_id')
    charisma_modifier = action_data.get('charisma_modifier', 0)

    try:
        target_race_obj = PopulationRace.objects.get(id=target_race_id)
        # Example recruitment logic:
        # Number of recruits could depend on charisma, scale, target_race, etc.
        num_recruits = max(1, 5 + charisma_modifier) # Minimum 1 recruit

        with transaction.atomic(): # Use a transaction for multiple object creation
            for _ in range(num_recruits):
                # Create new PopulationUnit objects
                from ..models import PopulationUnit # Import locally to avoid circular dependency
                PopulationUnit.objects.create(
                    realm=realm,
                    race=target_race_obj,
                    assigned_to=None # Initially unassigned
                )
        print(f"Recruited {num_recruits} {target_race_obj.name}s for {realm.name}")
    except PopulationRace.DoesNotExist:
        print(f"Error: Target race (ID: {target_race_id}) not found during recruitment completion.")
    except Exception as e:
        print(f"An error occurred during recruitment completion: {e}")