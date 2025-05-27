from django.core.management.base import BaseCommand
from realms.models import StrongholdType

class Command(BaseCommand):
    help = 'Create predefined StrongholdType entries'

    def handle(self, *args, **kwargs):
        stronghold_types = [
            {
                "name": "Castle", 
                "description": "The mainstay of defensive fortifications, a castle is a large, heavily built structure designed to fend off attackers and serve as a headquarters for you and your army. Castles are best placed near areas of importance in your domain, such as towns and cities, or at crossroads or other key defensive points. A castle has walls with 100 hit points each for purposes of the siege system.",
                "benefits": "A castle provides a defensive fortification for your realm and increases the total population units that can settle in a place by one.", 
                "duration_seasons": 4, 
                "population_cost": 2, 
                "resource_costs": {"Wood": 8, "Stone": 10}, 
                "gold_cost": 8,
                "population_capacity_bonus": 1
            },
            {
                "name": "City", 
                "description": "A fortified structure, typically the residence of a lord or noble.", 
                "benefits": "", 
                "duration_seasons": 1, 
                "population_cost": 1, 
                "resource_costs": {"Wood": 4, "Food": 1}, 
                "gold_cost": 8,
                "population_capacity_bonus": 1
            },
            {
                "name": "Keep", 
                "description": "A fortified structure, typically the residence of a lord or noble.", 
                "benefits": "", 
                "duration_seasons": 1, 
                "population_cost": 1, 
                "resource_costs": {"Wood": 4, "Food": 1}, 
                "gold_cost": 8,
                "population_capacity_bonus": 1
            },
            {
                "name": "Town", 
                "description": "A fortified structure, typically the residence of a lord or noble.", 
                "benefits": "", 
                "duration_seasons": 1, 
                "population_cost": 1, 
                "resource_costs": {"Wood": 4, "Food": 1}, 
                "gold_cost": 8,
                "population_capacity_bonus": 1
            },
            {
                "name": "Village", 
                "description": "A fortified structure, typically the residence of a lord or noble.", 
                "benefits": "", 
                "duration_seasons": 1, 
                "population_cost": 1, 
                "resource_costs": {"Wood": 4, "Food": 1}, 
                "gold_cost": 8,
                "population_capacity_bonus": 1
            },
            ]

        for stronghold_type in stronghold_types:
            # Check if the StrongholdType already exists to avoid duplication
            stronghold, created = StrongholdType.objects.get_or_create(
                name=stronghold_type["name"],
                defaults={"description": stronghold_type["description"],
                          "benefits": stronghold_type["benefits"],
                          "duration_seasons": stronghold_type["duration_seasons"],
                          "population_cost": stronghold_type["population_cost"],
                          "resource_costs": stronghold_type["resource_costs"],
                          "population_capacity_bonus": stronghold_type["population_capacity_bonus"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Stronghold Type: {stronghold.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Stronghold Type {stronghold.name} already exists"))