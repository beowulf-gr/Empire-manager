# In create_goods_types.py
from django.core.management.base import BaseCommand
from realms.models import GoodsType, Resource 

class Command(BaseCommand):
    help = 'Create predefined GoodsType entries with their new cost structure.'

    def handle(self, *args, **kwargs):
        try:
            iron_resource = Resource.objects.get(name="Iron")
        except Resource.DoesNotExist:
            self.stdout.write(self.style.ERROR("The 'Iron' resource does not exist. Please create it before running this command."))
            return
        try:
            wood_resource = Resource.objects.get(name="Wood")
        except Resource.DoesNotExist:
            self.stdout.write(self.style.ERROR("The 'Wood' resource does not exist. Please create it before running this command."))
            return
        
        goods_types_data = [
            {
                "name": "Exotic Goods",
                "description": "This category includes everything from porcelain goods to beautifully rendered statues and paintings.",
                "value": 2, "duration": 1,
                "cost_in_gold": 1.00, # Cost 1 GP worth of minerals
                "required_resource_category": "Minerals"
            },
            {
                "name": "Magic Items",
                "description": "Rare and wondrous to behold, magic item sales can quickly transform your domain.",
                "value": 6, "duration": 4,
                "cost_in_gold": 4.00, # Cost 4 GP worth of minerals
                "required_resource_category": "Minerals"
            },
            {
                "name": "Weapons and Armor",
                "description": "There is never a shortage of demand for stout shields, sharp swords, and tough armor.",
                "value": 1, "duration": 1,
                "cost_in_gold": 0.50, # Costs 0.5 GP worth of Iron
                "required_resource_category": None,
                "required_resource_specific": iron_resource
            },
            {
                "name": "Wooden Goods",
                "description": "An excellent option if your realm produces excess lumber. This category includes furniture, wagons, ships, and other items.",
                "value": 1, "duration": 1,
                "cost_in_gold": 0.67, # Costs 0.67 GP worth of Wood
                "required_resource_category": None,
                "required_resource_specific": wood_resource
            },
        ]

        for good_data in goods_types_data:
            GoodsType.objects.update_or_create(
                name=good_data["name"],
                defaults={
                    "description": good_data["description"],
                    "value": good_data["value"],
                    "duration": good_data["duration"],
                    "cost_in_gold": good_data["cost_in_gold"],
                    "required_resource_category": good_data.get("required_resource_category"),
                    "required_resource_specific": good_data.get("required_resource_specific")
                }
            )
            self.stdout.write(self.style.SUCCESS(f"Created/Updated GoodsType: {good_data['name']}"))