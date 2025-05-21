from django.core.management.base import BaseCommand
from realms.models import Resource
import random

class Command(BaseCommand):
    help = 'Create predefined PopulationRace entries'

    def handle(self, *args, **kwargs):
        resources = [
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