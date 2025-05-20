from ..models import Realm, OngoingAction

def get_harvest_crops_details():
    return {"name": "Harvest Crops", "slug": "harvest_crops", "description": "I fucking harvest.", "duration": 1}

def start_harvest_crops(realm: Realm, post_data):
    OngoingAction.objects.create(realm=realm, action_name="harvest_crops", start_season=realm.season, start_year=realm.year, duration=1)
    return True

def get_train_militia_details():
    return {"name": "Train Militia", "slug": "train_militia", "description": "Train the goddamn Militia.", "duration": 1}

def start_train_militia(realm: Realm, post_data):
    OngoingAction.objects.create(realm=realm, action_name="train_militia", start_season=realm.season, start_year=realm.year, duration=1)
    return True