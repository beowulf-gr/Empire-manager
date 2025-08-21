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
                "submit_text": "Start Recruitment"
                "descriptors": ["Limited"], "seasons": [], # All seasons 
                "inputs": [
                    {"name": "target_race", "label": "Target Race:", "type": "select", "required": True, "options_url": "/realm/get_population_races_json/"},
                    {"name": "charisma_modifier", "label": "Charisma Modifier:", "type": "number", "required": True, "default": 0}
                ]
            }
        ]

        for action_data in actions_to_create:
            action, created = ActionType.objects.get_or_create(
                action_key=action_data['action_key'],
                defaults={
                    'name': action_data['name'],
                    'description': action_data['description'],
                    'duration': action_data['duration'],
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
