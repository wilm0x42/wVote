#!/usr/bin/env python3

import datetime
import uuid
import html as html_lib

try:
    import cPickle as pickle
except:
    import pickle

current_week = None
next_week = None


def get_week(get_next_week):
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


def save_weeks():
    if current_week is not None and next_week is not None:
        # open("week.json", "w").write(json.dumps(current_week))
        pickle.dump(current_week, open("weeks/current-week.pickle", "wb"))
        pickle.dump(next_week, open("weeks/next-week.pickle", "wb"))
        print("COMPO: current-week.pickle and next-week.pickle overwritten")


def move_to_next_week():
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


def create_blank_entry(entrant_name, discord_id, get_next_week=True):
    entry = {
        "entryName": "",
        "entrantName": entrant_name,
        "discordID": discord_id,
        "uuid": str(uuid.uuid4())
    }
    get_week(get_next_week)["entries"].append(entry)

    return entry["uuid"]


def get_edit_form_for_entry(uuid, auth_key, admin=False):
    for which_week in [True, False]:
        w = get_week(which_week)

        for entry in w["entries"]:
            if entry["uuid"] == uuid:
                post_url = "/edit/post/%s/%s" % (uuid, auth_key)

                form_class = "entry-form"
                alert_header = ""

                if admin:
                    if which_week is True:
                        form_class = "form-next-week entry-form"
                        alert_header = "=== Entry for next week ==="
                    else:
                        form_class = "form-current-week entry-form"
                        alert_header = "=== ENTRY FOR CURRENT WEEK ==="

                    if entry_valid(entry):
                        alert_header += " (valid)"
                    else:
                        alert_header += " (invalid!)"

                html = "<form class='%s' action='%s' " % (form_class, post_url)
                html += "method='post' accept-charset='utf-8' enctype='multipart/form-data'>"

                if admin:
                    html += "<h3>%s</h3>" % alert_header

                def html_input(entry_param, label, input_type, value):
                    nonlocal html, entry

                    html += "<div class='entry-param'>"
                    html += "<label for='%s'>%s</label>" % (entry_param, label)
                    html += "<input name='%s' type='%s' value='%s'/>" % (
                        entry_param, input_type, value)
                    html += "</div><br>"

                def show_file(which_file):
                    nonlocal html, entry, admin

                    if not admin:
                        return

                    html += "<div class='entry-param'>"

                    if (which_file + "Filename") in entry:
                        file_url = "/files/%s/%s" % (entry["uuid"],
                                                    entry[which_file + "Filename"])
                        html += "<a href=%s>Link to %s</a>" % (
                            file_url, which_file)
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

                if admin:
                    html_input("entrantName", "Discord Username",
                              "text", html_lib.escape(entry["entrantName"]))
                    html_input("entryNotes", "Additional Notes", "text",
                              html_lib.escape(param_if_exists("entryNotes")))

                show_file("mp3")
                html_input("mp3", "Upload MP3", "file", "")

                link_label = "Or, if you have an external link to your submission (e.g. SoundCloud), you can enter that here."
                html_input("mp3Link", link_label, "text", "")

                show_file("pdf")
                html_input("pdf", "Upload PDF", "file", "")

                if admin:
                    html += "<div class='entry-param'>"
                    html += "<label for='deleteEntry'>Delete Entry</label>"
                    html += "<input type='checkbox' name='deleteEntry' value='true'/>"
                    html += "</div><br>"

                html += "<input class='entry-param submit-button' type='submit' value='Submit Entry'/>"
                html += "</form>"

                return html

    return "<p>I'm not sure how to tell you this, but that entry doesn't exist.</p>"


def get_all_entry_forms(auth_key):
    html = ""

    for which_week in [True, False]:
        w = get_week(which_week)

        for entry in w["entries"]:
            html += get_edit_form_for_entry(entry["uuid"], auth_key, admin=True)

    return html


def get_entrant_name(uuid):
    for which_week in [True, False]:
        for entry in get_week(which_week)["entries"]:
            if entry["uuid"] == uuid:
                return entry["entrantName"]


def entry_valid(entry):
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


def count_valid_entries(which_week):
    count = 0

    for e in get_week(which_week)["entries"]:
        if entry_valid(e):
            count += 1

    return count


def get_entry_file(uuid, filename):
    for which_week in [True, False]:
        week = get_week(which_week)

        for entry in week["entries"]:
            if entry["uuid"] == uuid:
                if False:  # not entryValid(e):
                    return None, None
                elif filename == entry["mp3Filename"]:
                    return entry["mp3"], "audio/mpeg"
                elif filename == entry["pdfFilename"]:
                    return entry["pdf"], "application/pdf"

    return None, None


def get_vote_controls_for_week(which_week):
    w = get_week(which_week)

    html = "<h2 class=\"week-title\">%s</h2>" % html_lib.escape(w["theme"])

    html += "<h3 class=\"week-subtitle\">%s - %d entries</h3>" % (
        html_lib.escape(w["date"]), count_valid_entries(which_week))

    html += "<table cellpadding='0' class='vote-controls'>\n"

    def add_node(tag, data):
        nonlocal html
        html += "<%s>%s</%s>" % (tag, data, tag)

    def add_th(data):
        add_node("th", data)

    def add_td(data):
        add_node("td", data)

    html += "<tr>"
    add_th("Entrant")
    add_th("Composition Title")
    add_th("PDF")
    add_th("MP3")
    html += "</tr>"

    for entry in w["entries"]:

        if not entry_valid(entry):
            continue

        html += "<tr>"

        add_td(html_lib.escape(entry["entrantName"]))
        add_td(html_lib.escape(entry["entryName"]))
        add_td("<button onclick=\"viewPDF('/files/%s/%s')\">View PDF</button>" %
           (entry["uuid"], entry["pdfFilename"]))

        if entry["mp3Format"] == "mp3":
            mp3Url = "/files/%s/%s" % (entry["uuid"], entry["mp3Filename"])

            add_td("<audio controls>"
                "<source src=\"%s\" type=\"audio/mpeg\">"
                "<a href=\"%s\">mp3 link</a>"
                "</audio>"
                % (mp3Url, mp3Url))
        elif entry["mp3Format"] == "external":
            # TODO: embed soundcloud players
            if "soundcloud.com" in entry["mp3"]:
                add_td("<a href=%s>Listen on SoundCloud</a>" %
                   html_lib.escape(entry["mp3"]))
            else:
                add_td("<a href=%s>Listen here!</a>" %
                   html_lib.escape(entry["mp3"]))
        else:
            add_td("Audio format not recognized D:")

        html += "</tr>"

    html += "</table>"

    return html
