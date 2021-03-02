#!/usr/bin/env python3

import html as html_lib
import string
import logging
import json

from aiohttp import web, web_request

import compo
import keys
import bot

config: dict = None

vote_template = open("templates/vote.html", "r").read()
submit_template = open("templates/submit.html", "r").read()
thanks_template = open("templates/thanks.html", "r").read()  #TODO: Remove
admin_template = open("templates/admin.html", "r").read()

favicon = open("static/favicon.ico", "rb").read()


too_big_text = """
File too big! We can only upload to discord files 8MB or less.
You can alternatively upload to SoundCloud or Clyp or something,
and provide us with a link. If you need help, ask us in
#weekly-challenge-discussion.
"""

# TODO: Put in config
def get_vue_url() -> str:
    global config

    if config["test_mode"]:
        return "https://cdn.jsdelivr.net/npm/vue@2/dist/vue.js"
    else:
        return "https://cdn.jsdelivr.net/npm/vue@2"


# Static/semi-static files:
async def vote_handler(request: web_request.Request) -> web.Response:
    html = vote_template.replace("[VUE-URL]", get_vue_url())

    return web.Response(text=html, content_type="text/html")


async def favicon_handler(request: web_request.Request) -> web.Response:
    return web.Response(body=favicon)


async def week_files_handler(request: web_request.Request) -> web.Response:
    data, content_type = compo.get_entry_file(request.match_info["uuid"],
                                              request.match_info["filename"])

    if not data:
        return web.Response(status=404, text="File not found")

    return web.Response(status=200, body=data, content_type=content_type)


async def admin_handler(request: web_request.Request) -> web.Response:
    auth_key = request.match_info["authKey"]

    if not keys.key_valid(auth_key, keys.admin_keys):
        return web.Response(status=404, text="File not found")

    html = admin_template.replace("[VUE-URL]", get_vue_url())
    html = html.replace("[ADMIN-KEY]", auth_key)

    return web.Response(status=200, body=html, content_type="text/html")


#TODO: Remove
async def vote_thanks_handler(request: web_request.Request) -> web.Response:
    message = thanks_template.replace("[HEADER]", "Thank you for voting!")
    message = message.replace("[BODY]",
        "Your vote has been recorded.  I will guard it with my life. :)")
    return web.Response(status=200, body=message, content_type="text/html")


# API handlers (JSON -> JSON)
async def get_entries_handler(request: web_request.Request) -> web.Response:
    return web.json_response(get_week_viewer(False, True))


async def admin_get_data_handler(request: web_request.Request) -> web.Response:
    auth_key = request.match_info["authKey"]

    if not keys.key_valid(auth_key, keys.admin_keys):
        return web.Response(status=404, text="File not found")


    weeks = [get_week_viewer(False, False), get_week_viewer(True, False)]
    votes = get_week_votes(False)

    data = {
        "weeks": weeks,
        "votes": votes
    }

    return web.json_response(data)


async def edit_handler(request: web_request.Request) -> web.Response:
    auth_key = request.match_info["authKey"]

    if not compo.get_week(True)["submissionsOpen"]:
        return web.Response(status=400,
                            text="Submissions are currently closed!")

    if keys.key_valid(auth_key, keys.edit_keys):
        key = keys.edit_keys[auth_key]

        entry = compo.get_entry_by_uuid(key["entryUUID"])

        form = get_edit_form_for_entry(entry, auth_key)
        html = submit_template.replace("[ENTRY-FORM]", form)
        html = html.replace("[ENTRANT-NAME]", entry["entrantName"])

        return web.Response(status=200, body=html, content_type="text/html")
    else:
        return web.Response(status=404, text="File not found")


async def admin_preview_handler(request: web_request.Request) -> web.Response:
    auth_key = request.match_info["authKey"]

    if not keys.key_valid(auth_key, keys.admin_keys):
        return web.Response(status=404, text="Invalid key")

    html = vote_template.replace("[WEEK-DATA]",
                                 json.dumps(get_week_viewer(True, True)))

    html = html.replace("[VUE-URL]", get_vue_url())

    return web.Response(text=html, content_type="text/html")


async def admin_viewvote_handler(request: web_request.Request) -> web.Response:
    auth_key = request.match_info["authKey"]
    user_id = request.match_info["userID"]

    if not keys.key_valid(auth_key, keys.admin_keys):
        return web.Response(status=401, text="Invalid key")


    week = compo.get_week(False)

    print("user_id: " + str(user_id))

    if not "votes" in week:
        week["votes"] = []

    for v in week["votes"]:
        if int(v["userID"]) == int(user_id):
            return web.Response(status=200,
                                body=json.dumps(v),
                                content_type="application/json")

    return web.Response(status=404, text="File not found")


async def admin_control_handler(request: web_request.Request) -> web.Response:
    auth_key = request.match_info["authKey"]

    if not keys.key_valid(auth_key, keys.admin_keys):
        return web.Response(status=404, text="File not found")

    this_week = compo.get_week(False)
    next_week = compo.get_week(True)

    data = await request.json()

    next_week["theme"] = data["weeks"][1]["theme"]
    next_week["date"] = data["weeks"][1]["date"]
    next_week["submissionsOpen"] = data["weeks"][1]["submissionsOpen"]

    this_week["theme"] = data["weeks"][0]["theme"]
    this_week["date"] = data["weeks"][0]["date"]
    this_week["votingOpen"] = data["weeks"][0]["votingOpen"]

    compo.save_weeks()
    return web.Response(status=204, text="Nice")


async def admin_archive_handler(request: web_request.Request) -> web.Response:
    auth_key = request.match_info["authKey"]

    if not keys.key_valid(auth_key, keys.admin_keys):
        return web.Response(status=404, text="File not found")

    compo.move_to_next_week()

    return web.Response(status=204, text="Nice")


async def admin_spoof_handler(request: web_request.Request) -> web.Response:
    auth_key = request.match_info["authKey"]

    if not keys.key_valid(auth_key, keys.admin_keys):
        return web.Response(status=404, text="File not found")

    entry_data = await request.json()

    compo.create_blank_entry(entry_data["entrantName"], entry_data["discordId"], entry_data["nextWeek"])

    return web.Response(status=204, text="Nice")


# TODO: JSON
async def file_post_handler(request: web_request.Request) -> web.Response:
    global config

    auth_key = request.match_info["authKey"]
    uuid = request.match_info["uuid"]

    user_authorized = (keys.key_valid(auth_key, keys.edit_keys)
                       and keys.edit_keys[auth_key]["entryUUID"] == uuid
                       and compo.get_week(True)["submissionsOpen"])

    is_admin = keys.key_valid(auth_key, keys.admin_keys)
    authorized = user_authorized or is_admin
    if not authorized:
        return web.Response(status=403, text="Not happening babe")

    # Find the entry
    choice = None
    for which_week in [True, False]:
        week = compo.get_week(which_week)

        for entryIndex, entry in enumerate(week["entries"]):
            if entry["uuid"] == uuid:
                choice = (week, entryIndex, entry)
                break

    if choice is None:
        return web.Response(status=400, text="That entry doesn't seem to exist")

    week, entryIndex, entry = choice

    # Process it
    reader = await request.multipart()
    if reader is None:
        return web.Response(status=400, text="Not happening babe")

    async for field in reader:
        if field.name == "entryName":
            entry["entryName"] = \
                (await field.read(decode=True)).decode("utf-8")
        elif (field.name == "entrantName"
              and keys.key_valid(auth_key, keys.admin_keys)):
            entry["entrantName"] = \
                (await field.read(decode=True)).decode("utf-8")
        elif (field.name == "entryNotes"
              and keys.key_valid(auth_key, keys.admin_keys)):
            entry["entryNotes"] = \
                (await field.read(decode=True)).decode("utf-8")
        elif (field.name == "deleteEntry"
              and keys.key_valid(auth_key, keys.admin_keys)):
            week["entries"].remove(entry)
            compo.save_weeks()
            return web.Response(status=200,
                                text="Entry successfully deleted.")
        elif field.name == "mp3Link":
            url = (await field.read(decode=True)).decode("utf-8")
            if len(url) > 1:
                entry["mp3"] = url
                entry["mp3Format"] = "external"
                entry["mp3Filename"] = ""
        elif field.name == "mp3" or field.name == "pdf":
            if field.filename == "":
                continue
            if not field.filename.endswith(field.name):
                errMsg = "Wrong file format! Expected %s" % field.name
                return web.Response(status=400, text=errMsg)

            size = 0
            entry[field.name] = None

            entry[field.name + "Filename"] = field.filename

            if field.name == "mp3":
                entry["mp3Format"] = "mp3"

            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                if size > 1000 * 1000 * 8:  # 8MB limit
                    entry[field.name] = None
                    entry[field.name + "Filename"] = None
                    return web.Response(status=413, text=too_big_text)
                if entry[field.name] is None:
                    entry[field.name] = chunk
                else:
                    entry[field.name] += chunk

    if not is_admin:
        # Move the entry to the end of the list
        week["entries"].append(week["entries"].pop(entryIndex))

    compo.save_weeks()

    await bot.submission_message(entry,
                                 keys.key_valid(auth_key, keys.admin_keys))

    if is_admin:
        return web.Response(status=303, headers={"Location": "%s/admin/%s" % (config["url_prefix"], auth_key)})

    thanks = thanks_template.replace("[HEADER]",
                          "Your entry has been recorded -- Good luck!")
    thanks = thanks.replace("[BODY]",
        "If you have any issues, "
        "let us know in #weekly-challenge-discussion, "
        "or DM one of our friendly moderators.")

    return web.Response(status=200,
                        body=thanks,  #TODO: Remove (Should be JSON).
                        content_type="text/html")


async def submit_vote_handler(request: web_request.Request) -> web.Response:
    vote_input = await request.json()

    auth_key = vote_input["voteKey"]

    if not keys.key_valid(auth_key, keys.vote_keys):
        return web.Response(status=403, text="Not happening babe")

    user_id = keys.vote_keys[auth_key]["userID"]
    user_name = keys.vote_keys[auth_key]["userName"]

    week = compo.get_week(False)

    if not "votes" in week:
        week["votes"] = []

    # If user has submitted a vote already, then remove it, so we can
    # replace it with the new one
    for v in week["votes"]:
        if int(v["userID"]) == int(user_id):
            week["votes"].remove(v)

    vote_data = {
        "ratings": vote_input["votes"],
        "userID": user_id,
        "userName": user_name
    }

    week["votes"].append(vote_data)

    compo.save_weeks()

    return web.Response(status=200, text="FRICK yeah")


# Helpers
# TODO: Vueify
def get_edit_form_for_entry(entry: dict, auth_key: str) -> str:
    post_url = "/edit/post/%s/%s" % (uuid, auth_key)

    form_class = "entry-form"

    html = "<form class='%s' action='%s' " % (form_class, post_url)
    html += ("method='post' accept-charset='utf-8' "
             "enctype='multipart/form-data'>")

    def html_input(entry_param, label, input_type, value):
        nonlocal html, entry

        html += "<div class='entry-param'>"
        html += "<label for='%s'>%s</label>" % (entry_param, label)
        html += "<input name='%s' type='%s' value='%s'/>" % (
            entry_param, input_type, value)
        html += "</div><br>"

    def param_if_exists(param):
        if param in entry:
            return entry[param]
        else:
            return ""

    html_input("entryName", "Entry Name", "text",
               html_lib.escape(entry["entryName"]))

    html_input("mp3", "Upload MP3", "file", "")

    link_label = ("Or, if you have an external link to your "
                  "submission (e.g. SoundCloud), you can "
                  "enter that here.")
    html_input("mp3Link", link_label, "text", "")

    html_input("pdf", "Upload PDF", "file", "")

    html += ("<input class='entry-param submit-button' "
             "type='submit' value='Submit Entry'/>")
    html += "</form>"

    return html


def get_week_viewer(which_week: bool, only_valid: bool) -> str:
    week = compo.get_week(which_week)

    entryData = []

    for e in week["entries"]:
        is_valid = compo.entry_valid(e)
        if only_valid and not is_valid:
            continue

        prunedEntry = {
            "uuid": e["uuid"],
            "pdfUrl": "/files/%s/%s" % (e["uuid"], e.get("pdfFilename")),
            "mp3Format": e.get("mp3Format"),
            "entryName": e["entryName"],
            "entrantName": e["entrantName"],
            "isValid": is_valid,
        }

        if e.get("mp3Format") == "mp3":
            prunedEntry["mp3Url"] = "/files/%s/%s" % \
                (e["uuid"], e["mp3Filename"])
        else:
            prunedEntry["mp3Url"] = e.get("mp3")

        # this data is just here for the benefit of the client
        for voteParam in ["votePrompt", "voteScore", "voteOverall"]:
            prunedEntry[voteParam] = 0

        entryData.append(prunedEntry)

    data = {
        "entries": entryData,
        "theme": week["theme"],
        "date": week["date"],
        "submissionsOpen": week["submissionsOpen"],
        "votingOpen": week["votingOpen"],
    }

    return data


def get_week_votes(which_week: bool) -> str:
    week = compo.get_week(which_week)

    if "votes" not in week:
        week["votes"] = []

    adaptedData = week["votes"].copy()

    # JavaScript is very silly and won't work if we send these huge
    # numbers as actual numbers, so we have to stringify them first
    for v in adaptedData:
        v["userID"] = str(v["userID"])

    return adaptedData


server = web.Application()

server.add_routes([
    web.get("/", vote_handler),
    web.get("/favicon.ico", favicon_handler),
    web.get("/files/{uuid}/{filename}", week_files_handler),
    web.get("/edit/{authKey}", edit_handler),
    web.get("/thanks", vote_thanks_handler),  #TODO: Remove
    web.get("/entry_data", get_entries_handler),
    web.get("/admin/{authKey}", admin_handler),
    web.get("/admin/get_admin_data/{authKey}", admin_get_data_handler),
    web.get("/admin/preview/{authKey}", admin_preview_handler),
    web.get("/admin/viewvote/{authKey}/{userID}", admin_viewvote_handler),
    web.post("/admin/edit/{authKey}", admin_control_handler),
    web.post("/admin/archive/{authKey}", admin_archive_handler),
    web.post("/admin/spoof/{authKey}", admin_spoof_handler),
    web.post("/edit/post/{uuid}/{authKey}", file_post_handler),
    web.post("/submit_vote", submit_vote_handler),
    web.static("/static", "static")
])


async def start_http(_config) -> None:
    global config
    config = _config

    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8251)
    await site.start()
    logging.info("HTTP: Started server")


if __name__ == "__main__":
    web.run_app(server)
