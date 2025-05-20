# empire_manager/realms/game_logic/action_definitions.py

# Define input types for form generation
INPUT_TYPE_TEXT = "text"
INPUT_TYPE_NUMBER = "number"
INPUT_TYPE_SELECT = "select" # For dropdowns (e.g., races, land units)

# --- Action Definitions ---
# Each action is a dictionary with:
# - 'name': Display name (e.g., "Recruit Population")
# - 'slug': Unique internal identifier (e.g., "recruit_population") - important for getattr
# - 'description': Detailed description for the modal
# - 'duration': How many seasons it takes
# - 'submit_text': Text for the action's primary button
# - 'inputs': List of dictionaries, each describing a form input field:
#   - 'name': Form field name (e.g., "target_race")
#   - 'label': Display label (e.g., "Target Race:")
#   - 'type': INPUT_TYPE_TEXT, INPUT_TYPE_NUMBER, INPUT_TYPE_SELECT
#   - 'required': True/False
#   - 'options_url': (Only for SELECT type) URL to fetch options (e.g., PopulationRace data)
#   - 'default': (Optional) Default value for input field

ALL_GAME_ACTIONS = {
    "Cultivate Fields": {
        "slug": "cultivate_fields",
        "description": "Prepare land for planting, increasing food production.",
        "duration": 1,
        "submit_text": "Start Cultivation",
        "inputs": [
            # Example: Maybe pick a specific land unit later? For now, no inputs.
        ]
    },
    "Recruit Peasants": {
        "slug": "recruit_peasants",
        "description": "Increase the population of your farmlands. A general call for new inhabitants.",
        "duration": 1,
        "submit_text": "Recruit",
        "inputs": []
    },
    "Scout Borders": {
        "slug": "scout_borders",
        "description": "Explore nearby territories for resources or threats.",
        "duration": 2,
        "submit_text": "Start Scouting",
        "inputs": []
    },
    "Harvest Crops": {
        "slug": "harvest_crops",
        "description": "Collect the food produced this season. (Usually an instant, seasonal action)",
        "duration": 1, # Even if instant, it might still have a duration for context
        "submit_text": "Harvest Now", # This might be an instant action, handled differently
        "inputs": []
    },
    "Train Militia": {
        "slug": "train_militia",
        "description": "Train basic military units for defense. Requires population.",
        "duration": 2,
        "submit_text": "Train",
        "inputs": []
    },
    "Trade Goods": {
        "slug": "trade_goods",
        "description": "Exchange resources with other realms for mutual benefit.",
        "duration": 1,
        "submit_text": "Initiate Trade",
        "inputs": []
    },
    "Gather Wood": {
        "slug": "gather_wood",
        "description": "Collect timber for construction and fuel.",
        "duration": 1,
        "submit_text": "Gather",
        "inputs": []
    },
    "Construct Building": {
        "slug": "construct_building",
        "description": "Start building a new structure, like a barracks or market.",
        "duration": 3,
        "submit_text": "Start Construction",
        "inputs": [
            # {"name": "building_type", "label": "Building Type:", "type": INPUT_TYPE_SELECT, "required": True, "options_url": "/some/building_types/url/"},
        ]
    },
    "Survey Resources": {
        "slug": "survey_resources",
        "description": "Search for new resource deposits in unexplored territories.",
        "duration": 3,
        "submit_text": "Start Survey",
        "inputs": []
    },
    "Stockpile Food": {
        "slug": "stockpile_food",
        "description": "Prepare for the harsh winter months by increasing food reserves.",
        "duration": 1,
        "submit_text": "Stockpile",
        "inputs": []
    },
    "Research Technology": {
        "slug": "research_technology",
        "description": "Invest in new advancements to unlock new abilities.",
        "duration": 4,
        "submit_text": "Start Research",
        "inputs": []
    },
    "Diplomacy": {
        "slug": "diplomacy",
        "description": "Engage in negotiations with other rulers or factions.",
        "duration": 2,
        "submit_text": "Initiate Diplomacy",
        "inputs": []
    },
    "Start Mining": {
        "slug": "start_mining",
        "description": "Begin extracting minerals from a suitable land unit.",
        "duration": 2,
        "submit_text": "Start Mining",
        "inputs": [
            # {"name": "land_unit_id", "label": "Mining Site:", "type": INPUT_TYPE_SELECT, "required": True, "options_url": "/some/land_units/url/"},
        ]
    },
    "Train Infantry": {
        "slug": "train_infantry",
        "description": "Recruit and train basic infantry units for your military. Requires gold and population.",
        "duration": 1,
        "submit_text": "Train Units",
        "inputs": [
            {"name": "quantity", "label": "Quantity:", "type": INPUT_TYPE_NUMBER, "required": True, "default": 1}
        ]
    },
    "Recruit Population": { # Your new action
        "slug": "recruit_population",
        "description": "Recruit new population units of a chosen race. Success depends on the recruiter's charisma.",
        "duration": 1,
        "submit_text": "Start Recruitment",
        "inputs": [
            {"name": "target_race", "label": "Target Race:", "type": INPUT_TYPE_SELECT, "required": True, "options_url": "/realm/get_population_races_json/"},
            {"name": "recruiter_race", "label": "Recruiter's Race:", "type": INPUT_TYPE_SELECT, "required": True, "options_url": "/realm/get_population_races_json/"},
            {"name": "charisma_modifier", "label": "Charisma Modifier:", "type": INPUT_TYPE_NUMBER, "required": True, "default": 0}
        ]
    },
}

# Mapping of seasonal names to action slugs
SEASONAL_ACTIONS = {
    "Spring": ["Cultivate Fields", "Recruit Peasants", "Scout Borders"],
    "Summer": ["Harvest Crops", "Train Militia", "Trade Goods"],
    "Autumn": ["Gather Wood", "Construct Building", "Survey Resources"],
    "Winter": ["Stockpile Food", "Research Technology", "Diplomacy"],
    "All": ["Start Mining", "Train Infantry", "Recruit Population"], # Actions always available
}

# Map slugs to the actual Python functions that handle the action's start/finish logic
# This assumes your start/finish functions are named like: start_cultivate_fields, finish_cultivate_fields etc.
ACTION_HANDLERS = {
    "cultivate_fields": {
        "module": "spring_actions",
        "start_func": "start_cultivate_fields",
        "finish_func": "finish_cultivate_fields",
    },
    "recruit_peasants": {
        "module": "spring_actions",
        "start_func": "start_recruit_peasants",
        "finish_func": "finish_recruit_peasants",
    },
    "scout_borders": {
        "module": "spring_actions",
        "start_func": "start_scout_borders",
        "finish_func": "finish_scout_borders",
    },
    "harvest_crops": {
        "module": "summer_actions",
        "start_func": "start_harvest_crops",
        "finish_func": "finish_harvest_crops",
    },
    "train_militia": {
        "module": "summer_actions",
        "start_func": "start_train_militia",
        "finish_func": "finish_train_militia",
    },
    "trade_goods": {
        "module": "summer_actions",
        "start_func": "start_trade_goods",
        "finish_func": "finish_trade_goods",
    },
    "gather_wood": {
        "module": "autumn_actions",
        "start_func": "start_gather_wood",
        "finish_func": "finish_gather_wood",
    },
    "construct_building": {
        "module": "autumn_actions",
        "start_func": "start_construct_building",
        "finish_func": "finish_construct_building",
    },
    "survey_resources": {
        "module": "autumn_actions",
        "start_func": "start_survey_resources",
        "finish_func": "finish_survey_resources",
    },
    "stockpile_food": {
        "module": "winter_actions",
        "start_func": "start_stockpile_food",
        "finish_func": "finish_stockpile_food",
    },
    "research_technology": {
        "module": "winter_actions",
        "start_func": "start_research_technology",
        "finish_func": "finish_research_technology",
    },
    "diplomacy": {
        "module": "winter_actions",
        "start_func": "start_diplomacy",
        "finish_func": "finish_diplomacy",
    },
    "start_mining": {
        "module": "economic_actions",
        "start_func": "start_mining",
        "finish_func": "apply_mining_yield", # Example, ensure this matches
    },
    "train_infantry": {
        "module": "military_actions",
        "start_func": "start_train_infantry",
        "finish_func": "finish_unit_training", # Example, ensure this matches
    },
    "recruit_population": {
        "module": "population_actions", # New module
        "start_func": "start_recruit_population",
        "finish_func": "finish_recruit_population",
    },
}