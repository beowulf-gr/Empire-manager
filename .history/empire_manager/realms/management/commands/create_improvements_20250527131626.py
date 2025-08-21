from django.core.management.base import BaseCommand
from realms.models import StrongholdImprovementType

class Command(BaseCommand):
    help = 'Create predefined StrongholdImprovementType entries'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to create stronghold improvement types...'))
        improvement_types = [
            {"name": "Craftsmen's Guild", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": {"Wood": 4, "Food": 1}, "gold_upkeep_cost": 1, "prerequisite_stronghold_types" :["Town", "City"]},
            {"name": "Grand Temple", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": {"Wood": 4, "Food": 1}, "gold_upkeep_cost": 1, "prerequisite_stronghold_types" :["City"]},
            {"name": "Marketplace", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": {"Wood": 4, "Food": 1}, "gold_upkeep_cost": 1, "prerequisite_stronghold_types" :["Town", "City"]},
            {"name": "Port", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": {"Wood": 4, "Food": 1}, "gold_upkeep_cost": 1, "prerequisite_stronghold_types" :["Town", "City"]},
            {"name": "Wall", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": {"Wood": 4, "Food": 1}, "gold_upkeep_cost": 1, "prerequisite_stronghold_types" :["Town", "City"]},
            {"name": "Wizard's Academy", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": {"Wood": 4, "Food": 1}, "gold_upkeep_cost": 1, "prerequisite_stronghold_types" :["City"]},
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
                          "gold_upkeep_cost": improvement_type["gold_upkeep_cost"],
                          "prerequisite_stronghold_types": improvement_type["prerequisite_stronghold_types"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Improvement Type: {improvement.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Improvement Type {improvement.name} already exists"))