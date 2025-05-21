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
    "Recruit Population": {
        "name": "Recruit Population", # <--- ADD THIS
        "slug": "recruit_population",
        "description": "Recruit new population units of a chosen race. Success depends on the recruiter's charisma.",
        "duration": 1,
        "submit_text": "Start Recruitment",
        "inputs": [
            {"name": "target_race", "label": "Target Race:", "type": INPUT_TYPE_SELECT, "required": True, "options_url": "/realm/get_population_races_json/"},
            {"name": "charisma_modifier", "label": "Charisma Modifier:", "type": INPUT_TYPE_NUMBER, "required": True, "default": 0}
        ]
    },
    "Buy Goods": {
        "name": "Buy Goods",
        "slug": "buy_goods",
        "description": "Purchase goods from the market.",
        "duration": 1,
        "submit_text": "Buy Goods",
        "inputs": [
            {"name": "goods_type", "label": "Goods Type:", "type": INPUT_TYPE_SELECT, "required": True, "options_url": "/realm/get_goods_types_json/"},
            {"name": "quantity", "label": "Quantity:", "type": INPUT_TYPE_NUMBER, "required": True, "default": 1}
        ]
    },
}

# Mapping of seasonal names to action slugs
SEASONAL_ACTIONS = {
    "Spring": [],
    "Summer": [],
    "Autumn": [],
    "Winter": [],
    "All": ["Recruit Population", "Buy Goods"], # Actions always available
}

# Map slugs to the actual Python functions that handle the action's start/finish logic
# This assumes your start/finish functions are named like: start_cultivate_fields, finish_cultivate_fields etc.
ACTION_HANDLERS = {
    "recruit_population": {
        "module": "generic_actions",
        "start_func": "start_recruit_population",
        "finish_func": "finish_recruit_population",
    },
    "buy_goods": {
        "module": "generic_actions",
        "start_func": "start_buy_goods",
        "finish_func": "finish_buy_goods",
    },
}