from datetime import datetime, timedelta
from string import ascii_letters, digits
from uuid import uuid4
import json

import pytest
import keys

config = json.load(open("botconf.json", "r"))
keys.configure(config)

class TestKeyValid():
    # is it unneccessary to do all the tests with each type of key?
    # probably... 
                           # callable to create key, store 4 key, args 4 keygen
    @pytest.fixture(params=[(keys.create_edit_key, keys.edit_keys, ("spam",)),
                            (keys.create_admin_key, keys.admin_keys, ()),
                            (keys.create_vote_key, keys.vote_keys, (42, "a"))])
    def multi_run(self, request):
        return request
    
    @pytest.fixture()
    def valid_key(self, multi_run):
        key = multi_run.param[0](*multi_run.param[2])
        yield key, multi_run.param[1], multi_run.param[2]
        del multi_run.param[1][key]

    @pytest.fixture()
    def expired_key(self, multi_run):
        key_gen, store, args = multi_run.param
        key = key_gen(*args)
        full_key = store[key]
        past_ttl = timedelta(minutes=full_key["timeToLive"] + 1)
        full_key["creationTime"] -= past_ttl
        return key, store, args

    def test_key_valid(self, valid_key):
        assert keys.key_valid(valid_key[0], valid_key[1])

    def test_key_not_in_store(self, valid_key):
        assert keys.key_valid(valid_key[0], {}) == False
    
    def test_key_expired(self, expired_key):
        assert keys.key_valid(expired_key[0], expired_key[1]) == False

    def test_expired_key_removed(self, expired_key):
        key, store, args = expired_key
        keys.key_valid(key, store)
        assert key not in store

    # everything past here is maybe a little overkill but whatevs....
    def test_return_bool(self, valid_key, expired_key):
        assert isinstance(keys.key_valid(valid_key[0], valid_key[1]), bool)
        assert isinstance(keys.key_valid(valid_key[0], {}), bool)
        assert isinstance(keys.key_valid(expired_key[0], expired_key[1]), bool)

class TestCreateKey():
    def test_key_valid_chars(self):
        alphanumeric = ascii_letters + digits
        passing = True
        for i in range(12):
            key = keys.create_key(i)
            for char in key:
                if char not in alphanumeric:
                    passing = False
                assert passing
    
    def test_key_correct_length(self):
        passing = True
        for i in range(16):
            key = keys.create_key(i)
            if len(key) != i:
                passing = False
            assert passing
    
    def test_return_str(self):
        assert isinstance(keys.create_key(8), str)

class TestCreateEditKey():
    @pytest.fixture(scope="class")
    def edit_key(self):
        uuid = str(uuid4())
        key = keys.create_edit_key(uuid)
        yield key, uuid
        del keys.edit_keys[key]
    
    def test_return_string(self, edit_key):
        assert type(edit_key[0]) is str

    def test_key_in_store(self, edit_key):
        assert edit_key[0] in keys.edit_keys

    def test_key_uuid(self, edit_key):
        key, uuid_used = edit_key
        assert keys.edit_keys[key]["entryUUID"] == uuid_used

    @pytest.fixture()
    def timed_edit_key(self):
        before = datetime.now()
        key = keys.create_edit_key(str(uuid4()))
        after = datetime.now()
        yield before, key, after
        del keys.edit_keys[key]

    def test_key_creation_time(self, timed_edit_key):
        before, key, after = timed_edit_key
        assert before <= keys.edit_keys[key]["creationTime"] <= after

    def test_time_to_live(self, edit_key):
        assert keys.edit_keys[edit_key[0]]["timeToLive"] == config["default_ttl"]

class TestCreateAdminKey():
    @pytest.fixture(scope="class")
    def admin_key(self):
        key = keys.create_admin_key()
        yield key
        del keys.admin_keys[key]
    
    def test_return_string(self, admin_key):
        assert type(admin_key) is str

    def test_key_in_store(self, admin_key):
        assert admin_key in keys.admin_keys

    @pytest.fixture()
    def timed_admin_key(self):
        before = datetime.now()
        key = keys.create_admin_key()
        after = datetime.now()
        yield before, key, after
        del keys.admin_keys[key]

    def test_key_creation_time(self, timed_admin_key):
        before, key, after = timed_admin_key
        assert before <= keys.admin_keys[key]["creationTime"] <= after

    def test_time_to_live(self, admin_key):
        assert keys.admin_keys[admin_key]["timeToLive"] == config["default_ttl"]

class TestCreateVoteKey():
    @pytest.fixture(scope="class")
    def vote_key(self):
        id = 156896959783895040
        name = "wiggle"
        key = keys.create_vote_key(id, name)
        yield key, id, name
        del keys.vote_keys[key]
    
    def test_return_string(self, vote_key):
        assert type(vote_key[0]) is str

    def test_key_in_store(self, vote_key):
        assert vote_key[0] in keys.vote_keys

    def test_key_user_id(self, vote_key):
        assert keys.vote_keys[vote_key[0]]["userID"] == vote_key[1]

    def test_key_user_name(self, vote_key):    
        assert keys.vote_keys[vote_key[0]]["userName"] == vote_key[2]

    @pytest.fixture()
    def timed_vote_key(self):
        before = datetime.now()
        key = keys.create_vote_key(294207224920670218, "MAYOOOOO")
        after = datetime.now()
        yield before, key, after
        del keys.vote_keys[key]

    def test_key_creation_time(self, timed_vote_key):
        before, key, after = timed_vote_key
        assert before <= keys.vote_keys[key]["creationTime"] <= after

    def test_time_to_live(self, vote_key):
        assert keys.vote_keys[vote_key[0]]["timeToLive"] == config["default_ttl"]

class TestConfigure():
    @pytest.fixture()
    def set_config(self):
        old_config = keys.config
        new_config = { "this is": "a config", 1: 0 }
        keys.configure(new_config)
        yield new_config
        keys.config = old_config

    def test_configure(self, set_config):
        assert keys.config == set_config