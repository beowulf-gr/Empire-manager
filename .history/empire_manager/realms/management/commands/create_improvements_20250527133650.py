from django.core.management.base import BaseCommand
from realms.models import StrongholdImprovementType

class Command(BaseCommand):
    help = 'Create predefined StrongholdImprovementType entries'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to create stronghold improvement types...'))
        improvement_types = [
            {"name": "Craftsmen's Guild", 
             "description": "By erecting a craftsmen’s guild, you can attract skilled workers to settle in your realm. The guild is critical to any attempts to establish large scale production of finished goods in your realm,", 
             "benefits": "Any town with a guild can produce weapons and armor, wooden goods, and exotic items as trade goods", 
             "duration_seasons": 2, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 2}, 
             "gold_cost": 2,
             "gold_upkeep_cost": 0, 
             "prerequisite_stronghold_types" :["Town", "City"]
            },
            {"name": "Grand Temple", 
             "description": "By erecting a monument to the gods, you can hope to curry their favor in managing your realm and protecting it from disaster. A temple draws the gods’ approval and gives you a bonus to ward off random events.", 
             "benefits": "For each grand temple in your domain, you gain a +1 circumstance bonus on all spring and fall random event checks.", 
             "duration_seasons": 4, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 4, "Stone": 4}, 
             "gold_cost": 4,
             "gold_upkeep_cost": 1, 
             "prerequisite_stronghold_types" :["City"]},
            {"name": "Marketplace", 
             "description": "A marketplace draws merchants and other traders to your realm. It makes it easier for you to conduct commerce and is a good expansion option if you do not have access to any waterways on which you can build a port.", 
             "benefits": "marketplace grants you a +2 circumstance bonus to all Knowledge (economics) checks made to buy and sell goods.", 
             "duration_seasons": 2, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 2}, 
             "gold_cost": 2,
             "gold_upkeep_cost": 0, 
             "prerequisite_stronghold_types" :["Town", "City"]
            },
            {"name": "Port", 
             "description": "A fortified structure, typically the residence of a lord or noble.", 
             "benefits": "", 
             "duration_seasons": 1, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 4, "Food": 1}, 
             "gold_cost": 2,
             "gold_upkeep_cost": 1, 
             "prerequisite_stronghold_types" :["Town", "City"]
            },
            {"name": "Wall", 
             "description": "A fortified structure, typically the residence of a lord or noble.", 
             "benefits": "", 
             "duration_seasons": 1, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 4, "Food": 1}, 
             "gold_cost": 2,
             "gold_upkeep_cost": 1, 
             "prerequisite_stronghold_types" :["Town", "City"]
            },
            {"name": "Wizard's Academy", 
             "description": "A fortified structure, typically the residence of a lord or noble.", 
             "benefits": "", 
             "duration_seasons": 1, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 4, "Food": 1}, 
             "gold_cost": 2,
             "gold_upkeep_cost": 1, 
             "prerequisite_stronghold_types" :["City"]
            },
            ]

        for improvement_type in improvement_types:
            # Check if the StrongholdType already exists to avoid duplication
            improvement, created = StrongholdImprovementType.objects.get_or_create(
                name=improvement_type["name"],
                defaults={"description": improvement_type["description"],
                          "benefits": improvement_type["benefits"],
                          "duration_seasons": improvement_type["duration_seasons"],
                          "population_cost": improvement_type["population_cost"],
                          "resource_costs": improvement_type["resource_costs"],
                          "gold_cost": improvement_type["gold_cost"],
                          "gold_upkeep_cost": improvement_type["gold_upkeep_cost"],
                          "prerequisite_stronghold_types": improvement_type["prerequisite_stronghold_types"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Improvement Type: {improvement.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Improvement Type {improvement.name} already exists"))