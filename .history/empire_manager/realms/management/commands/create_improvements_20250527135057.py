from django.core.management.base import BaseCommand
from django.db import transaction
from realms.models import StrongholdImprovementType, StrongholdType

class Command(BaseCommand):
    help = 'Create predefined StrongholdImprovementType entries'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to create stronghold improvement types...'))
        improvement_types_data = [
            {"name": "Craftsmen's Guild", 
             "description": "By erecting a craftsmen’s guild, you can attract skilled workers to settle in your realm. The guild is critical to any attempts to establish large scale production of finished goods in your realm,", 
             "benefits": "Any town with a guild can produce weapons and armor, wooden goods, and exotic items as trade goods", 
             "duration_seasons": 2, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 2}, 
             "gold_cost": 2,
             "gold_upkeep_cost": 0, 
             "prerequisite_stronghold_types" :["Town", "City"]
            },
            {"name": "Grand Temple", 
             "description": "By erecting a monument to the gods, you can hope to curry their favor in managing your realm and protecting it from disaster. A temple draws the gods’ approval and gives you a bonus to ward off random events.", 
             "benefits": "For each grand temple in your domain, you gain a +1 circumstance bonus on all spring and fall random event checks.", 
             "duration_seasons": 4, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 4, "Stone": 4}, 
             "gold_cost": 4,
             "gold_upkeep_cost": 1, 
             "prerequisite_stronghold_types" :["City"]},
            {"name": "Marketplace", 
             "description": "A marketplace draws merchants and other traders to your realm. It makes it easier for you to conduct commerce and is a good expansion option if you do not have access to any waterways on which you can build a port.", 
             "benefits": "marketplace grants you a +2 circumstance bonus to all Knowledge (economics) checks made to buy and sell goods.", 
             "duration_seasons": 2, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 2}, 
             "gold_cost": 2,
             "gold_upkeep_cost": 0, 
             "prerequisite_stronghold_types" :["Town", "City"]
            },
            {"name": "Port", 
             "description": "A port is a harbor that incorporates shipbuilding and other naval industries. When added to a city that borders or stands in a water area, the port can increase trade dramatically and allow you to buy and sell goods at better prices. Most trade is conducted via waterways, as a boat can more easily carry large quantities of goods than an overland caravan.", 
             "benefits": "A port allows you easier access to trade. With a port, you never need worry about gaining access to trade centers. Furthermore, when rolling to determine if you have access to trade good you gain a +2 circumstance bonus to all Knowledge (economics) checks made to buy or sell goods.", 
             "duration_seasons": 2, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 4}, 
             "gold_cost": 2,
             "gold_upkeep_cost": 0, 
             "prerequisite_stronghold_types" :["Town", "City"]
            },
            {"name": "Wall", 
             "description": "A critical defensive measure for any settlement located near wild borderlands or a contested zone between two realms, a wall provides a defensive fortification that can surround a stronghold.", 
             "benefits": "A stronghold with this feature gains an 80 hit point barrier for purposes of the siege system, See chapter two for rules on sieges.", 
             "duration_seasons": 2, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 2, "Stone": 2}, 
             "gold_cost": 1,
             "gold_upkeep_cost": 0, 
             "prerequisite_stronghold_types" :["Town", "City"]
            },
            {"name": "Wizard's Academy", 
             "description": "Many wizards seek out quiet, peaceful homes where they can study the arcane arts in peace. By establishing a wizard’s academy in your domain, you can draw spellcasters who can produce magic items and lend you magical support.", 
             "benefits": "Any city with a wizards’ academy can produce magical items for use in your realm or trade.", 
             "duration_seasons": 2, 
             "population_cost": 1, 
             "resource_costs": {"Wood": 2}, 
             "gold_cost": 4,
             "gold_upkeep_cost": 1, 
             "prerequisite_stronghold_types" :["City"]
            },
            ]
        
        created_count = 0
        for item_data in improvement_types_data:
            # Separate M2M data before calling get_or_create
            prereq_stronghold_names = item_data.pop('prerequisite_stronghold_names', [])
            
            # Prepare the defaults for get_or_create, excluding M2M fields
            # and potentially transforming resource_costs if needed
            defaults_data = {key: value for key, value in item_data.items() if key != 'name'}

            # Example: If resource_costs keys are names and need to be objects:
            # This is a simplified example; you might need more robust error handling
            # or ensure your models.py's JSONField for resource_costs can handle string keys directly.
            # For this example, I'll assume resource_costs as defined in improvement_types_data is fine
            # for direct assignment to the JSONField. If it needs ResourceType instances as keys,
            # you'd process it here before passing to defaults_data.

            improvement_type, created = StrongholdImprovementType.objects.get_or_create(
                name=item_data['name'],
                defaults=defaults_data
            )

            if created:
                # Now, handle the ManyToManyField for prerequisites
                if prereq_stronghold_names:
                    prerequisites_to_set = []
                    for prereq_name in prereq_stronghold_names:
                        try:
                            stronghold_type_obj = StrongholdType.objects.get(name=prereq_name)
                            prerequisites_to_set.append(stronghold_type_obj)
                        except StrongholdType.DoesNotExist:
                            self.stdout.write(self.style.WARNING(
                                f"Prerequisite StrongholdType '{prereq_name}' not found for improvement '{improvement_type.name}'. Skipping this prerequisite."
                            ))
                    
                    if prerequisites_to_set:
                        improvement_type.prerequisite_stronghold_types.set(prerequisites_to_set)
                
                self.stdout.write(self.style.SUCCESS(f"Successfully created StrongholdImprovementType: {improvement_type.name}"))
                created_count += 1
            else:
                # Optionally, update existing instances if needed, including M2M fields
                # For example, if you want to ensure prerequisites are updated even if the object wasn't 'created':
                if prereq_stronghold_names:
                    prerequisites_to_set = []
                    for prereq_name in prereq_stronghold_names:
                        try:
                            stronghold_type_obj = StrongholdType.objects.get(name=prereq_name)
                            prerequisites_to_set.append(stronghold_type_obj)
                        except StrongholdType.DoesNotExist:
                            pass # Already warned if created, or handle differently for updates
                    if prerequisites_to_set or not any(improvement_type.prerequisite_stronghold_types.all()): # Only set if there are new ones or if none were set
                        improvement_type.prerequisite_stronghold_types.set(prerequisites_to_set)


                self.stdout.write(self.style.NOTICE(f"StrongholdImprovementType '{improvement_type.name}' already exists. Checked/updated prerequisites."))


        self.stdout.write(self.style.SUCCESS(f'Finished processing stronghold improvement types. {created_count} created.'))