import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import compo

def test_create_blank_entry():
    result = compo.create_blank_entry("wiglaf", discord_id="is a wiener")
    assert type(result) is str
