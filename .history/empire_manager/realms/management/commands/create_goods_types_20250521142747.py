from django.core.management.base import BaseCommand
from realms.models import GoodsType
import random

class Command(BaseCommand):
    help = 'Create predefined PopulationRace entries'

    def handle(self, *args, **kwargs):
        goods = [
            {"name": "Exotic Items", "description": "" "value": 2},
            {"name": "Magic Items", "value": 6},
            {"name": "Weapons and Armor", "value": 1},
            {"name": "Wooden Goods", "value": 1},
        ]

        for good in goods:
            # Check if the Resource already exists to avoid duplication
            resource_obj, created = GoodsType.objects.get_or_create(
                name=good["name"],
                defaults={"value": good["value"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Resource: {resource_obj.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Resource {resource_obj.name} already exists"))