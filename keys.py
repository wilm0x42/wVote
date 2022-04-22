import random
import datetime
import string
from botconfig import Config as config

edit_keys = {
    # "a1b2c3d4":
    # {
    #   "entryUUID": "cf56f9c3-e81f-43b0-b16b-de2144b54b02",
    #   "creationTime": datetime.datetime.now(),
    #   "timeToLive": 200
    # }
}

admin_keys = {
    # "a1b2c3d4":
    # {
    #   "creationTime": datetime.datetime.now(),
    #   "timeToLive": 200
    # }
}

vote_keys = {
    # "a1b2c3d4":
    # {
    #  "userID": 336685325231325184,
    #  "userName": "wilm0x42",
    #  "creationTime": datetime.datetime.now(),
    #  "timeToLive": 200
    # }
}


def key_valid(key: str, keystore: dict) -> bool:
    if key not in keystore:
        return False

    now = datetime.datetime.now()
    ttl = datetime.timedelta(minutes=keystore[key]["timeToLive"])

    if now - keystore[key]["creationTime"] < ttl:
        return True
    del keystore[key]
    return False


def create_key(length: int = 8) -> str:
    key_characters = string.ascii_letters + string.digits
    return ''.join(random.SystemRandom().choice(key_characters)
                   for _ in range(length))


def create_edit_key(entry_uuid: str) -> str:
    key = create_key()

    edit_keys[key] = {
        "entryUUID": entry_uuid,
        "creationTime": datetime.datetime.now(),
        "timeToLive": config.default_ttl
    }

    return key


def create_admin_key() -> str:
    key = create_key()

    admin_keys[key] = {
        "creationTime": datetime.datetime.now(),
        "timeToLive": config.default_ttl
    }

    return key


def create_vote_key(user_id: int, user_name) -> str:
    key = create_key()

    vote_keys[key] = {
        "userID": user_id,
        "userName": user_name,
        "creationTime": datetime.datetime.now(),
        "timeToLive": config.default_ttl
    }

    return key
