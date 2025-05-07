# models.py

import json
import random

# Default configuration per land type
LAND_TYPE_DATA = {
    "Plains": {
        "production": {"food": 4},
        "choices": [],
        "harvest": 1,
        "settlement_capacity": 4
    },
    "Forest": {
        "production": {"lumber": 4, "food": 1},
        "choices": [],
        "harvest": 1,
        "settlement_capacity": 2
    },
    "Hills": {
        "production": {},
        "choices": [
            {"stone": 2},
            {"minerals": 1}
        ],
        "harvest": 1,
        "settlement_capacity": 1
    },
    "Mountains": {
        "production": {},
        "choices": [
            {"minerals": 2},
            {"stone": 4}
        ],
        "harvest": 2,
        "settlement_capacity": 2
    },
    "Swamp": {
        "production": {"food": 1, "gold":1},
        "choices": [],
        "harvest": 2,
        "settlement_capacity": 1
    },
    "Water": {
        "production": {"food": 2},
        "choices": [],
        "harvest": 1,
        "settlement_capacity": 1
    },
    "Wasteland": {
        "production": {},
        "choices": [],
        "harvest": 0,
        "settlement_capacity": 1
    },
    "Ruins": {
        "production": {"gold":random.randint(1, 10)-4},
        "choices": [],
        "harvest": 2,
        "settlement_capacity": 2
    },
}

MINERAL_SUBTYPES = [
    ("Adamantine", 3),
    ("Copper", 17),
    ("Gold", 7),
    ("Iron", 60),
    ("Mithral", 3),
    ("Silver", 10)
]

class PopulationUnit:
    def __init__(self, race):
        self.race = race
        self.assigned_to = None  # LandUnit name or None

    def to_dict(self):
        return {"race": self.race, "assigned_to": self.assigned_to}

    @staticmethod
    def from_dict(data):
        pu = PopulationUnit(data["race"])
        pu.assigned_to = data["assigned_to"]
        return pu


class LandUnit:
    def __init__(self, name, unit_type):
        self.name = name
        self.unit_type = unit_type
        self.production = LAND_TYPE_DATA[unit_type]["production"].copy()
        self.choices = LAND_TYPE_DATA[unit_type].get("choices", []).copy()
        self.harvest = LAND_TYPE_DATA[unit_type]["harvest"]
        self.settlement_capacity = LAND_TYPE_DATA[unit_type]["settlement_capacity"]
        self.assigned_population = []  # list of dicts: {"index": int, "choice": dict or None}
        self.upgrades = []
        self.mineral_type = None  # For land units producing minerals

    def can_produce(self):
        return len(self.assigned_population) >= self.harvest

    def produce_resources(self):
        resources = {}
        for assignment in self.assigned_population:
            if self.choices:
                choice = assignment.get("choice")
                if choice:
                    for res, amt in choice.items():
                        # Handle mineral subtype
                        if res == "minerals":
                            if not self.mineral_type:
                                self.mineral_type = self._assign_mineral_type()
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
        return "Iron"  # Fallback

    def to_dict(self):
        return {
            "name": self.name,
            "unit_type": self.unit_type,
            "production": self.production,
            "choices": self.choices,
            "harvest": self.harvest,
            "settlement_capacity": self.settlement_capacity,
            "assigned_population": self.assigned_population,
            "upgrades": self.upgrades,
            "mineral_type": self.mineral_type
        }

    @staticmethod
    def from_dict(data):
        unit = LandUnit(data["name"], data["unit_type"])
        unit.production = data["production"]
        unit.choices = data.get("choices", [])
        unit.harvest = data["harvest"]
        unit.settlement_capacity = data["settlement_capacity"]
        unit.assigned_population = data["assigned_population"]
        unit.upgrades = data["upgrades"]
        unit.mineral_type = data.get("mineral_type")
        return unit


class Realm:
    def __init__(self, name, ruler):
        self.name = name
        self.ruler = ruler
        self.treasury = 0  # gold units
        self.resources = {}  # e.g., {"food": 10, "wood": 5}
        self.population_units = []  # list of PopulationUnit
        self.land_units = []  # list of LandUnit
        self.season = "Spring"
        self.year = 1

    def add_population_unit(self, race):
        self.population_units.append(PopulationUnit(race))

    def add_land_unit(self, name, unit_type):
        self.land_units.append(LandUnit(name, unit_type))

    def assign_population_to_land(self, pop_index, land_name, choice=None):
        pop = self.population_units[pop_index]
        for unit in self.land_units:
            if unit.name == land_name:
                if len(unit.assigned_population) < unit.settlement_capacity:
                    if pop.assigned_to:
                        self.unassign_population(pop_index)
                    unit.assigned_population.append({"index": pop_index, "choice": choice})
                    pop.assigned_to = land_name
                break

    def unassign_population(self, pop_index):
        pop = self.population_units[pop_index]
        if pop.assigned_to:
            for unit in self.land_units:
                if unit.name == pop.assigned_to:
                    unit.assigned_population = [a for a in unit.assigned_population if a["index"] != pop_index]
            pop.assigned_to = None

    def collect_production(self):
        for unit in self.land_units:
            for resource, amount in unit.produce_resources().items():
                self.resources[resource] = self.resources.get(resource, 0) + amount

    def advance_season(self):
        seasons = ["Spring", "Summer", "Autumn", "Winter"]
        index = seasons.index(self.season)
        self.season = seasons[(index + 1) % 4]
        if self.season == "Spring":
            self.year += 1

    def to_dict(self):
        return {
            "name": self.name,
            "ruler": self.ruler,
            "treasury": self.treasury,
            "resources": self.resources,
            "population_units": [p.to_dict() for p in self.population_units],
            "land_units": [l.to_dict() for l in self.land_units],
            "season": self.season,
            "year": self.year
        }

    @staticmethod
    def from_dict(data):
        realm = Realm(data["name"], data["ruler"])
        realm.treasury = data["treasury"]
        realm.resources = data["resources"]
        realm.population_units = [PopulationUnit.from_dict(p) for p in data["population_units"]]
        realm.land_units = [LandUnit.from_dict(l) for l in data["land_units"]]
        realm.season = data["season"]
        realm.year = data["year"]
        return realm

    def save_to_file(self, filename):
        with open(filename, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @staticmethod
    def load_from_file(filename):
        with open(filename, "r") as f:
            data = json.load(f)
        return Realm.from_dict(data)
