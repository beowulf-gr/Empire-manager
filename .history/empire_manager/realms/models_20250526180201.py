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
    #resources = models.JSONField(default=dict)
    season = models.CharField(max_length=10, default="Spring")
    year = models.IntegerField(default=1)
    resources = models.ManyToManyField(Resource, through='RealmResource', related_name='realms_with_resource')
    goods = models.ManyToManyField(GoodsType, through='RealmGoodsType', related_name='realms_with_goods')


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
    assigned_population = models.JSONField(default=list)
    upgrades = models.JSONField(default=list)
    mineral_type = models.CharField(max_length=50, null=True, blank=True)

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
