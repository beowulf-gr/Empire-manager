# empire_manager/realms/game_logic/action_definitions.py

# Define input types for form generation
INPUT_TYPE_TEXT = "text"
INPUT_TYPE_NUMBER = "number"
INPUT_TYPE_SELECT = "select" # For dropdowns (e.g., races, land units)

# Map slugs to the actual Python functions that handle the action's start/finish logic
# This assumes your start/finish functions are named like: start_cultivate_fields, finish_cultivate_fields etc.
ACTION_HANDLERS = {
    "recruit_population": {
        "module": "generic_actions",
        "start_func": "start_recruit_population",
        #"finish_func": "finish_recruit_population",
    },
    "buy_resources": {
        "module": "generic_actions",
        "start_func": "start_buy_resources",
        #"finish_func": "finish_buy_resources",
    },
    "buy_goods": {
        "module": "generic_actions",
        "start_func": "start_buy_goods",
        #"finish_func": "finish_buy_resources",
    },
    "construct_stronghold": {
        "module": "generic_actions",
        "start_func": "start_construct_stronghold",
        "finish_func": "finish_construct_stronghold",
    },
    "build_roads": {
        "module": "generic_actions",
        "start_func": "start_build_roads",
        "finish_func": "finish_build_roads",
    },
    "build_mine": {
        "module": "generic_actions",
        "start_func": "start_build_mine",
        "finish_func": "finish_build_mine",
    },
    "upgrade_stronghold": {
        "module": "generic_actions",
        "start_func": "start_upgrade_stronghold",
        "finish_func": "finish_upgrade_stronghold",
    },
    "produce_goods": {
        "module": "generic_actions",
        "start_func": "start_produce_goods",
        "finish_func": "finish_produce_goods",
    },
}