# realms/templatetags/realms_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    # Ensure dictionary is a dictionary and key exists
    if isinstance(dictionary, dict) and key in dictionary:
        return dictionary.get(key)
    return None # Return None or a default value if not found/invalid