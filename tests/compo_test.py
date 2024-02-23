import compo
import uuid
import pytest

class TestCreateBlankEntry:
    def test_create_blank_entry_returns_string(self):
        result = compo.create_blank_entry("wiglaf", discord_id="is a wiener")
        assert type(result["uuid"]) is str

    def test_create_blank_entry_returns_valid_uuid(self):
        result = compo.create_blank_entry("wiglaf", discord_id="is still a wiener")

        try:
            uuid.UUID(result["uuid"])
        except ValueError:
            pytest.fail("create_blank_entry did not assign a valid uuid.")

class TestEntryValid:
    valid_entry = {
        "uuid": "totally",
        "pdf": "not",
        "pdfFilename": "trying",
        "mp3": "to",
        "mp3Format": "overthrow",
        "mp3Filename": "the",
        "entryName": "mods",
        "entrantName": "in #confetti"
    }

    def test_valid_entry(self):
        assert compo.entry_valid(self.valid_entry) == True

    def test_missing_requirements(self):
        for k, _ in self.valid_entry.items():
            invalid_entry = self.valid_entry.copy()
            del invalid_entry[k]

            assert compo.entry_valid(invalid_entry) == False

    def test_none_mp3(self):
        invalid_entry = self.valid_entry.copy()
        invalid_entry["mp3"] = None

        assert compo.entry_valid(invalid_entry) == False

    def test_none_pdf(self):
        invalid_entry = self.valid_entry.copy()
        invalid_entry["pdf"] = None

        assert compo.entry_valid(invalid_entry) == False


class TestLoadWeeks:
    def mock_pickle(self, mocker):
        mocker.patch("compo.pickle.load")
        mocker.patch("compo.open")

    def test_will_load_if_week_is_none(self, mocker):
        self.mock_pickle(mocker)

        compo.current_week = None
        compo.next_week = None

        compo.get_week(False)

        compo.pickle.load.assert_called()
        assert compo.pickle.load.call_count == 2

    def test_will_load_only_one_week_is_none(self, mocker):
        self.mock_pickle(mocker)

        compo.current_week = "CURRENT WEEK"
        compo.next_week = None

        result = compo.get_week(False)

        compo.open.assert_called_with("weeks/next-week.pickle", "rb")
        compo.pickle.load.assert_called()
        assert compo.pickle.load.call_count == 1
        assert result == "CURRENT WEEK"


class TestSaveWeeks:
    def mock_pickle(self, mocker):
        mocker.patch("compo.pickle.dump", return_value=None)
        mocker.patch("compo.open")

    def test_valid_write(self, mocker):
        self.mock_pickle(mocker)

        compo.current_week = "Solid"
        compo.next_week = "Snake"

        compo.save_weeks()

        compo.pickle.dump.assert_called()
        assert compo.pickle.dump.call_count == 2

    def test_current_week_none(self, mocker):
        self.mock_pickle(mocker)

        compo.current_week = None
        compo.next_week = "Raiden"

        compo.save_weeks()

        compo.pickle.dump.assert_not_called()

    def test_next_week_none(self, mocker):
        self.mock_pickle(mocker)

        compo.current_week = "Big Boss"
        compo.next_week = None

        compo.save_weeks()

        compo.pickle.dump.assert_not_called()

class TestMoveWeeks:
    def mock_pickle(self, mocker):
        mocker.patch("compo.pickle.dump", return_value=None)
        mocker.patch("compo.open")


    def test_move_weeks_dumps(self, mocker):
        self.mock_pickle(mocker)
        compo.move_to_next_week()

        compo.pickle.dump.assert_called()


    def test_move_weeks(self, mocker):
        self.mock_pickle(mocker)
        compo.current_week = "Gandalf the Gray"
        compo.next_week = "Gandalf the White"

        compo.move_to_next_week()

        assert compo.current_week == "Gandalf the White"
        assert compo.next_week == compo.blank_week()


class TestFindEntries:
    def setup_method(self):
        compo.current_week = compo.blank_week()
        compo.next_week = compo.blank_week()

    def test_cant_find_if_theres_nothing(self):
        found_entry = compo.find_entry_by_uuid("???")
        assert found_entry is None

    def test_cant_find_nonexistant(self):
        entry = compo.create_blank_entry("Hidden Guy", 0)

        compo.current_week["entries"].append(entry)

        found_entry = compo.find_entry_by_uuid("???")
        assert found_entry is None

    def test_can_find_current_week(self):
        entry = compo.create_blank_entry("Findable Guy", 1)

        compo.current_week["entries"].append(entry)

        found_entry = compo.find_entry_by_uuid(entry["uuid"])
        assert found_entry is entry


    def test_can_find_next_week(self):
        entry = compo.create_blank_entry("Findable Guy", 1)

        compo.next_week["entries"].append(entry)

        found_entry = compo.find_entry_by_uuid(entry["uuid"])
        assert found_entry is entry


class TestCountValidEntries:
    def test_no_entries_is_zero_valid(self):
        week = compo.blank_week()

        assert compo.count_valid_entries(week) == 0

    def test_only_invalid_entries_is_zero_valid(self):
        week = compo.blank_week()
        entry = compo.create_blank_entry("Invalid", 0)

        week["entries"].append(entry)

        assert not compo.entry_valid(entry)
        assert compo.count_valid_entries(week) == 0

    def test_counts_valid_entries(self):
        week = compo.blank_week()
        entry = compo.create_blank_entry("Invalid", 0)
        entry["pdf"] = "yes"
        entry["pdfFilename"] = "here"
        entry["mp3"] = "yes"
        entry["mp3Format"] = "here"
        entry["mp3Filename"] = "yes"

        week["entries"].append(entry)

        assert compo.entry_valid(entry)
        assert compo.count_valid_entries(week) == 1

class TestVerifyVotes:
    def test_all_is_good_by_default(self):
        week = compo.blank_week()

        compo.verify_votes(week)

        assert week["votes"] == []

    def test_a_single_vote_is_ok(self):
        week = compo.blank_week()
        votes = [{
            "userID": 1234,
            "ratings": [{
                "voteParam": "overall",
                "entryUUID": "123",
                "rating": 3
            }]
        }]
        week["votes"] = votes.copy()

        compo.verify_votes(week)

        assert week["votes"] == votes

    def test_cant_vote_too_high(self):
        week = compo.blank_week()
        votes = [{
            "userID": 1234,
            "ratings": [{
                "voteParam": "overall",
                "entryUUID": "123",
                "rating": 10
            }]
        }]
        week["votes"] = votes.copy()

        compo.verify_votes(week)

        assert week["votes"][0]["ratings"] == []

    def test_cant_vote_too_low(self):
        week = compo.blank_week()
        votes = [{
            "userID": 1234,
            "ratings": [{
                "voteParam": "overall",
                "entryUUID": "123",
                "rating": -5
            }]
        }]
        week["votes"] = votes.copy()

        compo.verify_votes(week)

        assert week["votes"][0]["ratings"] == []

    def test_duped_votes_are_discarded(self):
        week = compo.blank_week()
        rating1 = {
                "voteParam": "overall",
                "entryUUID": "123",
                "rating": 3
            }
        rating2 = {
                "voteParam": "overall",
                "entryUUID": "123",
                "rating": 4
            }
        votes = [{
            "userID": 1234,
            "ratings": [rating1, rating2]
        }]
        week["votes"] = votes.copy()

        compo.verify_votes(week)

        assert week["votes"][0]["ratings"] == [rating1]

class TestNormalizeVotes:
    def test_no_votes_means_no_scores(self):
        votes = []

        scores = compo.normalize_votes(votes)

        assert scores == {}

    def test_a_single_vote_is_averaged(self):
        votes = [{
            "userID": 1234,
            "ratings": [{
                "voteParam": "overall",
                "entryUUID": "123",
                "rating": 2
            }]
        }]

        scores = compo.normalize_votes(votes)

        assert scores == {"123": [(3, "overall")]}

    def test_no_ratings_left_still_works(self):
        votes = [{
            "userID": 1234,
            "ratings": []
        }]

        scores = compo.normalize_votes(votes)

        assert scores == {}

    def test_two_votes_become_extreme(self):
        votes = [{
            "userID": 1234,
            "ratings": [{
                "voteParam": "overall",
                "entryUUID": "123",
                "rating": 2
            }, {
                "voteParam": "overall",
                "entryUUID": "777",
                "rating": 3
            }]
        }]

        scores = compo.normalize_votes(votes)

        assert scores == {"123": [(1, "overall")], "777": [(5, "overall")]}
