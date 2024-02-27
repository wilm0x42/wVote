import datetime
import uuid
import logging
import statistics
import pickle
from typing import Optional, TypedDict, Union, Literal, BinaryIO, Any

THIS_WEEK = True
NEXT_WEEK = False


class Rating(TypedDict):
    rating: int
    entryUUID: str
    voteParam: str


class Vote(TypedDict):
    ratings: list[Rating]
    userID: str
    userName: str


class MandatoryEntryFields(TypedDict):
    entryName: str
    entrantName: str
    discordID: Optional[int]
    uuid: str


class Entry(MandatoryEntryFields, total=False):
    entryNotes: str
    mp3Format: Union[None, Literal["external", "mp3"]]
    pdfFilename: Optional[str]
    mp3Filename: Optional[str]
    pdf: Optional[bytes]
    mp3: Union[None, bytes, str]
    voteScore: Optional[float]
    votePlacement: Optional[int]


class ValidEntry(MandatoryEntryFields):
    entryNotes: str
    mp3Format: Union[None, Literal["external", "mp3"]]
    pdfFilename: Optional[str]
    mp3Filename: Optional[str]
    pdf: Optional[bytes]
    mp3: Union[None, bytes, str]
    voteScore: Optional[float]
    votePlacement: Optional[int]


class Week(TypedDict):
    theme: str
    date: str
    submissionsOpen: bool
    votingOpen: bool
    entries: list[Entry]
    votes: list[Vote]
    voteParams: list[str]
    helpTipDefs: dict[str, dict[str, str]]
    crudbroke: int


class PickleTool:
    def load(self, file: BinaryIO):
        return pickle.load(file)
    
    def dump(self, data: Any, file: BinaryIO):
        return pickle.dump(data, file)
    
class Compos:
    def __init__(self, pickletool: PickleTool):
        self.current_week: Optional[Week] = None
        self.next_week: Optional[Week] = None
        self.pickletool = pickletool

    def blank_week(self) -> Week:
        return {
            "theme": "Week XYZ: Fill this in by hand!",
            "date": "Month day'th 20XX",
            "submissionsOpen": True,
            "votingOpen": True,
            "entries": [],
            "votes": [],
            "voteParams": ["prompt", "score", "overall"],
            "helpTipDefs": {
                "prompt": {
                    "1": "1 - Blatantly breaks rules",
                    "2": "2 - Not really in the spirit of things",
                    "3": "3 - Fits fine as far as I'm concerned!",
                    "4": "4 - Exemplary interpretation!",
                    "5": "5 - Incredibly creative!",
                },
                "score": {
                    "1": "1 - Not useful",
                    "2": "2 - Some important issues",
                    "3": "3 - Not bad!",
                    "4": "4 - Looks very nice!",
                    "5": "5 - Beautiful!",
                },
                "overall": {
                    "1": "1 - Just not for me",
                    "2": "2 - It's got potential",
                    "3": "3 - I like this!",
                    "4": "4 - Above average for me!",
                    "5": "5 - Simply outstanding!",
                },
            },
            "crudbroke": 0,
        }

    def get_week(self, get_next_week: bool) -> Week:
        """
        Returns a dictionary that encodes information for a week's challenge. If
        the requested week has no information, attempts to read previously
        serialized information. If the pickle object was not found, returns
        a new dictionary.

        Parameters
        ----------
        get_next_week : bool
            Whether the week that should be retrieved is the following week.
            False returns the current week's information, while True retrieves
            next week's information.

        Returns
        -------
        dict
            A dictionary that encodes information for a week. The information
            includes theme, date, whether submissions are open, and a list of
            entries.
        """

        if self.current_week is None:
            try:
                self.current_week = self.pickletool.load(open("weeks/current-week.pickle", "rb"))
            except FileNotFoundError:
                self.current_week = self.blank_week()
                # self.current_week["submissionsOpen"] = False

        if self.next_week is None:
            try:
                self.next_week = self.pickletool.load(open("weeks/next-week.pickle", "rb"))
            except FileNotFoundError:
                self.next_week = self.blank_week()

        return self.next_week if get_next_week else self.current_week

    def save_weeks(self) -> None:
        """
        Saves `current_week` and `next_week` into pickle objects so that they can
        later be read again.
        """
        if self.current_week is not None and self.next_week is not None:
            self.pickletool.dump(self.current_week, open("weeks/current-week.pickle", "wb"))
            self.pickletool.dump(self.next_week, open("weeks/next-week.pickle", "wb"))
            logging.info("COMPO: current-week.pickle and next-week.pickle overwritten")

    def advance_weeks(self) -> None:
        """
        Archives the current week, then replaces `current_week` with `next_week`,
        freeing up `next_week` to be replaced with new information.

        Calls `save_weeks()` to serialize the data after modification.
        """

        with open(
            "weeks/archive/" + datetime.datetime.now().strftime("%y-%m-%d") + ".pickle",
            "wb",
        ) as archive_file:
            self.pickletool.dump(self.current_week, archive_file)

        self.current_week = self.next_week
        self.next_week = self.blank_week()

        self.save_weeks()

    def find_entry_by_uuid(self, uuid: str) -> Optional[Entry]:
        for which_week in [THIS_WEEK, NEXT_WEEK]:
            for entry in self.get_week(which_week)["entries"]:
                if entry["uuid"] == uuid:
                    return entry
        return None

    def get_entry_file(
        self, uuid: str, filename: str
    ) -> Union[tuple[Union[bytes, str, None], str], tuple[None, None]]:
        entry = self.find_entry_by_uuid(uuid)
        if entry is None:
            return None, None

        if (
            "mp3" in entry
            and "mp3Filename" in entry
            and entry["mp3Filename"] == filename
        ):
            return entry["mp3"], "audio/mpeg"

        if (
            "pdf" in entry
            and "pdfFilename" in entry
            and entry["pdfFilename"] == filename
        ):
            return entry["pdf"], "application/pdf"

        return None, None

    def get_ranked_entrant_list(self, week: Week) -> list:
        """Bloc STAR Voting wooooo"""

        param_weights = {"prompt": 0.33, "score": 0.33, "overall": 0.33}

        if len(week["entries"]) < 1:  # lol no one submitted
            return []

        verify_votes(week)

        scores = normalize_votes(week["votes"])

        entry_pool: list[Entry] = []

        # Write final scores to entry data, and put 'em all in entry_pool
        v_entries: list[Entry] = week["entries"]  # type: ignore
        for e in v_entries:
            if validate_entry(e):
                e["voteScore"] = statistics.mean(
                    score[0] for score in scores.get(e["uuid"], [(0, None)])
                )
                entry_pool.append(e)

        ranked_entries: list[Entry] = []
        # Now that we have scores calculated, run the actual STAR algorithm
        while len(entry_pool) > 1:
            entry_pool = sorted(entry_pool, key=lambda e: e["voteScore"], reverse=True)

            entry_a = entry_pool[0]
            entry_b = entry_pool[1]

            prefer_entry_a = 0
            prefer_entry_b = 0

            for v in week["votes"]:
                # note that normalization doesn't matter for comparing preference
                score_a = sum(
                    r["rating"] * param_weights[r["voteParam"]]
                    for r in v["ratings"]
                    if r["entryUUID"] == entry_a["uuid"]
                )
                score_b = sum(
                    r["rating"] * param_weights[r["voteParam"]]
                    for r in v["ratings"]
                    if r["entryUUID"] == entry_b["uuid"]
                )

                if score_a > score_b:
                    prefer_entry_a += 1
                elif score_b > score_a:
                    prefer_entry_b += 1

            # greater than or equal to, as entry_a is the entry with a higher score,
            # to settle things in the case of a tie
            if prefer_entry_a >= prefer_entry_b:
                ranked_entries.append(entry_pool.pop(0))
            else:
                ranked_entries.append(entry_pool.pop(1))

        # Add the one remaining entry
        ranked_entries.append(entry_pool.pop(0))

        for place, e in enumerate(ranked_entries):
            e["votePlacement"] = place + 1

        return list(reversed(ranked_entries))


def verify_votes(week: Week) -> None:
    # Makes sure a single user can only vote on the same parameter
    # for the same entry a single time
    user_votes = set({})

    # Validate data, and throw away sus ratings
    for v in week["votes"]:
        for r in v["ratings"]:
            if not (
                0 <= r["rating"] <= 5
                and r["voteParam"] in week["voteParams"]
                and (v["userID"], r["entryUUID"], r["voteParam"]) not in user_votes
            ):
                logging.warning("COMPO: FRAUD DETECTED (CHECK VOTES)")
                logging.warning(f"Sus rating: {str(r)}")
                v["ratings"].remove(r)
                continue

            user_votes.add((v["userID"], r["entryUUID"], r["voteParam"]))


def fetch_votes_for_entry(votes: list, entry_uuid: str) -> list:
    """List all non-zero votes for an entry"""

    return [
        r
        for v in votes
        for r in v["ratings"]
        if r["rating"] != 0 and r["entryUUID"] == entry_uuid
    ]


def normalize_votes(votes: list[Vote]) -> dict[str, list[tuple[float, str]]]:
    """Trim away 0-votes and normalize each user's scores
    into the 1-5 range.
    """
    scores: dict[str, list[tuple[float, str]]] = {}

    for v in votes:
        valid_ratings = [r for r in v["ratings"] if r["rating"] != 0]

        if not valid_ratings:
            # The user cleared all votes
            continue

        rating_values = [r["rating"] for r in valid_ratings]

        minimum = min(rating_values)
        maximum = max(rating_values)
        extent = maximum - minimum

        for r in valid_ratings:
            if extent == 0:
                normalized = 3.0
            else:
                normalized = (float(r["rating"]) - minimum) / extent * 4 + 1

            scores.setdefault(r["entryUUID"], []).append((normalized, r["voteParam"]))

    return scores


def add_to_week(week: Week, entry: Entry):
    week["entries"].append(entry)


def validate_entry(entry: Entry) -> Union[ValidEntry, None]:
    requirements = [
        "uuid",
        "pdf",
        "pdfFilename",
        "mp3",
        "mp3Format",
        "mp3Filename",
        "entryName",
        "entrantName",
    ]

    if any(requirement not in entry for requirement in requirements):
        return None

    if not all(entry[param] is not None for param in ["mp3", "pdf"]):
        return None
    
    return entry # type: ignore


def valid_entries(week: Week) -> list[ValidEntry]:
    return [e for e in week["entries"] if validate_entry(e)] # type: ignore


def create_blank_entry(entrant_name: str, discord_id: Optional[int]) -> Entry:
    """
    Create a blank entry for an entrant and returns a UUID

    Parameters
    ----------
    entrant_name : str
        The name of the entrant
    discord_id : int
        The entrant's Discord ID

    Returns
    -------
    entry : dict
        A new Entry
    """
    return {
        "entryName": "",
        "entrantName": entrant_name,
        "discordID": discord_id,
        "uuid": str(uuid.uuid4()),
    }
