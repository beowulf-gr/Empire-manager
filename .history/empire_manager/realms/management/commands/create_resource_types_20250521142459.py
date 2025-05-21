from django.core.management.base import BaseCommand
from realms.models import Resource
import random

class Command(BaseCommand):
    help = 'Create predefined PopulationRace entries'

    def handle(self, *args, **kwargs):
        resources = [
            {"name": "Food", "value": 0.0500},
            {"name": "Wood", "value": 0.0667},
            {"name": "Stone", "value": 0.0833},
            {"name": "Adamantine", "value": 3.0000},
            {"name": "Copper", "value": 0.1000},
            {"name": "Gold", "value": 1},
            {"name": "Iron", "value": 0.1000},
            {"name": "Mithral", "value": 2.0000},
            {"name": "Silver", "value": 0.2000},
        ]

        for resource in resources:
            # Check if the Resource already exists to avoid duplication
            resource_obj, created = Resource.objects.get_or_create(
                name=resource["name"],
                defaults={"gold_equivalent": resource["gold_equivalent"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Resource: {resource_obj.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Resource {resource_obj.name} already exists"))