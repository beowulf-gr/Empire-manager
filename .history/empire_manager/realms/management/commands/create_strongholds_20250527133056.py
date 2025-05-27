from django.core.management.base import BaseCommand
from realms.models import StrongholdType

class Command(BaseCommand):
    help = 'Create predefined StrongholdType entries'

    def handle(self, *args, **kwargs):
        stronghold_types = [
            {
                "name": "Castle", 
                "description": "The mainstay of defensive fortifications, a castle is a large, heavily built structure designed to fend off attackers and serve as a headquarters for you and your army. Castles are best placed near areas of importance in your domain, such as towns and cities, or at crossroads or other key defensive points. A castle has walls with 100 hit points each for purposes of the siege system.",
                "benefits": "A castle provides a defensive fortification for your realm and increases the total population units that can settle in a place by one.", 
                "duration_seasons": 4, 
                "population_cost": 2, 
                "resource_costs": {"Wood": 8, "Stone": 10}, 
                "gold_cost": 8,
                "population_capacity_bonus": 1
            },
            {
                "name": "City", 
                "description": "Cities are the crown jewels of any nobleman’s holdings. They draw merchants to an area, making it easy to sell finished goods and raw materials while granting access to markets across the world. Cities also cause a tremendous rise in a region's population, as laborers and others move to the city to find work in the markets and industries that spring up in it. Best of all, cities draw artisans to the area who can drive down the cost of converting raw materials into finished items.", 
                "benefits": "A city increases the number of population units you can place in an area by 4", 
                "duration_seasons": 4, 
                "population_cost": 2, 
                "resource_costs": {"Wood": 10, "Stone": 10}, 
                "gold_cost": 10,
                "population_capacity_bonus": 4
            },
            {
                "name": "Keep", 
                "description": "A keep is normally the inner portion of a castle, but for purposes of this system it includes any smaller defensive fortifications. A keep is a good choice to defend areas that are of lesser importance than the main trade routes and production areas of your holdings. These structures can also serve to defend your borders and hold a position until you can raise the funds to build a castle. The keep has 80 hit points for purposes of the siege system.", 
                "benefits": "A keep provides a defensive fortification for your realm and increases the total population units that can settle in a place by one.", 
                "duration_seasons": 2, 
                "population_cost": 1, 
                "resource_costs": {"Wood": 4, "Stone": 5}, 
                "gold_cost": 4,
                "population_capacity_bonus": 1
            },
            {
                "name": "Town", 
                "description": "One step below a city in terms of size and utility, a town is still a good option when your holdings are young and you still have plenty of room for growth. ‘Towns serve as trade centers and as places where you can convert raw materials into finished goods. Multiple towns increase the total wealth of your holdings and help promote trade.", 
                "benefits": "A town increases the number of population units you can place in an area by 2.", 
                "duration_seasons": 2, 
                "population_cost": 1, 
                "resource_costs": {"Wood": 5, "Stone": 5}, 
                "gold_cost": 5,
                "population_capacity_bonus": 2
            },
            {
                "name": "Village", 
                "description": "The smallest settlement you can establish in your domain, a village is a good starting point or centerpiece for wide areas set aside for agriculture, mining, and other tesource gathering activities. Villages act like nodes in your Holding’s nervous system. While they produce little on their own, they are important in building a web of connections and resource collection points to keep your domain running smoothly. If you want for villages, your production efforts become scattershot.", 
                "benefits": "Α village increases the number of population units you can place in an area by 1.", 
                "duration_seasons": 1, 
                "population_cost": 1, 
                "resource_costs": {"Wood": 2, "Stone": 2}, 
                "gold_cost": 2,
                "population_capacity_bonus": 1
            },
            ]

        for stronghold_type in stronghold_types:
            # Check if the StrongholdType already exists to avoid duplication
            stronghold, created = StrongholdType.objects.get_or_create(
                name=stronghold_type["name"],
                defaults={"description": stronghold_type["description"],
                          "benefits": stronghold_type["benefits"],
                          "duration_seasons": stronghold_type["duration_seasons"],
                          "population_cost": stronghold_type["population_cost"],
                          "resource_costs": stronghold_type["resource_costs"],
                          "population_capacity_bonus": stronghold_type["population_capacity_bonus"]}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created Stronghold Type: {stronghold.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Stronghold Type {stronghold.name} already exists"))