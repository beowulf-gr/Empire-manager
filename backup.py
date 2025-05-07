from django.db import models
from django.contrib.postgres.fields import JSONField
import random

MINERAL_SUBTYPES = [
    ("Adamantine", 3),
    ("Copper", 17),
    ("Gold", 7),
    ("Iron", 60),
    ("Mithral", 3),
    ("Silver", 10)
]

class Realm(models.Model):
    name = models.CharField(max_length=100)
    ruler = models.CharField(max_length=100)
    treasury = models.IntegerField(default=0)
    resources = models.JSONField(default=dict)
    season = models.CharField(max_length=10, default="Spring")
    year = models.IntegerField(default=1)

    def __str__(self):
        return self.name


class LandUnit(models.Model):
    name = models.CharField(max_length=100)
    unit_type = models.CharField(max_length=50)
    production = models.JSONField(default=dict)
    choices = models.JSONField(default=list, blank=True)
    harvest = models.IntegerField(default=1)
    settlement_capacity = models.IntegerField(default=1)
    assigned_population = models.JSONField(default=list)
    upgrades = models.JSONField(default=list)
    mineral_type = models.CharField(max_length=50, null=True, blank=True)

    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='land_units')

    def can_produce(self):
        return len(self.assigned_population) >= self.harvest

    def produce_resources(self):
        resources = {}
        for assignment in self.assigned_population:
            if self.choices:
                choice = assignment.get("choice")
                if choice:
                    for res, amt in choice.items():
                        if res == "minerals":
                            if not self.mineral_type:
                                self.mineral_type = self._assign_mineral_type()
                                self.save()
                            resources[self.mineral_type] = resources.get(self.mineral_type, 0) + amt
                        else:
                            resources[res] = resources.get(res, 0) + amt
            else:
                for res, amt in self.production.items():
                    resources[res] = resources.get(res, 0) + amt
        return resources

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
    race = models.CharField(max_length=50)
    assigned_to = models.ForeignKey(LandUnit, on_delete=models.SET_NULL, null=True, blank=True, related_name='pop_units')
    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, related_name='population_units')

    def __str__(self):
        return f"{self.race} (assigned to: {self.assigned_to.name if self.assigned_to else 'None'})"
