from django.core.management.base import BaseCommand
from realms.models import MercenaryUnitSize

class Command(BaseCommand):
    help = 'Create predefined MercenaryUnitSize entries'

    def handle(self, *args, **kwargs):
        mercenary_sizes = [
            {"name": "Solo", "gold_cost_recruitment_modifier": 0.125, "food_cost_upkeep": 0},
            {"name": "Tiny", "gold_cost_recruitment_modifier": 0.25, "food_cost_upkeep": 0},
            {"name": "Small", "gold_cost_recruitment_modifier": 0.5, "food_cost_upkeep": 0.5},
            {"name": "Medium", "gold_cost_recruitment_modifier": 1, "food_cost_upkeep": 1},
            {"name": "Large", "gold_cost_recruitment_modifier": 2, "food_cost_upkeep": 2},
            {"name": "Huge", "gold_cost_recruitment_modifier": 4, "food_cost_upkeep": 4},
            {"name": "Gargantuan", "gold_cost_recruitment_modifier": 8, "food_cost_upkeep": 8},
            {"name": "Colossal", "gold_cost_recruitment_modifier": 12, "food_cost_upkeep": 12}
        ]

        for size in mercenary_sizes:
            # Check if the MercenaryUnitSize already exists to avoid duplication
            mercenary_unit_size, created = MercenaryUnitSize.objects.get_or_create(
                name=size["name"],
                defaults={"gold_cost_recruitment_modifier": size["gold_cost_recruitment_modifier"], "food_cost_upkeep": size["food_cost_upkeep"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Mercenary Unit Size: {mercenary_unit_size.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Mercenary Unit Size {mercenary_unit_size.name} already exists"))