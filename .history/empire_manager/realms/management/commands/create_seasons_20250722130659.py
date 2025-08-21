from django.core.management.base import BaseCommand
from realms.models import Season

class Command(BaseCommand):
    help = 'Create predefined Season entries'

    def handle(self, *args, **kwargs):
        seasons = [
            {"name": "Spring", "order": 1},
            {"name": "Summer", "order": 2},
            {"name": "Fall", "order": 3},
            {"name": "Winter", "order": 4}
        ]

        for season in seasons:
            # Check if the MercenaryUnitSize already exists to avoid duplication
            realm_season, created =Season.objects.get_or_create(
                name=season["name"],
                defaults={"order": season["order"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Season: {realm_season.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Season {realm_season.name} already exists"))