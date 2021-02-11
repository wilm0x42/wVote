#!/usr/bin/env python3

import datetime
import html as html_lib
import urllib.parse
import uuid
import logging
import json
from typing import Optional

import pickle

current_week = None
next_week = None


def get_week(get_next_week: bool) -> dict:
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
    global current_week, next_week

    if current_week is None:
        # current_week = json.loads(open("week.json", "r").read())
        try:
            current_week = pickle.load(open("weeks/current-week.pickle", "rb"))
        except FileNotFoundError:
            current_week = {
                "theme": "Week XYZ: Fill this in by hand!",
                "date": "Month day'th 20XX",
                "submissionsOpen": False,
                "entries": []
            }
    if next_week is None:
        try:
            next_week = pickle.load(open("weeks/next-week.pickle", "rb"))
        except FileNotFoundError:
            next_week = {
                "theme": "Week XYZ: Fill this in by hand!",
                "date": "Month day'th 20XX",
                "submissionsOpen": True,
                "entries": []
            }

    if get_next_week:
        return next_week
    else:
        return current_week


def save_weeks() -> None:
    """
    Saves `current_week` and `next_week` into pickle objects so that they can
    later be read again.
    """
    if current_week is not None and next_week is not None:
        # open("week.json", "w").write(json.dumps(current_week))
        pickle.dump(current_week, open("weeks/current-week.pickle", "wb"))
        pickle.dump(next_week, open("weeks/next-week.pickle", "wb"))
        logging.info("COMPO: current-week.pickle and next-week.pickle overwritten")


def move_to_next_week() -> None:
    """
    Replaces `current_week` with `next_week`, freeing up `next_week` to be
    replaced with new information.

    Calls `save_weeks()` to serialize the data after modification.
    """
    global current_week, next_week

    archive_filename = "weeks/archive/" + \
        datetime.datetime.now().strftime("%m-%d-%y") + ".pickle"
    pickle.dump(current_week, open(archive_filename, "wb"))

    current_week = next_week
    next_week = {
        "theme": "Week XYZ: Fill this in by hand!",
        "date": "Month day'th 20XX",
        "submissionsOpen": True,
        "entries": []
    }

    save_weeks()


def create_blank_entry(entrant_name: str,
                       discord_id: Optional[int],
                       get_next_week: bool = True) -> str:
    """
    Create a blank entry for an entrant and returns a UUID

    Parameters
    ----------
    entrant_name : str
        The name of the entrant
    discord_id : Optional[int]
        The entrant's Discord ID
    get_next_week : bool, optional
        Whether the entry should be for the folowing week, by default True

    Returns
    -------
    str
        A randomly generated UUID
    """
    entry = {
        "entryName": "",
        "entrantName": entrant_name,
        "discordID": discord_id,
        "uuid": str(uuid.uuid4())
    }
    get_week(get_next_week)["entries"].append(entry)

    return entry["uuid"]


def get_admin_form_for_entry(uuid: str, auth_key: str) -> str:
    for which_week in [True, False]:
        week = get_week(which_week)

        for entry in week["entries"]:
            if entry["uuid"] == uuid:
                post_url = "/edit/post/%s/%s" % (uuid, auth_key)

                form_class = "admin-entry-form"
                alert_header = ""
                header_color = "black"

                if which_week is True:
                    form_class = "form-next-week admin-entry-form"
                    alert_header = "Entry for NEXT week"
                else:
                    form_class = "form-current-week admin-entry-form"
                    alert_header = "Entry for CURRENT week"
                    header_color = "orange"

                if entry_valid(entry):
                    alert_header += " (valid)"
                else:
                    alert_header += " (invalid!)"
                    form_class = "form-invalid admin-entry-form"
                    header_color = "red"

                html = "<form class='%s' action='%s' " % (form_class, post_url)
                html += ("method='post' accept-charset='utf-8' "
                         "enctype='multipart/form-data'>")

                html += "<h3 style='color: %s;' " \
                        "onclick='foldForm(this.parentElement)'>%s</h3>" \
                    % (header_color, alert_header)

                def html_input(entry_param, label, input_type, value):
                    nonlocal html, entry

                    html += "<div class='admin-entry-param'>"
                    html += "<label for='%s'>%s</label>" % (entry_param, label)
                    html += "<input name='%s' type='%s' value='%s'/>" % (
                        entry_param, input_type, value)
                    html += "</div><br>"

                def show_file(which_file):
                    nonlocal html, entry

                    html += "<div class='admin-entry-param'>"

                    if (which_file + "Filename") in entry \
                            and entry[which_file + "Filename"] != None:
                        file_url = "/files/%s/%s" % \
                            (entry["uuid"],
                             urllib.parse.quote(entry[which_file + "Filename"]))
                        if which_file == "mp3":
                            if entry["mp3Format"] == "external":
                                file_url = entry["mp3"]

                        html += "<a href='%s'>Link to %s</a>" % (file_url,
                                                                 which_file)
                    else:
                        html += "<p>%s not uploaded.<p>" % which_file

                    html += "</div><br>"

                def param_if_exists(param):
                    if param in entry:
                        return entry[param]
                    else:
                        return ""

                html_input("entryName", "Entry Name", "text",
                           html_lib.escape(entry["entryName"]))
                html_input("entrantName", "Discord Username", "text",
                           html_lib.escape(entry["entrantName"]))
                html_input("entryNotes", "Additional Notes", "text",
                           html_lib.escape(param_if_exists("entryNotes")))

                show_file("mp3")
                html_input("mp3", "Upload MP3", "file", "")

                link_label = ("Or, if you have an external link to your "
                              "submission (e.g. SoundCloud), you can "
                              "enter that here.")
                html_input("mp3Link", link_label, "text", "")

                show_file("pdf")
                html_input("pdf", "Upload PDF", "file", "")

                html += "<div class='admin-entry-param'>"
                html += "<label for='deleteEntry'>Delete Entry</label>"
                html += ("<input type='checkbox' name='deleteEntry' "
                         "value='true'/>")
                html += "</div><br>"

                html += (
                    "<input class='admin-entry-param admin-submit-button' "
                    "type='submit' value='Submit Entry'/>")
                html += "</form>"

                return html

    return ("<p>I'm not sure how to tell you this, "
            "but that entry doesn't exist.</p>")


def get_edit_form_for_entry(uuid: str, auth_key: str) -> str:
    for which_week in [True, False]:
        week = get_week(which_week)

        for entry in week["entries"]:
            if entry["uuid"] == uuid:
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

    return ("<p>I'm not sure how to tell you this, "
            "but that entry doesn't exist.</p>")


def get_all_admin_forms(auth_key: str) -> str:
    html = ""

    for which_week in [True, False]:
        week = get_week(which_week)

        for entry in week["entries"]:
            try:
                html += get_admin_form_for_entry(entry["uuid"], auth_key)
            except Exception as e:
                logging.error("COMPO: Error in get_all_admin_forms: %s" % str(e))
                html += ("<h3>This entry seems to have caused an error, "
                         "so we can't display it.  Inform the nerds!</h3>")
                continue

    return html


def get_entrant_name(uuid: str) -> Optional[str]:
    for which_week in [True, False]:
        for entry in get_week(which_week)["entries"]:
            if entry["uuid"] == uuid:
                return entry["entrantName"]


def entry_valid(entry: dict) -> bool:
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

    for requirement in requirements:
        if requirement not in entry:
            return False

    for param in ["mp3", "pdf"]:
        if entry[param] is None:
            return False

    return True


def count_valid_entries(which_week: bool) -> int:
    count = 0

    for e in get_week(which_week)["entries"]:
        if entry_valid(e):
            count += 1

    return count


def get_entry_file(uuid: str, filename: str) -> tuple:
    for which_week in [True, False]:
        week = get_week(which_week)

        for entry in week["entries"]:

            def param_if_exists(param):
                nonlocal entry
                if param in entry:
                    return entry[param]
                else:
                    return ""

            if entry["uuid"] == uuid:
                if filename == param_if_exists("mp3Filename"):
                    return entry["mp3"], "audio/mpeg"
                elif filename == param_if_exists("pdfFilename"):
                    return entry["pdf"], "application/pdf"

    return None, None

def get_tablerow_for_entry(entry: dict) -> str:
    html = ""
    
    def add_node(tag: str, data: str) -> None:
        nonlocal html
        html += "<%s>%s</%s>" % (tag, data, tag)

    def add_td(data: str) -> None:
        add_node("td", data)
    
    html += "<tr>"

    add_td(html_lib.escape(entry["entrantName"]))
    
    add_td(html_lib.escape(entry["entryName"]))
    
    add_td(
        "<button onclick=\"viewPDF('/files/%s/%s')\">View PDF</button>" %
        (entry["uuid"], urllib.parse.quote(entry["pdfFilename"])))

    if entry["mp3Format"] == "mp3":
        mp3Url = "/files/%s/%s" % \
            (entry["uuid"],
             urllib.parse.quote(entry["mp3Filename"]))

        add_td("<audio controls>"
               "<source src=\"%s\" type=\"audio/mpeg\">"
               "<a href=\"%s\">mp3 link</a>"
               "</audio>" % (mp3Url, mp3Url))
    elif entry["mp3Format"] == "external":
        # TODO: embed soundcloud players
        # Sanitize url to prevent against bad times
        url = entry["mp3"]
        if url.startswith('http://'):
            sanitized = url[:7] + urllib.parse.quote(url[7:])
        elif url.startswith('https://'):
            sanitized = url[:8] + urllib.parse.quote(url[8:])
        else:
            sanitized = urllib.parse.quote(url)

        sanitized = sanitized.replace("%3F", "?")
        sanitized = sanitized.replace("%3D", "=")
        sanitized = sanitized.replace("%26", "&")

        # Check for soundcloud/bandcamp
        if "soundcloud.com" in sanitized:
            add_td("<a href=%s>Listen on SoundCloud</a>" % sanitized)
        elif "bandcamp.com" in sanitized:
            add_td("<a href=%s>Listen on Bandcamp</a>" % sanitized)
        else:
            add_td("<a href=%s>Listen here!</a>" % sanitized)
    else:
        add_td("Audio format not recognized D:")

    html += "</tr>"
    
    return html

def get_vote_controls_for_week(which_week: bool) -> str:
    w = get_week(which_week)

    html = "<h2 class=\"week-title\">%s</h2>" % html_lib.escape(w["theme"])

    html += "<h3 class=\"week-subtitle\">%s - %d entries</h3>" % (
        html_lib.escape(w["date"]), count_valid_entries(which_week))

    html += "<table cellpadding='0' class='vote-controls'>\n"

    def add_node(tag: str, data: str) -> None:
        nonlocal html
        html += "<%s>%s</%s>" % (tag, data, tag)

    html += "<tr>"
    add_node("th", "Entrant")
    add_node("th", "Composition Title")
    add_node("th", "PDF")
    add_node("th", "MP3")
    html += "</tr>"

    for entry in w["entries"]:

        if not entry_valid(entry):
            continue
        
        html += get_tablerow_for_entry(entry)

    html += "</table>"

    return html
