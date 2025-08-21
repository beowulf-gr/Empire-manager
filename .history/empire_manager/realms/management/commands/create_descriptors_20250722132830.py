from django.core.management.base import BaseCommand
from realms.models import Descriptor

class Command(BaseCommand):
    help = 'Create predefined Descriptor entries'

    def handle(self, *args, **kwargs):
        descriptors = [
            {"name": "Contruction", "description": "Actions related to building and infrastructure."},
            {"name": "Limited", "description": "This action can only be taken once per season."},
            {"name": "Obligatory", "description": "This action must be taken at least once every season it is available."},
            {"name": "Political", "description": "Actions related to politics and diplomacy."},
        ]

        for descriptor in descriptors:
            # Check if the MercenaryUnitSize already exists to avoid duplication
            action_descriptor, created =Descriptor.objects.get_or_create(
                name=descriptor["name"],
                defaults={"description": descriptor["description"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Descriptor: {action_descriptor.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Descriptor {action_descriptor.name} already exists"))