from django.core.management.base import BaseCommand
from realms.models import LandUnitType
import random

class Command(BaseCommand):
    help = 'Create predefined LandUnitType entries'

    def handle(self, *args, **kwargs):
        land_unit_types = [
            {"name": "Forest", "production": {"wood": 4, "food": 1}, "choices": [], "harvest": 1, "settlement_capacity": 2},
            {"name": "Hills", "production": {}, "choices": [{"stone": 2}, {"minerals": 1}], "harvest": 3, "settlement_capacity": 1},
            {"name": "Plains", "production": {"food": 4}, "choices": [], "harvest": 1, "settlement_capacity": 4},
            {"name": "Mountains", "production": {}, "choices": [{"stone": 4}, {"minerals": 2}], "harvest": 2, "settlement_capacity": 2},
            {"name": "Ruins", "production": {"gold":random.randint(1, 10)-4}, "choices": [], "harvest": 2, "settlement_capacity": 2},
            {"name": "Wasteland", "production": {}, "choices": [], "harvest": 0, "settlement_capacity": 1},
            {"name": "Swamp", "production": {"gold":1, "food": 1}, "choices": [], "harvest": 2, "settlement_capacity": 1},
            {"name": "Water", "production": {"food":2}, "choices": [], "harvest": 1, "settlement_capacity": 1},
            # Add more entries as needed
        ]

        for unit_type in land_unit_types:
            # Check if the LandUnitType already exists to avoid duplication
            land_unit_type, created = LandUnitType.objects.get_or_create(
                name=unit_type["name"],
                defaults={
                    "production": unit_type["production"],
                    "choices": unit_type["choices"],
                    "harvest": unit_type["harvest"],
                    "settlement_capacity": unit_type["settlement_capacity"],
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created LandUnitType: {land_unit_type.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"LandUnitType {land_unit_type.name} already exists"))
