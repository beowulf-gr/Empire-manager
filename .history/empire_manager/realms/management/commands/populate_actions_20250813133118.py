from django.core.management.base import BaseCommand
from realms.models import ActionType, Descriptor, Season

class Command(BaseCommand):
    help = 'Populates the ActionType model from definitions.'

    def handle(self, *args, **kwargs):

        self.stdout.write("Populating ActionTypes...")
        
        # Data from your action_definitions.py
        actions_to_create = [
            {
                "action_key": "buy_resources", "name": "Buy Resources",
                "description": "Purchase resources from the market.", "duration": 0,
                "submit_text": "Buy Resources",
                "descriptors": [], "seasons": [] # All seasons
            },
            {
                "action_key": "buy_goods", "name": "Buy Goods",
                "description": "Purchase trade goods from the market.", "duration": 0,
                "submit_text": "Buy Trade Goods",
                "descriptors": [], "seasons": [] # All seasons
            },
            {
                "action_key": "recruit_population", "name": "Recruit Population",
                "description": "Recruit new population units of a chosen race. Success depends on the recruiter's charisma.", "duration": 0,
                "submit_text": "Start Recruitment",
                "descriptors": ["Limited"], "seasons": [], # All seasons 
                "inputs": [
                    {"name": "target_race", "label": "Target Race:", "type": "select", "required": True, "options_url": "/realm/get_population_races_json/"},
                    {"name": "charisma_modifier", "label": "Charisma Modifier:", "type": "number", "required": True, "default": 0}
                ]
            },
            {
                "action_key": "construct_stronghold", "name": "Construct Stronghold",
                "description": "Build a new stronghold on an available land unit. Costs and duration vary by the type of stronghold selected.", "duration": 1,
                "submit_text": "Start Construction",
                "descriptors": ["Construction"], "seasons": ["Spring", "Summer", "Fall"],
                "seasonal_modifications": {
                    "Fall": {"duration_add": 2}, 
                    "Summer": {"duration_add": 1}
                },
                "inputs": [
                    {
                        "name": "stronghold_type", "label": "Stronghold Type:", "type": "select", 
                        "required": True, "options_url": "/realm/get_stronghold_types_json/"
                    },
                    {
                        "name": "land_unit", "label": "Location (Land Unit):", "type": "select",
                        "required": True, "options_url": "/realm/placeholder/get_land_units_json/" # Placeholder will be replaced by JS
                    },
                    {
                        "name": "stronghold_name", "label": "Stronghold Name (Optional):", "type": "text",
                        "required": False 
                    }
                ]
            },
            {
                "action_key": "build_roads", "name": "Build Roads",
                "description": "Connect up to 4 land areas with roads. Costs increase for areas without a stronghold.", "duration": 2,
                "submit_text": "Build Roads", "descriptors": ["Construction"], "seasons": ["Spring", "Summer", "Fall"],
                "seasonal_modifications": {
                    "Fall": {"duration_add": 2}, 
                    "Summer": {"duration_add": 1}
                },
                "inputs": [
                    {
                        "name": "land_units_for_roads", "label": "Select up to 4 Land Units to build roads on:", "type": "checklist", 
                        "required": True, "options_url": "/realm/placeholder/get_road_eligible_land_units_json/", "max_select": 4
                    }
                ]
            },
            {
                "action_key": "build_mine", "name": "Build Mine",
                "description": "Construct a mine on a mineral or stone-producing land unit to increase its output.", "duration": 2,
                "submit_text": "Build Mine", "descriptors": ["Construction"], "seasons": ["Spring", "Summer", "Fall"],
                "seasonal_modifications": {
                    "Fall": {"duration_add": 2}, 
                    "Summer": {"duration_add": 1}
                },
                "inputs": [
                    {
                        "name": "land_unit_for_mine", "label": "Select a Land Unit to build a mine on:", "type": "select", 
                        "required": True, "options_url": "/realm/placeholder/get_mine_eligible_land_units_json/"
                    }
                ]
            },
            {
                "action_key": "produce_goods", "name": "Produce Trade Goods",
                "description": "Assign free population units to strongholds to transform raw resources into finished products", "duration": 1, # This will be dynamic based on the chosen good
                "submit_text": "Begin Production", "descriptors": [], "seasons": [], # All seasons,
                "inputs": [
                    {
                        "name": "good_to_produce",
                        "label": "Select Good to Produce:",
                        "type": "select",
                        "required": True,
                        # This now points to the new URL that lists all possible goods
                        "options_url": "/realm/placeholder/get_all_producible_goods_json/"
                    }
                ]
            },
            {
                "action_key": "upgrade_stronghold", "name": "Upgrade Stronghold",
                "description": "Construct a new improvement like a Marketplace or Walls in an existing stronghold.",
                "duration": 1, # This will be dynamic based on the chosen upgrade
                "submit_text": "Begin Upgrade",
                "descriptors": ["Construction"], "seasons": [],
                "inputs": [
                    {
                        "name": "stronghold_to_upgrade",
                        "label": "Select Stronghold to Upgrade:",
                        "type": "select",
                        "required": True,
                        "options_url": "/realm/placeholder/get_existing_strongholds_json/"
                    }
                    # // The rest of the form (upgrade type, population) will be added
                    # // dynamically with JavaScript.
                ]
            }
        ]

        for action_data in actions_to_create:
            action, created = ActionType.objects.update_or_create(
                action_key=action_data['action_key'],
                defaults={
                    'name': action_data['name'],
                    'description': action_data['description'],
                    'duration': action_data['duration'],
                    'submit_text': action_data['submit_text'],
                    "seasonal_modifications": action_data.get('seasonal_modifications', {}),
                    'inputs': action_data.get('inputs', []),
                }
            )

            # Assign Descriptors
            desc_objs = Descriptor.objects.filter(name__in=action_data['descriptors'])
            action.descriptors.set(desc_objs)

            # Assign Seasons (if empty, it's available in all)
            if action_data['seasons']:
                season_objs = Season.objects.filter(name__in=action_data['seasons'])
                action.available_seasons.set(season_objs)
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created action: {action.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Action '{action.name}' already exists."))
