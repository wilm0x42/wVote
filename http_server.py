#!/usr/bin/env python3

import datetime
import html as html_lib
import string
import random

from aiohttp import web

import compo

vote_template = open("vote.html", "r").read()
submit_template = open("submit.html", "r").read()
submit_success = open("submitted.html", "r").read()
admin_template = open("admin.html", "r").read()

favicon = open("static/favicon.ico", "rb").read()

server_domain = "8bitweekly.xyz"

too_big_text = """
File too big! We can only upload to discord files 8MB or less.
You can alternatively upload to SoundCloud or Clyp or something,
and provide us with a link. If you need help, ask us in
#weekly-challenge-discussion.
"""

edit_keys = {
    # "a1b2c3d4":
    # {
    # 	"entryUUID": "cf56f9c3-e81f-43b0-b16b-de2144b54b02",
    # 	"creationTime": datetime.datetime.now(),
    # 	"timeToLive": 200
    # }
}

admin_keys = {
    # "a1b2c3d4":
    # {
    # 	"creationTime": datetime.datetime.now(),
    # 	"timeToLive": 200
    # }
}


def key_valid(key, keystore):
    if key not in keystore:
        return False

    now = datetime.datetime.now()
    ttl = datetime.timedelta(minutes=int(keystore[key]["timeToLive"]))

    if now - keystore[key]["creationTime"] < ttl:
        return True
    else:
        keystore.pop(key)
        return False


def create_key(length=8):
    key_characters = string.ascii_letters + string.digits
    key = ''.join(random.SystemRandom().choice(key_characters)
                  for _ in range(8))
    return key


def create_edit_key(entry_uuid):
    key = create_key()

    edit_keys[key] = {
        "entryUUID": entry_uuid,
        "creationTime": datetime.datetime.now(),
        "timeToLive": 30
    }

    return key


def create_admin_key():
    key = create_key()

    admin_keys[key] = {
        "creationTime": datetime.datetime.now(),
        "timeToLive": 30
    }

    return key


def get_admin_controls(auth_key):
    this_week = compo.get_week(False)
    next_week = compo.get_week(True)

    html = ""

    def text_field(field, label, value):
        nonlocal html
        html += "<form action='/admin/edit/%s' " % auth_key
        html += ("onsubmit='setTimeout(function()"
                 "{window.location.reload();},100);' ")
        html += ("method='post' accept-charset='utf-8' "
                 "enctype='application/x-www-form-urlencoded'>")

        html += "<label for='%s'>%s</label>" % (field, label)
        html += "<input name='%s' type='text' value='%s' />" % (
            field, html_lib.escape(value))
        html += "<input type='submit' value='Submit'/>"
        html += "</form><br>"

    text_field("currentWeekTheme",
               "Theme/title of current week", this_week["theme"])
    text_field("currentWeekDate", "Date of current week", this_week["date"])
    text_field("nextWeekTheme", "Theme/title of next week", next_week["theme"])
    text_field("nextWeekDate", "Date of next week", next_week["date"])

    if compo.get_week(True)["submissionsOpen"]:
        html += "<p>Submissions are currently OPEN</p>"
    else:
        html += "<p>Submissions are currently CLOSED</p>"

    # TODO: This is all html code, so it should probably go in a .html ;P

    html += "<form action='/admin/edit/%s' " % auth_key
    html += "onsubmit='setTimeout(function(){window.location.reload();},100);' "
    html += ("method='post' accept-charset='utf-8' "
             "enctype='application/x-www-form-urlencoded'>")
    html += "<label for='submissionsOpen'>Submissions Open</label>"
    html += "<input type='radio' name='submissionsOpen' value='Yes'>"
    html += "<label for='Yes'>Yes</label>"
    html += "<input type='radio' name='submissionsOpen' value='No'>"
    html += "<label for='No'>No</label>"
    html += "<input type='submit' value='Submit'/>"
    html += "</form><br>"

    html += ("<form style='border: 1px solid black;' action='/admin/edit/%s' "
             % auth_key)
    html += "onsubmit='setTimeout(function(){window.location.reload();},100);' "
    html += ("(method='post' accept-charset='utf-8'"
             "enctype='application/x-www-form-urlencoded'>")
    html += "<label>Force create an entry</label><br>"
    html += "<label for='newEntryEntrant'>Spoofed entrant name</label>"
    html += ("<input type='text' name='newEntryEntrant' "
             "value='Wiglaf'><br>")
    html += ("<label for='newEntryDiscordID'>(Optional) "
             "Spoofed entrant discord ID</label>")
    html += "<input type='text' name='newEntryDiscordID' value=''><br>"
    html += ("<label for='newEntryWeek'>Place entry in current week "
             "instead of next week?</label>")
    html += "<input type='checkbox' name='newEntryWeek' value='on'><br>"
    html += "<input type='submit' value='Submit'/>"
    html += "</form><br>"

    html += "<form action='/admin/edit/%s' " % auth_key
    html += "onsubmit='setTimeout(function(){window.location.reload();},100);' "
    html += ("method='post' accept-charset='utf-8' "
             "enctype='application/x-www-form-urlencoded'>")
    html += ("<label for='rolloutWeek'>Archive current week, "
             "and make next week current</label>")
    html += "<input type='checkbox' name='rolloutWeek' value='on'>"
    html += "<input type='submit' value='Submit'/>"
    html += "</form>"

    return html


async def admin_control_handler(request):
    auth_key = request.match_info["authKey"]

    if key_valid(auth_key, admin_keys):
        this_week = compo.get_week(False)
        next_week = compo.get_week(True)

        data = await request.post()

        def data_param(week, param, field):
            nonlocal data

            if field in data:
                week[param] = data[field]

        data_param(this_week, "theme", "currentWeekTheme")
        data_param(this_week, "date", "currentWeekDate")
        data_param(next_week, "theme", "nextWeekTheme")
        data_param(next_week, "date", "nextWeekDate")

        if "submissionsOpen" in data:
            if data["submissionsOpen"] == "Yes":
                compo.get_week(True)["submissionsOpen"] = True
            if data["submissionsOpen"] == "No":
                compo.get_week(True)["submissionsOpen"] = False

        if "rolloutWeek" in data:
            if data["rolloutWeek"] == "on":
                compo.move_to_next_week()

        if "newEntryEntrant" in data:
            new_entry_week = True
            if "newEntryWeek" in data:
                new_entry_week = False

            new_entry_discord_id = None
            if "newEntryDiscordID" in data:
                if data["newEntryDiscordID"] != "":
                    try:
                        new_entry_discord_id = int(data["newEntryDiscordID"])
                    except ValueError:
                        new_entry_discord_id = None

            compo.create_blank_entry(data["newEntryEntrant"],
                                     new_entry_discord_id,
                                     new_entry_week)
        compo.save_weeks()
        return web.Response(status=204, text="Nice")
    else:
        return web.Response(status=404, text="File not found")


async def vote_handler(request):
    html = None

    html = vote_template.replace(
        "[VOTE-CONTROLS]", compo.get_vote_controls_for_week(False))

    return web.Response(text=html, content_type="text/html")


async def week_files_handler(request):
    data, content_type = compo.get_entry_file(request.match_info["uuid"],
                                              request.match_info["filename"])

    if not data:
        return web.Response(status=404, text="File not found")

    return web.Response(status=200, body=data, content_type=content_type)


async def favicon_handler(request):
    return web.Response(body=favicon)


async def edit_handler(request):
    authKey = request.match_info["authKey"]

    if not compo.get_week(True)["submissionsOpen"]:
        return web.Response(status=404,
                            text="Submissions are currently closed!")

    if key_valid(authKey, edit_keys):
        key = edit_keys[authKey]

        form = compo.get_edit_form_for_entry(key["entryUUID"], authKey)
        html = submit_template.replace("[ENTRY-FORM]", form)
        html = html.replace(
            "[ENTRANT-NAME]", compo.get_entrant_name(key["entryUUID"]))

        return web.Response(status=200, body=html, content_type="text/html")
    else:
        return web.Response(status=404, text="File not found")


async def admin_handler(request):
    auth_key = request.match_info["authKey"]

    if key_valid(auth_key, admin_keys):
        key = admin_keys[auth_key]

        html = admin_template.replace(
            "[ENTRY-LIST]", compo.get_all_entry_forms(auth_key))
        html = html.replace("[VOTE-CONTROLS]",
                            compo.get_vote_controls_for_week(True))
        html = html.replace("[ADMIN-CONTROLS]", get_admin_controls(auth_key))

        return web.Response(status=200, body=html, content_type="text/html")
    else:
        return web.Response(status=404, text="File not found")


# TODO: Refactor this function
async def file_post_handler(request):
    auth_key = request.match_info["authKey"]
    uuid = request.match_info["uuid"]

    if (key_valid(auth_key, edit_keys)
        and edit_keys[auth_key]["entryUUID"] == uuid
        and compo.get_week(True)["submissionsOpen"]) \
            or key_valid(auth_key, admin_keys):
        for which_week in [True, False]:
            week = compo.get_week(which_week)

            for entry in week["entries"]:
                if entry["uuid"] != uuid:
                    continue

                reader = await request.multipart()

                if reader is None:
                    return web.Response(status=400, text="Not happening babe")

                while True:
                    field = await reader.next()

                    if field is None:
                        break

                    if field.name == "entryName":
                        entry["entryName"] = \
                            (await field.read(decode=True)).decode("utf-8")
                    elif (field.name == "entrantName"
                          and key_valid(auth_key, admin_keys)):
                        entry["entrantName"] = \
                            (await field.read(decode=True)).decode("utf-8")
                    elif (field.name == "entryNotes"
                          and key_valid(auth_key, admin_keys)):
                        entry["entryNotes"] = \
                            (await field.read(decode=True)).decode("utf-8")

                    elif (field.name == "deleteEntry"
                          and key_valid(auth_key, admin_keys)):
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

                            if size > 1024 * 1024 * 8:  # 8MB limit
                                entry[field.name] = None
                                entry[field.name + "Filename"] = None
                                return web.Response(status=413,
                                                    text=too_big_text)

                            if entry[field.name] is None:
                                entry[field.name] = chunk
                            else:
                                entry[field.name] += chunk

                compo.save_weeks()
                return web.Response(status=200,
                                    body=submit_success,
                                    content_type="text/html")

        return web.Response(status=400, text="That entry doesn't seem to exist")

    else:
        return web.Response(status=403, text="Not happening babe")

# async def debug_handler(request):
#   cmd = request.match_info["command"]

#   if cmd == "save":
#       compo.save_weeks()

#   return web.Response(status=200, text="Nice.")

# for member in bot.client.guilds[0].members:

# async def yeet_handler(request):
#   await bot.client.get_channel(720055562573840384).send("yeet yate yote")
#   return web.Response(text="lmao")

server = web.Application()

server.add_routes([web.get("/", vote_handler),
                   web.get("/files/{uuid}/{filename}", week_files_handler),
                   web.get("/favicon.ico", favicon_handler),
                   web.get("/edit/{authKey}", edit_handler),
                   web.get("/admin/{authKey}", admin_handler),
                   web.post("/admin/edit/{authKey}", admin_control_handler),
                   web.post("/edit/post/{uuid}/{authKey}", file_post_handler),
                   # web.get("/debug/{command}", debug_handler),
                   web.static("/static", "static")
                   ])


async def start_http():
    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8251)
    await site.start()
    print("HTTP: Started server")

if __name__ == "__main__":
    web.run_app(server)
