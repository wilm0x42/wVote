import compo
import uuid

class TestCreateBlankEntry:
    def test_create_blank_entry_returns_string(self):
        result = compo.create_blank_entry("wiglaf", discord_id="is a wiener")
        assert type(result) is str

    def test_create_blank_entry_returns_valid_uuid(self):
        result = compo.create_blank_entry("wiglaf", discord_id="is still a wiener")

        try:
            uuid.UUID(result)
        except ValueError:
            pytest.fail("create_blank_entry did not return a valid uuid.")

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
