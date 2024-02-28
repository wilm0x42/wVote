import random
import datetime
import string
from typing import TypedDict
from . import config


class EditKey(TypedDict):
    entryUUID: str
    creationTime: datetime.datetime
    timeToLive: float


class AdminKey(TypedDict):
    creationTime: datetime.datetime
    timeToLive: float


class VoteKey(TypedDict):
    userID: int
    userName: str
    creationTime: datetime.datetime
    timeToLive: float


class Keys:
    def __init__(self, options: config.Config):
        self.edit_keys: dict[str, EditKey] = {}
        self.admin_keys: dict[str, AdminKey] = {}
        self.vote_keys: dict[str, VoteKey] = {}
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

    def is_valid_edit_key(self, key, uuid) -> bool:
        if not self.key_valid(key, self.edit_keys):
            return False

        return self.edit_keys[key]["entryUUID"] == uuid

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

    def create_vote_key(self, user_id: int, user_name: str) -> str:
        key = self.create_key()

        self.vote_keys[key] = {
            "userID": user_id,
            "userName": user_name,
            "creationTime": datetime.datetime.now(),
            "timeToLive": self.options.default_ttl,
        }

        return key
