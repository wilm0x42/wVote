import random
import datetime
import string
from . import config


class Keys:
    def __init__(self, options: config.Config):
        self.edit_keys = {
            # "a1b2c3d4":
            # {
            #   "entryUUID": "cf56f9c3-e81f-43b0-b16b-de2144b54b02",
            #   "creationTime": datetime.datetime.now(),
            #   "timeToLive": 200
            # }
        }

        self.admin_keys = {
            # "a1b2c3d4":
            # {
            #   "creationTime": datetime.datetime.now(),
            #   "timeToLive": 200
            # }
        }

        self.vote_keys = {
            # "a1b2c3d4":
            # {
            #  "userID": 336685325231325184,
            #  "userName": "wilm0x42",
            #  "creationTime": datetime.datetime.now(),
            #  "timeToLive": 200
            # }
        }
        self.options = options

    def key_valid(self, key: str, keystore: dict) -> bool:
        """Validates a key. If it expires, it's removed from storage."""
        if key not in keystore:
            return False

        now = datetime.datetime.now()
        ttl = datetime.timedelta(minutes=keystore[key]["timeToLive"])

        if now - keystore[key]["creationTime"] > ttl:
            del keystore[key]
            return False

        return True

    def is_valid_admin_key(self, key) -> bool:
        return self.key_valid(key, self.admin_keys)

    def is_valid_vote_key(self, key) -> bool:
        return self.key_valid(key, self.vote_keys)

    def is_valid_edit_key(self, key) -> bool:
        return self.key_valid(key, self.edit_keys)

    def create_key(self, length: int = 8) -> str:
        """Generates a cryptographically-random alphanumeric key."""
        key_characters = string.ascii_letters + string.digits
        return "".join(
            random.SystemRandom().choice(key_characters) for _ in range(length)
        )

    def create_edit_key(self, entry_uuid: str) -> str:
        key = self.create_key()

        self.edit_keys[key] = {
            "entryUUID": entry_uuid,
            "creationTime": datetime.datetime.now(),
            "timeToLive": self.options.default_ttl,
        }

        return key

    def create_admin_key(self) -> str:
        key = self.create_key()

        self.admin_keys[key] = {
            "creationTime": datetime.datetime.now(),
            "timeToLive": self.options.default_ttl,
        }

        return key

    def create_vote_key(self, user_id: int, user_name) -> str:
        key = self.create_key()

        self.vote_keys[key] = {
            "userID": user_id,
            "userName": user_name,
            "creationTime": datetime.datetime.now(),
            "timeToLive": self.options.default_ttl,
        }

        return key
