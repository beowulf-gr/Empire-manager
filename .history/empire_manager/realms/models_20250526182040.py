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
    treasury = models.IntegerField(default=0)
    debt = models.IntegerField(default=0)
    #resources = models.JSONField(default=dict)
    season = models.CharField(max_length=10, default="Spring")
    year = models.IntegerField(default=1)
    resources = models.ManyToManyField(Resource, through='RealmResource', related_name='realms_with_resource')
    goods = models.ManyToManyField(GoodsType, through='RealmGoodsType', related_name='realms_with_goods')
    loyalty_population = models.IntegerField(default=0)
    loyalty_military = models.IntegerField(default=0)
    loyalty_mercenaries = models.IntegerField(default=0,)

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
    settlement_capacity = models.IntegerField(default=1)
    #choices = models.JSONField(default=list, blank=True)

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

    def can_produce(self):
        return len(self.assigned_population) >= self.harvest

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
    resource_costs = models.JSONField(default=dict, help_text="JSON dictionary of resource costs, e.g., {'Wood': 50, 'Stone': 20, 'Gold': 100}")
    
    population_capacity_bonus = models.IntegerField(default=0, help_text="Bonus to population capacity.")

    def __str__(self):
        return self.name

class StrongholdInstance(models.Model):
    """
    An instance of a stronghold built on a specific LandUnit.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    population_cost = models.PositiveIntegerField(default=50, help_text="Population units required for construction/upgrade.")
    resource_costs = models.JSONField(default=dict, help_text="JSON dictionary of resource costs, e.g., {'Wood': 20, 'Iron': 10, 'Gold': 50}")

    # Prerequisites
    prerequisite_stronghold_types = models.ManyToManyField(StrongholdType, blank=True, help_text="Stronghold types required to build this improvement.")
    # prerequisite_other_improvements = models.ManyToManyField('self', symmetrical=False, blank=True, help_text="Other improvements required.") # If needed
    max_level = models.PositiveIntegerField(default=1, help_text="Maximum level this improvement can be upgraded to.")
    # construction_time = models.PositiveIntegerField(default=1, help_text="Time units (e.g., turns) to construct/upgrade.") # Replaced by duration_seasons

    def __str__(self):
        return self.name

class StrongholdImprovementInstance(models.Model):
    """
    An instance of an improvement built within a specific StrongholdInstance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stronghold_instance = models.ForeignKey(StrongholdInstance, on_delete=models.CASCADE, related_name='improvements')
    improvement_type = models.ForeignKey(StrongholdImprovementType, on_delete=models.PROTECT)
    level = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True, help_text="Is the improvement currently active and providing benefits?")
    construction_completed_turn = models.PositiveIntegerField(null=True, blank=True, help_text="Game turn when construction/upgrade was completed.")


    class Meta:
        unique_together = ('stronghold_instance', 'improvement_type') # Usually one of each type per stronghold, unless levels are handled differently

    def __str__(self):
        return f"{self.improvement_type.name} (Lvl {self.level}) in {self.stronghold_instance.name}"

class MercenaryUnitType(models.Model):
    """
    Defines types of mercenary units available for hire.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    race = models.ForeignKey(PopulationRace, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.PositiveIntegerField(default=10, help_text="Number of individuals in one unit of this type.")
    challenge_rating = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="A measure of the unit's overall combat effectiveness.")
    # Recruitment costs
    gold_cost_recruit = models.PositiveIntegerField(default=100)
    # Upkeep costs (per turn/season)
    gold_cost_upkeep = models.PositiveIntegerField(default=10)
    food_cost_upkeep = models.PositiveIntegerField(default=5)
    # Combat stats (can be expanded)
    attack_strength = models.PositiveIntegerField(default=10)
    defense_strength = models.PositiveIntegerField(default=5)
    hit_points = models.PositiveIntegerField(default=20)
    movement_range = models.PositiveIntegerField(default=3)
    icon_class = models.CharField(max_length=50, blank=True, null=True, help_text="CSS class for an icon.")


    def __str__(self):
        return f"{self.name} ({self.race.name if self.race else 'Mixed Race'})"

class RealmMercenaryUnit(models.Model):
    """
    An instance of a mercenary unit currently hired by a realm.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='mercenary_units')
    unit_type = models.ForeignKey(MercenaryUnitType, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, help_text="Number of these mercenary units hired.")
    location = models.ForeignKey(LandUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='stationed_mercenaries')
    contract_duration_turns = models.PositiveIntegerField(null=True, blank=True, help_text="Remaining duration of the contract in turns.")
    hired_on_turn = models.PositiveIntegerField()

    class Meta:
        verbose_name_plural = "Realm Mercenary Units"

    def __str__(self):
        return f"{self.quantity}x {self.unit_type.name} for {self.realm.name}"

class MilitaryUnitType(models.Model):
    """
    Defines types of military units that can be trained by a realm.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    race = models.ForeignKey(PopulationRace, on_delete=models.SET_NULL, null=True, blank=True)
    # Base attributes (per single unit of this type, actual stats might be modified by level, equipment, etc.)
    base_size = models.PositiveIntegerField(default=10, help_text="Typical number of individuals in one unit of this type.")
    base_level = models.PositiveIntegerField(default=1) # Starting level
    # Recruitment Costs
    base_gold_cost_recruit = models.PositiveIntegerField(default=50)
    base_food_cost_recruit = models.PositiveIntegerField(default=0) # Some units might not cost food to recruit initially
    base_resource_cost_recruit_type = models.ForeignKey(ResourceType, null=True, blank=True, on_delete=models.SET_NULL, related_name='military_units_costing_this')
    base_resource_cost_recruit_amount = models.PositiveIntegerField(default=0, null=True, blank=True)
    # Upkeep Costs (per turn/season)
    base_gold_cost_upkeep = models.PositiveIntegerField(default=5)
    base_food_cost_upkeep = models.PositiveIntegerField(default=2)
    # Combat Stats
    base_attack = models.PositiveIntegerField(default=5)
    base_defense = models.PositiveIntegerField(default=5)
    base_hit_points = models.PositiveIntegerField(default=10)
    base_movement_range = models.PositiveIntegerField(default=2)
    # Training
    training_time = models.PositiveIntegerField(default=1, help_text="Time units (e.g., turns) to train one unit.")
    can_be_trained_at = models.ManyToManyField(StrongholdImprovementType, blank=True, related_name='trainable_units', help_text="Improvements required to train this unit.")
    icon_class = models.CharField(max_length=50, blank=True, null=True, help_text="CSS class for an icon.")


    def __str__(self):
        return f"{self.name} ({self.race.name if self.race else 'Generic'})"

class RealmMilitaryUnit(models.Model):
    """
    An instance of a realm's own military unit.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='military_units')
    unit_type = models.ForeignKey(MilitaryUnitType, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1, help_text="Current veterancy level of the unit.")
    experience = models.PositiveIntegerField(default=0, help_text="Experience points towards next level.")
    location = models.ForeignKey(LandUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='stationed_military_units')
    # current_hit_points = models.PositiveIntegerField(null=True, blank=True) # To track damage if units are not just abstract quantities

    class Meta:
        verbose_name_plural = "Realm Military Units"

    # def save(self, *args, **kwargs):
    #     if self.current_hit_points is None:
    #         self.current_hit_points = self.unit_type.base_hit_points * self.quantity # Initial HP
    #     super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x Lvl {self.level} {self.unit_type.name} of {self.realm.name}"