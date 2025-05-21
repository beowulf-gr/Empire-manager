from django.core.management.base import BaseCommand
from realms.models import GoodsType
import random

class Command(BaseCommand):
    help = 'Create predefined PopulationRace entries'

    def handle(self, *args, **kwargs):
        goods = [
            {"name": "Exotic Items", "description": "This category includes everything from porcelain goods to beautifully rendered statues and paintings. Exotic items are generally luxury goods best used to sell for their cash value." "value": 2},
            {"name": "Magic Items", "description" : "Rare and wondrous to behold, magic item sales can quickly transform your domain into an economic powerhouse. Though expensive and slow to produce, they are worth tremendous amounts of money." "value": 6},
            {"name": "Weapons and Armor", "description": "In the rough and tumble worlds of fantasy RPGs, there is never a shortage of demandm on stout shields, sharp swords, and tough armor." "value": 1},
            {"name": "Wooden Goods", "description": "While cheap and easy to make, wooden goods are an excellent option if your realm produces excess lumber that you need to be rid of. This category includes furniture, wagons, ships, and other items." "value": 1},
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