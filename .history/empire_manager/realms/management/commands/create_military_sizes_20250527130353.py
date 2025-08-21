from django.core.management.base import BaseCommand
from realms.models import MilitaryUnitSize

class Command(BaseCommand):
    help = 'Create predefined MilitaryUnitSize entries'

    def handle(self, *args, **kwargs):
        military_sizes = [
            {"name": "Solo", "gold_cost_upkeep": 1, "food_cost_upkeep": 0},
            {"name": "Tiny", "gold_cost_upkeep": 1, "food_cost_upkeep": 0},
            {"name": "Small", "gold_cost_upkeep": 1, "food_cost_upkeep": 0},
            {"name": "Medium", "gold_cost_upkeep": 1, "food_cost_upkeep": 1},
            {"name": "Large", "gold_cost_upkeep": 1, "food_cost_upkeep": 2},
            {"name": "Huge", "gold_cost_upkeep": 2, "food_cost_upkeep": 4},
            {"name": "Gargantuan", "gold_cost_upkeep": 4, "food_cost_upkeep": 6},
            {"name": "Colossal", "gold_cost_upkeep": 6, "food_cost_upkeep": 8}
        ]

        for size in military_sizes:
            # Check if the MercenaryUnitSize already exists to avoid duplication
            military_unit_size, created = MilitaryUnitSize.objects.get_or_create(
                name=size["name"],
                defaults={"gold_cost_upkeep": size["gold_cost_upkeep"], "food_cost_upkeep": size["food_cost_upkeep"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Mercenary Unit Size: {military_unit_size.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Mercenary Unit Size {military_unit_size.name} already exists"))