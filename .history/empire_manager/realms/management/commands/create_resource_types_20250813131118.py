from django.core.management.base import BaseCommand
from realms.models import Resource
import random

class Command(BaseCommand):
    help = 'Create predefined Resource entries'

    def handle(self, *args, **kwargs):
        resources = [
            {"name": "Food", "value": 0.0500, "gold_cost_display": "20 Food units/1 Gold unit"},
            {"name": "Wood", "value": 0.0667, "gold_cost_display": "15 Wood units/1 Gold unit"},
            {"name": "Stone", "value": 0.0833, "gold_cost_display": "12 Stone units/1 Gold unit"},
            {"name": "Adamantine", "value": 3.0000, "gold_cost_display": "1 Adamantine unit/3 Gold units", "category": "Minerals"},
            {"name": "Copper", "value": 0.1000, "gold_cost_display": "10 Copper units/1 Gold unit", "category": "Minerals"},
            {"name": "Gold", "value": 1, "gold_cost_display": "1 Gold unit/1 Gold unit", "category": "Minerals"},
            {"name": "Iron", "value": 0.1000, "gold_cost_display": "10 Iron units/1 Gold unit", "category": "Minerals"},
            {"name": "Mithral", "value": 2.0000, "gold_cost_display": "1 Mithral unit/2 Gold units", "category": "Minerals"},
            {"name": "Silver", "value": 0.2000, "gold_cost_display": "5 Silver units/1 Gold unit", "category": "Minerals"},
        ]

        for resource in resources:
            Resource.objects.update_or_create(
                name=resource["name"],
                defaults={
                    "value": resource["value"],
                    "gold_cost_display": resource["gold_cost_display"],
                    "category": resource.get("category", "")
                }
            )
            self.stdout.write(self.style.SUCCESS(f"Created/Updated Resource: {resource['name']}"))
