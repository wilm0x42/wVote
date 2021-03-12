import compo
import uuid
import pickle

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

class TestSaveWeeks:
    def mock_pickle(self, mocker):
        mocker.patch("compo.pickle.dump")
        mocker.patch("compo.open")

    def test_valid_write(self, mocker):
        self.mock_pickle(mocker)

        compo.current_week = "Solid"
        compo.next_week = "Snake"

        compo.save_weeks()

        pickle.dump.assert_called()
        assert pickle.dump.call_count == 2

    def test_current_week_none(self, mocker):
        self.mock_pickle(mocker)

        compo.current_week = None
        compo.next_week = "Raiden"

        compo.save_weeks()

        pickle.dump.assert_not_called()

    def test_next_week_none(self, mocker):
        self.mock_pickle(mocker)

        compo.current_week = "Big Boss"
        compo.next_week = None

        compo.save_weeks()

        pickle.dump.assert_not_called()
