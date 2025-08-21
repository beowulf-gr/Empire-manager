from django.core.management.base import BaseCommand
from realms.models import StrongholdImprovementType

class Command(BaseCommand):
    help = 'Create predefined StrongholdImprovementType entries'

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
        for data in improvement_types_data:
            prereq_names = data.pop('prerequisite_stronghold_names', []) # Get and remove prereq names

            # Ensure resource_costs keys are valid ResourceType names or handle as needed
            # For simplicity, assuming keys in resource_costs are names of existing ResourceTypes
            # You might want to fetch ResourceType objects based on these names for robustness.
            
            improvement_type, created = StrongholdImprovementType.objects.get_or_create(
                name=data['name'],
                defaults=data # All other fields
            )

            if created:
                # Fetch prerequisite StrongholdType objects
                prerequisites = []
                if prereq_names:
                    for prereq_name in prereq_names:
                        try:
                            stronghold_type = StrongholdType.objects.get(name=prereq_name)
                            prerequisites.append(stronghold_type)
                        except StrongholdType.DoesNotExist:
                            self.stdout.write(self.style.WARNING(
                                f"Prerequisite StrongholdType '{prereq_name}' not found for improvement '{improvement_type.name}'. Skipping this prerequisite."
                            ))
                
                # Set the ManyToMany relationship
                if prerequisites:
                    improvement_type.prerequisite_stronghold_types.set(prerequisites)
                
                # If you also have prerequisite_other_improvements (ManyToManyField to 'self'):
                # prereq_improvement_names = data.pop('prerequisite_other_improvement_names', [])
                # if prereq_improvement_names:
                #     other_prereqs = StrongholdImprovementType.objects.filter(name__in=prereq_improvement_names)
                #     improvement_type.prerequisite_other_improvements.set(other_prereqs)

                self.stdout.write(self.style.SUCCESS(f"Successfully created StrongholdImprovementType: {improvement_type.name}"))
                created_count += 1
            else:
                self.stdout.write(self.style.NOTICE(f"StrongholdImprovementType '{improvement_type.name}' already exists."))

        self.stdout.write(self.style.SUCCESS(f'Finished creating stronghold improvement types. {created_count} created.'))

        for improvement_type in improvement_types:
            # Check if the StrongholdType already exists to avoid duplication
            improvement, created = StrongholdImprovementType.objects.get_or_create(
                name=improvement_type["name"],
                defaults={"description": improvement_type["description"],
                          "benefits": improvement_type["benefits"],
                          "duration_seasons": improvement_type["duration_seasons"],
                          "population_cost": improvement_type["population_cost"],
                          "resource_costs": improvement_type["resource_costs"],
                          "gold_cost": improvement_type["gold_cost"],
                          "gold_upkeep_cost": improvement_type["gold_upkeep_cost"],
                          "prerequisite_stronghold_types": improvement_type["prerequisite_stronghold_types"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Improvement Type: {improvement.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Improvement Type {improvement.name} already exists"))