import logging
import json
import urllib.parse
from typing import Dict

from aiohttp import web, web_request

from . import bot
from . import config
from . import compo
from . import keys

logger = logging.getLogger(__name__)
TOO_BIG_TEXT = """
File too big! We can only upload to discord files 8MB or less.
You can alternatively upload to SoundCloud or Clyp or something,
and provide us with a link. If you need help, ask us in
#weekly-challenge-discussion.
"""


class WebServer:
    def __init__(
        self,
        options: config.Config,
        bot: bot.WBot,
        compos: compo.Compos,
        keys: keys.Keys,
    ):
        self.options = options

        # Static/semi-static files:
        async def week_files_handler(request: web_request.Request) -> web.Response:
            """Download the requested file for an entry"""
            data, content_type = compos.get_entry_file(
                request.match_info["uuid"], request.match_info["filename"]
            )

            if not data:
                return web.Response(status=404, text="File not found")

            return web.Response(status=200, body=data, content_type=content_type)

        # API handlers
        async def get_entries_handler(request: web_request.Request) -> web.Response:
            """Display this weeks votable entries"""
            return web.json_response(
                format_week(compos.get_week(compo.THIS_WEEK), False)
            )

        async def get_entry_handler(request: web_request.Request) -> web.Response:
            """Return an entry for editing"""
            auth_key = request.match_info["authKey"]

            if not compos.get_week(compo.NEXT_WEEK)["submissionsOpen"]:
                return web.Response(
                    status=400, text="Submissions are currently closed!"
                )

            if not keys.is_valid_edit_key(auth_key):
                return web.Response(status=401, text="Invalid or expired link")

            key = keys.edit_keys[auth_key]

            entry = compos.find_entry_by_uuid(key["entryUUID"])

            if not entry:
                return web.Response(status=400, text="Entry doesn't exist")
            return web.json_response(get_editable_entry(entry))

        async def admin_get_data_handler(request: web_request.Request) -> web.Response:
            """Display admin data:

            - Week information
            - Submissions
            - Votes
            """
            auth_key = request.match_info["authKey"]

            if not keys.is_valid_admin_key(auth_key):
                return web.Response(status=401, text="Invalid or expired admin link")

            this_week = compos.get_week(compo.THIS_WEEK)
            next_week = compos.get_week(compo.NEXT_WEEK)

            weeks = [format_week(this_week, True), format_week(next_week, True)]
            votes = get_week_votes(this_week)

            data = {"weeks": weeks, "votes": votes}

            return web.json_response(data)

        async def admin_preview_handler(request: web_request.Request) -> web.Response:
            """Display next weeks votable entries"""
            auth_key = request.match_info["authKey"]

            if not keys.is_valid_admin_key(auth_key):
                return web.Response(status=401, text="Invalid or expired admin link")

            return web.json_response(
                format_week(compos.get_week(compo.NEXT_WEEK), False)
            )

        async def admin_viewvote_handler(request: web_request.Request) -> web.Response:
            """?"""
            auth_key = request.match_info["authKey"]
            user_id = request.match_info["userID"]

            if not keys.is_valid_admin_key(auth_key):
                return web.Response(status=401, text="Invalid or expired admin link")

            week = compos.get_week(compo.THIS_WEEK)

            for v in week["votes"]:
                if int(v["userID"]) == int(user_id):
                    return web.Response(
                        status=200, body=json.dumps(v), content_type="application/json"
                    )

            return web.Response(status=404, text="File not found")

        async def admin_deletevote_handler(
            request: web_request.Request,
        ) -> web.Response:
            """Delete every vote from an user"""
            auth_key = request.match_info["authKey"]
            user_id = request.match_info["userID"]

            if not keys.is_valid_admin_key(auth_key):
                return web.Response(status=401, text="Invalid or expired admin link")

            week = compos.get_week(compo.THIS_WEEK)
            week["votes"] = [
                vote for vote in week["votes"] if vote["userID"] != user_id
            ]

            compos.save_weeks()

            return web.Response(status=204)

        async def admin_control_handler(request: web_request.Request) -> web.Response:
            """Update week information"""
            auth_key = request.match_info["authKey"]

            if not keys.is_valid_admin_key(auth_key):
                return web.Response(status=401, text="Invalid or expired admin link")

            this_week = compos.get_week(compo.THIS_WEEK)
            next_week = compos.get_week(compo.NEXT_WEEK)

            data = await request.json()

            next_week["theme"] = data["weeks"][1]["theme"]
            next_week["date"] = data["weeks"][1]["date"]
            next_week["submissionsOpen"] = data["weeks"][1]["submissionsOpen"]

            this_week["theme"] = data["weeks"][0]["theme"]
            this_week["date"] = data["weeks"][0]["date"]
            this_week["votingOpen"] = data["weeks"][0]["votingOpen"]

            compos.save_weeks()
            return web.Response(status=204, text="Nice")

        async def admin_archive_handler(request: web_request.Request) -> web.Response:
            """Archive current week, move next week to current, and create a new week"""
            auth_key = request.match_info["authKey"]

            if not keys.is_valid_admin_key(auth_key):
                return web.Response(status=401, text="Invalid or expired admin link")

            compos.advance_weeks()

            return web.Response(status=204, text="Nice")

        async def admin_spoof_handler(request: web_request.Request) -> web.Response:
            """Create a fake new entry

            TODO: Take in more data?
            """
            auth_key = request.match_info["authKey"]

            if not keys.is_valid_admin_key(auth_key):
                return web.Response(status=401, text="Invalid or expired admin link")

            entry_data = await request.json()

            discord_id = None
            if "discordId" in entry_data:
                try:
                    discord_id = int(entry_data["discordId"])
                except ValueError:
                    pass
            new_entry = compo.create_blank_entry(entry_data["entrantName"], discord_id)
            week = compos.get_week(entry_data["nextWeek"])
            week["entries"].append(new_entry)

            return web.Response(status=204, text="Nice")

        async def file_post_handler(request: web_request.Request) -> web.Response:
            """Handle user submission.
            If user was an admin, mark entry as meddled with.

            This takes multipart/form-encoding because of large files
            """
            auth_key = request.match_info["authKey"]
            uuid = request.match_info["uuid"]

            is_authorized_user = (
                keys.is_valid_edit_key(auth_key)
                and keys.edit_keys[auth_key]["entryUUID"] == uuid
                and compos.get_week(compo.NEXT_WEEK)["submissionsOpen"]
            )

            is_admin = keys.is_valid_admin_key(auth_key)
            is_authorized = is_authorized_user or is_admin
            if not is_authorized:
                return web.Response(status=401, text="Invalid or expired link")

            # Find the entry
            choice = None
            for which_week in [True, False]:
                week = compos.get_week(which_week)

                for entry_index, entry in enumerate(week["entries"]):
                    if entry["uuid"] == uuid:
                        choice = (week, entry_index, entry)
                        break

            if choice is None:
                return web.Response(status=404, text="That entry doesn't seem to exist")

            week, entry_index, entry = choice

            # Process it
            reader = await request.multipart()
            if reader is None:
                return web.Response(status=400, text="Error uploading data idk")

            async for field in reader:
                if is_admin:
                    if field.name == "entrantName":
                        entry["entrantName"] = (await field.read(decode=True)).decode(
                            "utf-8"
                        )
                    elif field.name == "entryNotes":
                        entry["entryNotes"] = (await field.read(decode=True)).decode(
                            "utf-8"
                        )
                        if entry["entryNotes"] == "undefined":
                            entry["entryNotes"] = ""
                    elif field.name == "deleteEntry":
                        week["entries"].remove(entry)
                        compos.save_weeks()
                        return web.Response(
                            status=200, text="Entry successfully deleted."
                        )

                if field.name == "entryName":
                    entry["entryName"] = (await field.read(decode=True)).decode("utf-8")
                elif field.name == "mp3Link":
                    url = (await field.read(decode=True)).decode("utf-8")
                    if len(url) > 1:
                        if not any(
                            url.startswith(host) for host in options.allowed_hosts
                        ):
                            return web.Response(
                                status=400,
                                text="You entered a link to a website we don't allow.",
                            )

                        entry["mp3"] = url
                        entry["mp3Format"] = "external"
                        entry["mp3Filename"] = ""
                elif field.name == "mp3" or field.name == "pdf":
                    if field.filename == "" or not field.filename:
                        continue
                    if not field.filename.endswith(field.name):
                        error_message = "Wrong file format! Expected %s" % field.name
                        return web.Response(status=400, text=error_message)

                    size = 0
                    entry[field.name] = None

                    file_field_name = field.name + "Filename"
                    entry[file_field_name] = field.filename  # type: ignore

                    if field.name == "mp3":
                        entry["mp3Format"] = "mp3"

                    while True:
                        chunk = await field.read_chunk()
                        if not chunk:
                            break
                        size += len(chunk)
                        if size > 1000 * 1000 * 25:  # 25MB limit
                            entry[field.name] = None
                            entry[field.name + "Filename"] = None  # type: ignore
                            return web.Response(status=413, text=TOO_BIG_TEXT)
                        if entry.get(field.name) is None:
                            entry[field.name] = chunk
                        else:
                            entry[field.name] += chunk  # type: ignore

            if not is_admin:
                # Move the entry to the end of the list
                week["entries"].append(week["entries"].pop(entry_index))

            compos.save_weeks()

            await bot.submission_message(entry, is_admin)

            return web.Response(status=204)

        async def submit_vote_handler(request: web_request.Request) -> web.Response:
            """Record user votes"""
            vote_input = await request.json()

            auth_key = vote_input["voteKey"]

            if not keys.is_valid_vote_key(auth_key):
                return web.Response(status=401, text="Invalid or expired vote token")

            user_id = keys.vote_keys[auth_key]["userID"]
            user_name = keys.vote_keys[auth_key]["userName"]
            user_votes = vote_input["votes"]

            week = compos.get_week(compo.THIS_WEEK)

            # If user has submitted a vote already, then remove it, so we can
            # replace it with the new one
            for v in week["votes"]:
                if int(v["userID"]) == int(user_id):
                    week["votes"].remove(v)

            # Find the user's entry
            user_entry = None

            for entry in week["entries"]:
                if entry["discordID"] == user_id:
                    user_entry = entry
                    break

            # Remove the user's vote on their own entry (Search by UUID to prevent name spoofing).
            if user_entry is not None:
                user_votes = [
                    vote
                    for vote in user_votes
                    if vote["entryUUID"] != user_entry["uuid"]
                ]

                # Find the user's highest rating
                max_vote = max(vote["rating"] for vote in user_votes)

                # Grant the user rating equal to their highest vote on each category
                for param in week["voteParams"]:
                    user_votes.append(
                        {
                            "entryUUID": user_entry["uuid"],
                            "voteForName": user_name,
                            "voteParam": param,
                            "rating": max_vote,
                        }
                    )

            vote_data: compo.Vote = {
                "ratings": user_votes,
                "userID": user_id,
                "userName": user_name,
            }

            week["votes"].append(vote_data)

            compos.save_weeks()

            return web.Response(status=200, text="FRICK yeah")

        async def allowed_hosts_handler(request: web_request.Request) -> web.Response:
            """Returns the list of allowed hosts for song links"""

            return web.json_response(options.allowed_hosts)

        # Helpers
        def format_week(week: compo.Week, is_admin: bool) -> dict:
            """
            Massages week data into the format that will be output as JSON.
            """
            entry_data = []

            for e in week["entries"]:
                is_valid = compo.validate_entry(e)
                if not is_admin and not is_valid:
                    continue

                pruned_entry = {
                    "uuid": e["uuid"],
                    "mp3Format": e.get("mp3Format"),
                    "entryName": e["entryName"],
                    "entrantName": e["entrantName"],
                    "isValid": is_valid,
                }

                pdf_filename = e.get("pdfFilename")
                if pdf_filename is not None:
                    pruned_entry["pdfUrl"] = (
                        "/files/%s/%s" % (e["uuid"], urllib.parse.quote(pdf_filename)),
                    )
                else:
                    pruned_entry["pdfUrl"] = None

                if is_admin and "entryNotes" in e:
                    pruned_entry["entryNotes"] = e["entryNotes"]

                mp3Filename = e.get("mp3Filename")
                if e.get("mp3Format") == "mp3" and mp3Filename:
                    pruned_entry["mp3Url"] = "/files/%s/%s" % (
                        e["uuid"],
                        urllib.parse.quote(mp3Filename),
                    )
                else:
                    pruned_entry["mp3Url"] = e.get("mp3")

                # dummy vote data for the client's benefit
                for vote_param in week["voteParams"]:
                    pruned_entry[vote_param] = None

                entry_data.append(pruned_entry)

            if not week.get("helpTipDefs"):
                help_tip_defs = {}
                for vote_param in week["voteParams"]:
                    help_tip_defs[vote_param] = {
                        "1": "1",
                        "2": "2",
                        "3": "3",
                        "4": "4",
                        "5": "5",
                    }
            else:
                help_tip_defs = week["helpTipDefs"]

            data = {
                "entries": entry_data,
                "theme": week["theme"],
                "date": week["date"],
                "submissionsOpen": week["submissionsOpen"],
                "votingOpen": week["votingOpen"],
                "voteParams": week["voteParams"],
                "helpTipDefs": help_tip_defs,
            }

            return data

        def get_week_votes(week: compo.Week) -> list[compo.Vote]:
            adapted_data = week["votes"].copy()

            # JavaScript is very silly and won't work if we send these huge
            # numbers as actual numbers, so we have to stringify them first
            for v in adapted_data:
                v["userID"] = str(v["userID"])

            return adapted_data

        def get_editable_entry(entry: compo.Entry) -> dict:
            entry_data = {
                "uuid": entry["uuid"],
                "entryName": entry["entryName"],
                "entrantName": entry["entrantName"],
                "pdfUrl": None,
                "mp3Format": entry.get("mp3Format"),
            }

            mp3Filename = entry.get("mp3Filename")
            if entry.get("mp3Format") == "mp3" and mp3Filename:
                entry_data["mp3Url"] = f"/api/files/{entry['uuid']}/{mp3Filename}"
            else:
                entry_data["mp3Url"] = entry.get("mp3")

            if entry.get("pdfFilename") is not None:
                entry_data["pdfUrl"] = "/api/files/%s/%s" % (
                    entry["uuid"],
                    entry.get("pdfFilename"),
                )

            return entry_data

        server = web.Application()

        server.add_routes(
            [
                web.get("/api/files/{uuid}/{filename}", week_files_handler),
                web.get("/api/entry_data", get_entries_handler),
                web.get("/api/entry_data/{authKey}", get_entry_handler),
                web.get("/api/allowed_hosts", allowed_hosts_handler),
                web.get("/api/admin/get_admin_data/{authKey}", admin_get_data_handler),
                web.get("/api/admin/get_preview_data/{authKey}", admin_preview_handler),
                web.get(
                    "/api/admin/viewvote/{authKey}/{userID}", admin_viewvote_handler
                ),
                web.post("/api/admin/edit/{authKey}", admin_control_handler),
                web.post("/api/admin/archive/{authKey}", admin_archive_handler),
                web.post("/api/admin/spoof/{authKey}", admin_spoof_handler),
                web.post(
                    "/api/admin/delete_vote/{authKey}/{userID}",
                    admin_deletevote_handler,
                ),
                web.post("/api/edit/post/{uuid}/{authKey}", file_post_handler),
                web.post("/api/submit_vote", submit_vote_handler),
                web.static("/", "static"),
            ]
        )
        self.server = server

    async def start_http(self) -> None:
        """Starts the HTTP server"""
        runner = web.AppRunner(self.server)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.options.http_port)
        await site.start()
        logging.info("HTTP: Started server")
