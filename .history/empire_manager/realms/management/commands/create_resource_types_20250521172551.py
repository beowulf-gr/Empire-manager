from django.core.management.base import BaseCommand
from realms.models import Resource
import random

class Command(BaseCommand):
    help = 'Create predefined Resource entries'

    def handle(self, *args, **kwargs):
        resources = [
            {"name": "Food", "value": 0.0500, "display": "20 Food units/1 Gold unit"},
            {"name": "Wood", "value": 0.0667, "display": "15 Wood units/1 Gold unit"},
            {"name": "Stone", "value": 0.0833, "display": "12 Stone units/1 Gold unit"},
            {"name": "Adamantine", "value": 3.0000, "display": "1 Adamantine unit/3 Gold units"},
            {"name": "Copper", "value": 0.1000, "display": "10 Copper units/1 Gold unit"},
            {"name": "Gold", "value": 1, "display": "1 Gold unit/1 Gold unit"},
            {"name": "Iron", "value": 0.1000, "display": "10 Iron units/1 Gold unit"},
            {"name": "Mithral", "value": 2.0000, "display": "1 Mithral unit/2 Gold units"},
            {"name": "Silver", "value": 0.2000, "display": "5 Silver units/1 Gold unit"},
        ]

        for resource in resources:
            # Check if the Resource already exists to avoid duplication
            resource_obj, created = Resource.objects.get_or_create(
                name=resource["name"],
                defaults={"value": resource["value"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Resource: {resource_obj.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Resource {resource_obj.name} already exists"))
                resource_obj.value = resource["value"]
                resource_obj.gold_cost_display = res_data["display"]
                resource_obj.save()