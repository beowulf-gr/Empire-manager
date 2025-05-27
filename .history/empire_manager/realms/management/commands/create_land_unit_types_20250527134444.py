from django.core.management.base import BaseCommand
from realms.models import LandUnitType
import random

class Command(BaseCommand):
    help = 'Create predefined LandUnitType entries'

    def handle(self, *args, **kwargs):
        land_unit_types = [
            {"name": "Forest", "production": {"Wood": 4, "Food": 1}, "harvest": 1, "base_population_capacity": 2},
            {"name": "Hills - Stone", "production": {"Stone": 2}, "harvest": 3, "base_population_capacity": 1},
            {"name": "Hills - Minerals", "production": {"minerals": 1}, "harvest": 3, "base_population_capacity": 1},
            {"name": "Plains", "production": {"Food": 4}, "harvest": 1, "base_population_capacity": 4},
            {"name": "Mountains - Stone", "production": {"Stone": 4}, "harvest": 2, "base_population_capacity": 2},
            {"name": "Mountains - Minerals", "production": {"minerals": 2}, "harvest": 2, "base_population_capacity": 2},
            {"name": "Ruins", "production": {"Gold":random.randint(1, 10)-4}, "harvest": 2, "base_population_capacity": 2},
            {"name": "Wasteland", "production": {}, "harvest": 0, "base_population_capacity": 1},
            {"name": "Swamp", "production": {"Gold":1, "Food": 1}, "harvest": 2, "base_population_capacity": 1},
            {"name": "Water", "production": {"Food":2}, "harvest": 1, "base_population_capacity": 1},
        ]

        for unit_type in land_unit_types:
            # Check if the LandUnitType already exists to avoid duplication
            land_unit_type, created = LandUnitType.objects.get_or_create(
                name=unit_type["name"],
                defaults={
                    "production": unit_type["production"],
                    "harvest": unit_type["harvest"],
                    "base_population_capacity": unit_type["base_population_capacity"],
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created LandUnitType: {land_unit_type.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"LandUnitType {land_unit_type.name} already exists"))
