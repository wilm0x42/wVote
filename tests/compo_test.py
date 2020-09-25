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
