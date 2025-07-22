from django.db import models
from django.contrib.postgres.fields import JSONField
import random
from decimal import Decimal

MINERAL_SUBTYPES = [
    ("Adamantine", 3),
    ("Copper", 17),
    ("Gold", 7),
    ("Iron", 60),
    ("Mithral", 3),
    ("Silver", 10)
]
class RealmScale(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(default="")
    pop_unit_size = models.IntegerField(default=1)
    land_unit_size = models.IntegerField(default=1)
    gold_unit_value = models.IntegerField(default=1)
    military_unit_size = models.IntegerField(default=1)

    def __str__(self):
        return self.name
    
class Resource(models.Model):
    name = models.CharField(max_length=50, unique=True) # e.g., "Food", "Wood", "Gold", "Iron"
    value = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000) # Base value of the resource
    gold_cost_display = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

# --- NEW MODEL: RealmResource (the "through" model for ManyToMany) ---
class RealmResource(models.Model):
    realm = models.ForeignKey('Realm', on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0) # The amount of this resource for this specific realm

    class Meta:
        unique_together = ('realm', 'resource') # A realm can only have one entry per resource type

    def __str__(self):
        return f"{self.realm.name} - {self.resource.name}: {self.quantity}"
    
class GoodsType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(default="")
    value = models.IntegerField(default=1)

    # Cost definition
    cost_resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='goods_costing_this_resource',
        null=True
    )
    cost_quantity = models.IntegerField(default=0) # How much of cost_resource is needed
    
    duration = models.IntegerField(default=1) # Duration in seasons to produce

    def __str__(self):
        return self.name
    
# --- NEW MODEL: RealmGoodsType (the "through" model for ManyToMany) ---
class RealmGoodsType(models.Model):
    realm = models.ForeignKey('Realm', on_delete=models.CASCADE)
    goods_type = models.ForeignKey(GoodsType, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0) # The amount of this specific good for this realm

    class Meta:
        unique_together = ('realm', 'goods_type') # A realm can only have one entry per goods type

    def __str__(self):
        return f"{self.realm.name} - {self.goods_type.name}: {self.quantity}"
    
class Realm(models.Model):
    name = models.CharField(max_length=100, unique=True)
    ruler = models.CharField(max_length=100)
    scale = models.ForeignKey(RealmScale, on_delete=models.CASCADE, null=True, blank=True)
    treasury = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    debt = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    #resources = models.JSONField(default=dict)
    season = models.CharField(max_length=10, default="Spring")
    year = models.IntegerField(default=1)
    resources = models.ManyToManyField(Resource, through='RealmResource', related_name='realms_with_resource')
    goods = models.ManyToManyField(GoodsType, through='RealmGoodsType', related_name='realms_with_goods')
    loyalty_population = models.IntegerField(default=0)
    loyalty_military = models.IntegerField(default=0)
    loyalty_mercenaries = models.IntegerField(default=0)

    @property
    def total_living_space(self):
        """
        Calculates the sum of total_population_capacity for all land units in this realm.
        """
        total_space = 0
        # self.land_units is the reverse manager from LandUnit.realm
        # Ensure LandUnit has the 'total_population_capacity' property defined.
        # Using .all() is good practice if you might prefetch or filter later,
        # but direct iteration also works.
        for land_unit_instance in self.land_units.all():
            total_space += land_unit_instance.total_population_capacity
        return total_space
    
    @property
    def yearly_gold_costs(self):
        """
        Calculates the total gold upkeep costs per season/turn for the realm.
        This includes mercenary units, military units, and stronghold improvements.
        """
        total_gold_upkeep = Decimal('0.00')

        # Mercenary upkeep
        for mercenary_unit in self.mercenary_units.all(): # mercenary_units is the related_name
            total_gold_upkeep += mercenary_unit.calculated_gold_cost_upkeep

        # Military unit upkeep
        for military_unit in self.military_units.all(): # military_units is the related_name
            total_gold_upkeep += Decimal(military_unit.calculated_gold_cost_upkeep)
        
        # Stronghold improvements upkeep
        for stronghold_instance in self.strongholds.all(): # strongholds is the related_name
            for improvement_instance in stronghold_instance.improvements.all(): # improvements is the related_name
                if improvement_instance.improvement_type:
                    total_gold_upkeep += Decimal(improvement_instance.improvement_type.gold_upkeep_cost)
                    
        return total_gold_upkeep.quantize(Decimal('0.01'))

    @property
    def yearly_food_costs(self):
        """
        Calculates the total food upkeep costs per season/turn for the realm.
        This includes mercenary units and military units.
        """
        total_food_upkeep = Decimal('0.00')

        # Mercenary upkeep
        for mercenary_unit in self.mercenary_units.all(): # mercenary_units is the related_name
            total_food_upkeep += mercenary_unit.total_food_cost_upkeep
            
        # Military unit upkeep
        for military_unit in self.military_units.all(): # military_units is the related_name
            if military_unit.unit_type:
                total_food_upkeep += Decimal(military_unit.unit_type.base_food_cost_upkeep * military_unit.quantity)

        return total_food_upkeep.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


    def __str__(self):
        return self.name

    def get_resource_quantity(self, resource_name):
        """Helper to get a resource quantity by name."""
        try:
            return self.realmresource_set.get(resource__name=resource_name).quantity
        except RealmResource.DoesNotExist:
            return 0

    def update_resource_quantity(self, resource_name, amount):
        """Helper to update a resource quantity."""
        resource_obj, created = Resource.objects.get_or_create(name=resource_name)
        realm_resource, created = RealmResource.objects.get_or_create(
            realm=self,
            resource=resource_obj,
            defaults={'quantity': 0}
        )
        realm_resource.quantity += amount
        realm_resource.save()

    def get_goods_quantity(self, goods_name):
        """Helper to get a goods quantity by name."""
        try:
            return self.realmgoodstype_set.get(goods_type__name=goods_name).quantity
        except RealmGoodsType.DoesNotExist:
            return 0

    def update_goods_quantity(self, goods_name, amount):
        """Helper to update a goods quantity."""
        goods_type_obj, created = GoodsType.objects.get_or_create(name=goods_name)
        realm_goods, created = RealmGoodsType.objects.get_or_create(
            realm=self,
            goods_type=goods_type_obj,
            defaults={'quantity': 0}
        )
        realm_goods.quantity += amount
        realm_goods.save()

    def next_season(self):
        seasons = ["Spring", "Summer", "Autumn", "Winter"]
        current_index = seasons.index(self.season)
        next_index = (current_index + 1) % 4
        self.season = seasons[next_index]
        if self.season == "Spring":
            self.year += 1
        self.save()

    def get_ongoing_actions(self):
        return self.ongoingaction_set.all()

    def __str__(self):
        return self.name
    
class OngoingAction(models.Model):
    realm = models.ForeignKey(Realm, on_delete=models.CASCADE)
    action_name = models.CharField(max_length=100)  # e.g., "construct_farm", "train_units"
    start_season = models.CharField(max_length=10)
    start_year = models.IntegerField()
    duration = models.IntegerField(default=1)  # Duration in seasons
    completed = models.BooleanField(default=False)
    # You might want to store additional action-specific data here as JSON
    data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.action_name} for {self.realm.name} (Started {self.start_season} Year {self.start_year})"

    def is_completed(self, current_season, current_year):
        seasons = ["Spring", "Summer", "Autumn", "Winter"]
        start_index = seasons.index(self.start_season)
        current_index = seasons.index(current_season)

        elapsed_years = current_year - self.start_year
        elapsed_seasons = elapsed_years * 4 + (current_index - start_index)

        return elapsed_seasons >= self.duration
    
class LandUnitType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    production = models.JSONField(default=dict)
    harvest = models.IntegerField(default=1)
    base_population_capacity = models.IntegerField(default=1)

    def __str__(self):
        return self.name
    
class PopulationRace(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class LandUnit(models.Model):
    name = models.CharField(max_length=100)
    unit_type = models.ForeignKey(LandUnitType, on_delete=models.CASCADE)
    assigned_population = models.ManyToManyField('PopulationUnit', blank=True, related_name='located_in_land_units')
    upgrades = models.JSONField(default=list)
    mineral_type = models.CharField(max_length=50, null=True, blank=True)
    has_roads = models.BooleanField(default=False)
    has_mine = models.BooleanField(default=False)

    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='land_units')

    @property
    def total_population_capacity(self):
        """
        Calculates the total population capacity for this land unit.
        It's the land unit type's base capacity, plus stronghold bonus (if any),
        plus any specific land unit modifiers (if defined).
        """
        if not self.unit_type: # Should have a unit_type
            return 0
            
        capacity = self.unit_type.base_population_capacity
        
        # Add stronghold bonus if a stronghold exists on this land unit
        try:
            # self.stronghold is the reverse accessor from StrongholdInstance.land_unit
            if hasattr(self, 'stronghold') and self.stronghold: 
                capacity += self.stronghold.stronghold_type.population_capacity_bonus
        except models.ObjectDoesNotExist: # More specific: StrongholdInstance.DoesNotExist
            # This handles the case where the related stronghold might not exist or is None
            pass
        
        return int(capacity)

    def _assign_mineral_type(self):
        roll = random.randint(1, 100)
        total = 0
        for mineral, chance in MINERAL_SUBTYPES:
            total += chance
            if roll <= total:
                return mineral
        return "Iron"

    def __str__(self):
        return f"{self.name} ({self.unit_type})"

class PopulationUnit(models.Model):
    race = models.ForeignKey(PopulationRace, on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(LandUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='pop_units')
    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='population_units')

    def __str__(self):
        return f"{self.race} (assigned to: {self.assigned_to.name if self.assigned_to else 'None'})"

class StrongholdType(models.Model):
    """
    Defines types of strongholds (e.g., Village, Town, City, Castle).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    
    # New Cost Structure
    duration_seasons = models.PositiveIntegerField(default=1, help_text="Number of seasons (turns) it takes to build.")
    population_cost = models.PositiveIntegerField(default=1, help_text="Population units required for construction.")
    resource_costs = models.JSONField(default=dict, help_text="JSON dictionary of resource costs, e.g., {'Wood': 50, 'Stone': 20}")
    gold_cost = models.PositiveIntegerField(default=0, help_text="Gold cost for construction.")
    
    population_capacity_bonus = models.IntegerField(default=0, help_text="Bonus to population capacity.")

    def __str__(self):
        return self.name

class StrongholdInstance(models.Model):
    """
    An instance of a stronghold built on a specific LandUnit.
    """
    land_unit = models.OneToOneField(LandUnit, on_delete=models.CASCADE, related_name='stronghold')
    stronghold_type = models.ForeignKey(StrongholdType, on_delete=models.PROTECT)
    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='strongholds')
    name = models.CharField(max_length=100, blank=True, help_text="Custom name for this stronghold, defaults to type name.")
    # current_hp = models.PositiveIntegerField(default=100) # If strongholds can be damaged

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.stronghold_type.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.stronghold_type.name}) in {self.land_unit.name or 'Unnamed Land'}"

class StrongholdImprovementType(models.Model):
    """
    Defines types of improvements that can be built within a stronghold.
    e.g., Marketplace, Barracks, Temple, Walls.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    benefits = models.JSONField(default=dict, help_text="JSON dictionary of benefits, e.g., {'trade_income_modifier': 0.1, 'unit_training_speed': -0.1}")
    
    # New Cost Structure
    duration_seasons = models.PositiveIntegerField(default=1, help_text="Number of seasons (turns) it takes to build/upgrade.")
    population_cost = models.PositiveIntegerField(default=1, help_text="Population units required for construction/upgrade.")
    resource_costs = models.JSONField(default=dict, help_text="JSON dictionary of resource costs, e.g., {'Wood': 20, 'Iron': 10, 'Gold': 50}")
    gold_cost = models.PositiveIntegerField(default=0, help_text="Gold cost for construction.")
    gold_upkeep_cost = models.PositiveIntegerField(default=0, help_text="Gold upkeep cost per year after construction.")

    # Prerequisites
    prerequisite_stronghold_types = models.ManyToManyField(StrongholdType, blank=True, help_text="Stronghold types required to build this improvement.")

    def __str__(self):
        return self.name

class StrongholdImprovementInstance(models.Model):
    """
    An instance of an improvement built within a specific StrongholdInstance.
    """
    stronghold_instance = models.ForeignKey(StrongholdInstance, on_delete=models.CASCADE, related_name='improvements')
    improvement_type = models.ForeignKey(StrongholdImprovementType, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('stronghold_instance', 'improvement_type') # Usually one of each type per stronghold, unless levels are handled differently

    def __str__(self):
        return f"{self.improvement_type.name} (Lvl {self.level}) in {self.stronghold_instance.name}"
    
class MercenaryUnitSize(models.Model):
    """
    Defines the size category for mercenary units, affecting costs and individual counts.
    e.g., Solo, Tiny, Small, Medium.
    """
    name = models.CharField(max_length=50, unique=True)
    # Modifier for gold recruitment cost. e.g., 0.125 for Solo (1/8), 0.25 for Tiny (1/4)
    gold_cost_recruitment_modifier = models.DecimalField(max_digits=5, decimal_places=3, default=1.0)
    # Direct food upkeep cost per unit of this size category per turn/season.
    food_cost_upkeep = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    # Number of individuals this size represents.

    def __str__(self):
        return self.name

class RealmMercenaryUnit(models.Model):
    """
    An instance of a mercenary unit currently hired by a realm.
    """
    race = models.ForeignKey(PopulationRace, on_delete=models.SET_NULL, null=True, blank=True)
    mercenary_size = models.ForeignKey(MercenaryUnitSize, on_delete=models.PROTECT, related_name="unit_types")
    challenge_rating = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="A measure of the unit's overall combat effectiveness. Can be fractional (e.g., 0.5 for CR 1/2).")
    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='mercenary_units')

    @property
    def calculated_gold_cost_upkeep(self):
        """Calculates gold cost for recruitment based on CR and size modifier."""
        if self.mercenary_size:
            # Formula: 2 * Challenge rating * size modifier
            cost = Decimal('2.0') * Decimal(str(self.challenge_rating)) * self.mercenary_size.gold_cost_recruitment_modifier
            return cost.quantize(Decimal('0.01')) # Quantize to 2 decimal places if needed, or use round()
        return Decimal('0.00')

    @property
    def calculated_food_cost_upkeep(self):
        """Food cost upkeep is directly from the MercenaryUnitSize."""
        if self.mercenary_size:
            return self.mercenary_size.food_cost_upkeep
        return Decimal('0.00')

    class Meta:
        verbose_name_plural = "Realm Mercenary Units"

    def __str__(self):
        return f"{self.mercenary_size} {self.race} unit for {self.realm.name}"
    
class MilitaryUnitSize(models.Model):
    """
    Defines the size category for military units, affecting costs.
    e.g., Solo, Tiny, Small, Medium.
    """
    name = models.CharField(max_length=50, unique=True)
    # Modifier for gold recruitment cost. e.g., 0.125 for Solo (1/8), 0.25 for Tiny (1/4)
    gold_cost_upkeep = models.IntegerField(default=1, help_text="Base gold cost for upkeep per unit of this size category per year.")
    # Direct food upkeep cost per unit of this size category per turn/season.
    food_cost_upkeep = models.IntegerField(default=1, help_text="Base food cost for upkeep per unit of this size category per year.")
    # Number of individuals this size represents.

    def __str__(self):
        return self.name

class RealmMilitaryUnit(models.Model):
    """
    An instance of a realm's own military unit.
    """
    race = models.ForeignKey(PopulationRace, on_delete=models.SET_NULL, null=True, blank=True)
    military_size = models.ForeignKey(MilitaryUnitSize, on_delete=models.PROTECT, related_name="unit_types")
    level = models.PositiveIntegerField(default=1, help_text="Base level of the unit type, affects stats and costs.")

    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='military_units')
    
    @property
    def calculated_gold_cost_upkeep(self):
        """Calculates gold cost for recruitment based on CR and size modifier."""
        if self.military_size:
            # Formula: Size modifier + level - 1
            cost = self.military_size.gold_cost_upkeep + (self.level - 1)
            return cost
        return 0

    @property
    def calculated_food_cost_upkeep(self):
        """Food cost upkeep is directly from the MercenaryUnitSize."""
        if self.military_size:
            return self.military_size.food_cost_upkeep
        return 0

    class Meta:
        verbose_name_plural = "Realm Military Units"

    def __str__(self):
        return f"Lvl {self.level} {self.military_size.name} {self.race} unit of {self.realm.name}"
    
class Season(models.Model):
    """Represents a game season."""
    name = models.CharField(max_length=20, primary_key=True)
    order = models.PositiveSmallIntegerField(unique=True, help_text="Order for sorting seasons (e.g., 1 for Spring).")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order']

class Descriptor(models.Model):
    """A category or tag for an action, e.g., 'Construction', 'Limited', 'Political'."""
    name = models.CharField(max_length=50, primary_key=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class ActionType(models.Model):
    """Stores the complete definition of a game action."""
    action_key = models.CharField(max_length=50, unique=True, primary_key=True,
                                  help_text="A unique key for game logic, e.g., 'build_farm'.")
    
    # Name & Description
    name = models.CharField(max_length=100, help_text="The user-facing name of the action.")
    description = models.TextField(help_text="A full description of the action and its effects.")

    # Descriptors (Tags/Categories)
    descriptors = models.ManyToManyField(Descriptor, blank=True)

    # Requirements & Costs
    prerequisites = models.JSONField(default=dict, blank=True,
                                     help_text="Conditions that must be met but are not consumed. E.g., {'building': {'barracks': 2}}")
    cost_gold = models.PositiveIntegerField(default=0)
    cost_wood = models.PositiveIntegerField(default=0)
    cost_stone = models.PositiveIntegerField(default=0)
    # Use JSON for flexible item costs
    cost_items = models.JSONField(default=dict, blank=True,
                                  help_text="Items consumed to perform the action. E.g., {'iron_ingots': 10}")

    # Season Availability & Modifications
    available_seasons = models.ManyToManyField(Season, blank=True, related_name='available_actions',
                                               help_text="Seasons when this action can be used. If empty, usable in all seasons.")
    
    seasonal_modifications = models.JSONField(default=dict, blank=True,
                                              help_text="JSON with modifications for specific seasons. E.g., {'Summer': {'cost_multiplier': 1.5}}")

    def __str__(self):
        return self.name
