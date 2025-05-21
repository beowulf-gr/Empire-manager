from django.core.management.base import BaseCommand
from realms.models import GoodsType, Resource # Import GoodsType and Resource

class Command(BaseCommand):
    help = 'Create predefined GoodsType entries with their costs and durations.'

    def handle(self, *args, **kwargs):
        # IMPORTANT: Ensure your Resource objects (like "Wood", "Silver", "Gold", "Iron")
        # are already created in the database before running this command.
        # You can create them via Django admin or a separate management command.

        goods_types_data = [
            {
                "name": "Exotic Items (Silver)",
                "description": "This category includes everything from porcelain goods to beautifully rendered statues and paintings. Exotic items are generally luxury goods best used to sell for their cash value.", # Updated description for clarity
                "value": 2,
                "duration": 1, # Example duration
                "cost_resource_name": "Silver", # Name of the Resource required
                "cost_quantity": 5 # Example: 5 Silver units (worth 1 Gold if 1 Silver = 0.2 Gold)
            },
            {
                "name": "Exotic Items (Copper)",
                "description": "Luxurious items. Cost: Iron worth 10 Gold.",
                "value": 2,
                "duration": 1,
                "cost_resource_name": "Copper", # Name of the Resource required
                "cost_quantity": 10 # Example: 10 Copper units (worth 1 Gold if 1 Copper = 0.1 Gold)
            },
            {
                "name": "Exotic Items (Gold)",
                "description": "Luxurious items. Cost: Iron worth 10 Gold.",
                "value": 2,
                "duration": 1,
                "cost_resource_name": "Gold", # Name of the Resource required
                "cost_quantity": 1
            },
            {
                "name": "Magic Items (Silver)",
                "description" : "Rare and wondrous to behold, magic item sales can quickly transform your domain into an economic powerhouse. Though expensive and slow to produce, they are worth tremendous amounts of money.",
                "value": 6,
                "duration": 4,
                "cost_resource_name": "Silver",
                "cost_quantity": 20
            },
            {
                "name": "Magic Items (Gold)",
                "description" : "Rare and wondrous to behold, magic item sales can quickly transform your domain into an economic powerhouse. Though expensive and slow to produce, they are worth tremendous amounts of money.",
                "value": 6,
                "duration": 4,
                "cost_resource_name": "Gold",
                "cost_quantity": 4
            },
            {
                "name": "Magic Items (Copper)",
                "description" : "Rare and wondrous to behold, magic item sales can quickly transform your domain into an economic powerhouse. Though expensive and slow to produce, they are worth tremendous amounts of money.",
                "value": 6,
                "duration": 4,
                "cost_resource_name": "Copper",
                "cost_quantity": 40
            },
            {
                "name": "Magic Items (Mithral)",
                "description" : "Rare and wondrous to behold, magic item sales can quickly transform your domain into an economic powerhouse. Though expensive and slow to produce, they are worth tremendous amounts of money.",
                "value": 6,
                "duration": 4,
                "cost_resource_name": "Mithral",
                "cost_quantity": 2
            },
            {
                "name": "Weapons and Armor",
                "description": "In the rough and tumble worlds of fantasy RPGs, there is never a shortage of demandm on stout shields, sharp swords, and tough armor.",
                "value": 1,
                "duration": 1,
                "cost_resource_name": "Iron",
                "cost_quantity": 5
            },
            {
                "name": "Wooden Goods",
                "description": "While cheap and easy to make, wooden goods are an excellent option if your realm produces excess lumber that you need to be rid of. This category includes furniture, wagons, ships, and other items.",
                "value": 1,
                "duration": 1,
                "cost_resource_name": "Wood",
                "cost_quantity": 10
            },
        ]

        self.stdout.write(self.style.HTTP_INFO("--- Populating GoodsType ---"))

        for good_data in goods_types_data:
            cost_resource_obj = None
            if good_data.get("cost_resource_name"):
                try:
                    # Attempt to get the Resource object by name
                    cost_resource_obj = Resource.objects.get(name=good_data["cost_resource_name"])
                except Resource.DoesNotExist:
                    self.stdout.write(self.style.ERROR(
                        f"Resource '{good_data['cost_resource_name']}' not found for GoodsType '{good_data['name']}'. "
                        "This GoodsType will be created without a cost resource."
                    ))
                    # Set to None if resource not found, so cost_resource field remains null
                    cost_resource_obj = None

            goods_type_obj, created = GoodsType.objects.get_or_create(
                name=good_data["name"],
                defaults={
                    "description": good_data["description"],
                    "value": good_data["value"],
                    "duration": good_data["duration"],
                    "cost_resource": cost_resource_obj, # Assign the Resource object
                    "cost_quantity": good_data.get("cost_quantity", 0)
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created GoodsType: {goods_type_obj.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"GoodsType '{goods_type_obj.name}' already exists. Skipping creation."))
                # Optional: update existing fields if 'created' is False and you want to ensure data matches
                # goods_type_obj.description = good_data["description"]
                # goods_type_obj.value = good_data["value"]
                # goods_type_obj.duration = good_data["duration"]
                # goods_type_obj.cost_resource = cost_resource_obj
                # goods_type_obj.cost_quantity = good_data.get("cost_quantity", 0)
                # goods_type_obj.save()

        self.stdout.write(self.style.HTTP_INFO("--- GoodsType Population Complete ---"))