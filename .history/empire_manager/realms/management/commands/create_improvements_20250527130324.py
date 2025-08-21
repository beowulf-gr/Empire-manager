from django.core.management.base import BaseCommand
from realms.models import StrongholdImprovementType

class Command(BaseCommand):
    help = 'Create predefined StrongholdImprovementType entries'

    def handle(self, *args, **kwargs):
        improvement_types = [
            {"name": "Castle", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": "", "population_capacity_bonus": 1},
            {"name": "Castle", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": "", "population_capacity_bonus": 1},
            {"name": "Castle", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": "", "population_capacity_bonus": 1},
            {"name": "Castle", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": "", "population_capacity_bonus": 1},
            {"name": "Castle", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": "", "population_capacity_bonus": 1},
            {"name": "Castle", "description": "A fortified structure, typically the residence of a lord or noble.", "benefits": "", "duration_seasons": 1, "population_cost": 1, "resource_costs": "", "population_capacity_bonus": 1},
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
                          "population_capacity_bonus": improvement_type["population_capacity_bonus"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Stronghold Type: {improvement.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Stronghold Type {improvement.name} already exists"))