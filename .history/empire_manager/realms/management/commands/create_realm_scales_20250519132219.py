from django.core.management.base import BaseCommand
from realms.models import RealmScale

class Command(BaseCommand):
    help = 'Create predefined RealmScale entries'

    def handle(self, *args, **kwargs):
        realm_scales = [
            {"name": "Barony", "description": "A small realm, typically ruled by a baron or baroness.", "pop_unit_size": 10, "land_unit_size": 1, "gold_unit_value": 1000},
            {"name": "Kingdom", "description": "A larger realm, ruled by a king or queen.", "pop_unit_size": 1000, "land_unit_size": 20, "gold_unit_value": 10000},
            {"name": "Empire", "description": "A vast realm, often consisting of multiple kingdoms.", "pop_unit_size": 10000, "land_unit_size": 400, "gold_unit_value": 100000},
            # Add more entries as needed
        ]

        for scale in realm_scales:
            # Check if the PopulationRace already exists to avoid duplication
            realm_scale, created = RealmScale.objects.get_or_create(
                name=scale["name"],
                defaults={"description": scale["description"],
                          "pop_unit_size": scale["pop_unit_size"],
                          "land_unit_size": scale["land_unit_size"],
                          "gold_unit_value": scale["gold_unit_value"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Scale: {realm_scale.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Scale {realm_scale.name} already exists"))