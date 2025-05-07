from django.core.management.base import BaseCommand
from realms.models import PopulationRace
import random

class Command(BaseCommand):
    help = 'Create predefined PopulationRace entries'

    def handle(self, *args, **kwargs):
        population_races = [
            {"name": "Dwarves"},
            {"name": "Elves"},
            {"name": "Gnomes"},
            {"name": "Goblins"},
            {"name": "Halflings"},
            {"name": "Humans"},
            {"name": "Orcs"},
            {"name": "Undead"},
            # Add more entries as needed
        ]

        for race in population_races:
            # Check if the PopulationRace already exists to avoid duplication
            population_race, created = PopulationRace.objects.get_or_create(
                name=race["name"],
                defaults={}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created PopulationRace: {population_race.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"PopulationRace {population_race.name} already exists"))

        for unit_type in land_unit_types:
            # Check if the LandUnitType already exists to avoid duplication
            land_unit_type, created = LandUnitType.objects.get_or_create(
                name=unit_type["name"],
                defaults={
                    "production": unit_type["production"],
                    "harvest": unit_type["harvest"],
                    "settlement_capacity": unit_type["settlement_capacity"],
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created LandUnitType: {land_unit_type.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"LandUnitType {land_unit_type.name} already exists"))
