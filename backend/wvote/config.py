from dataclasses import dataclass, field
from collections.abc import Sequence

@dataclass
class Config:
    """Holds configuration data for 8bot"""

    command_prefix: Sequence[str] = field(default_factory=lambda: ("8!",))
    """The list of prefixes for bot commands"""

    test_mode: bool = True
    """Whether the bot is running in test mode"""

    admins: Sequence[int] = (0,)
    """The list of administrators' Discord IDs"""

    results_blacklist: Sequence[int] = (0,)
    """The list of people not to send vote results to"""

    default_ttl: float = 30
    """How long a link is valid for, in minutes"""

    postentries_channel: int = 0
    """The channel ID to post entries in"""

    notify_admins_channel: int = 0
    """The channel ID to submit submission notifications in"""

    bot_key: str = "SET YOUR KEY"
    """The bot key to use for logging in with discord.py"""

    url_prefix: str = "http://127.0.0.1:8251"
    """The URL prefix to use for links"""

    http_port: int = 8251
    """The port to use for the HTTP server"""

    timezone_offset: float = 0
    """I can't remember what's up with this lmao"""

    deadline_time_offset: str = "00:00"
    """How far to offset the deadline for vote!howlong. """

    deadline_weekday: int = 4
    """
    The day of the week to use for the deadline. 0 is Sunday, 1 is Monday,
    2 is Tuesday, 3 is Wednesday, 4 is Thursday, 5 is Friday, and 6 is Saturday
    """

    allowed_hosts: Sequence[str] = ("https://soundcloud.com/", "https://clyp.it/")
    """Links for embedding playback, I'm pretty sure"""


