#!/usr/bin/env python3

import datetime
import json
import uuid
import html as htmlLib

try:
    import cPickle as pickle
except:
    import pickle

currentWeek = None
nextWeek = None

def getWeek(next):
    global currentWeek, nextWeek

    if currentWeek == None:
        #currentWeek = json.loads(open("week.json", "r").read())
        try:
            currentWeek = pickle.load(open("weeks/current-week.pickle", "rb"))
        except FileNotFoundError:
            currentWeek = {
                "theme": "Week XYZ: Fill this in by hand!",
                "date": "Month day'th 20XX",
                "submissionsOpen": False,
                "entries": []
            }
    if nextWeek == None:
        try:
            nextWeek = pickle.load(open("weeks/next-week.pickle", "rb"))
        except FileNotFoundError:
            nextWeek = {
                "theme": "Week XYZ: Fill this in by hand!",
                "date": "Month day'th 20XX",
                "submissionsOpen": True,
                "entries": []
            }

    if next:
        return nextWeek
    else:
        return currentWeek

def saveWeeks():
    if currentWeek != None and nextWeek != None:
        #open("week.json", "w").write(json.dumps(currentWeek))
        pickle.dump(currentWeek, open("weeks/current-week.pickle", "wb"))
        pickle.dump(nextWeek, open("weeks/next-week.pickle", "wb"))
        print("COMPO: current-week.pickle and next-week.pickle overwritten")

def moveToNextWeek():
    global currentWeek, nextWeek

    archiveFilename = "weeks/archive/" + datetime.datetime.now().strftime("%m-%d-%y") + ".pickle"
    pickle.dump(currentWeek, open(archiveFilename, "wb"))

    currentWeek = nextWeek
    nextWeek = {
        "theme": "Week XYZ: Fill this in by hand!",
        "date": "Month day'th 20XX",
        "submissionsOpen": True,
        "entries": []
    }

    saveWeeks()

def createBlankEntry(entrantName, discordID, whichWeek=True):
    entry = {
        "entryName": "",
        "entrantName": entrantName,
        "discordID": discordID,
        "uuid": str(uuid.uuid4())
    }
    getWeek(whichWeek)["entries"].append(entry)

    return entry["uuid"]

def getEditFormForEntry(uuid, authKey, admin=False):
    for whichWeek in [True, False]:
        w = getWeek(whichWeek)

        for entry in w["entries"]:
            if entry["uuid"] == uuid:
                postUrl = "/edit/post/%s/%s" % (uuid, authKey)

                formClass = "entry-form"
                alertHeader = ""

                if admin:
                    if whichWeek == True:
                        formClass = "form-next-week entry-form"
                        alertHeader = "=== Entry for next week ==="
                    else:
                        formClass = "form-current-week entry-form"
                        alertHeader = "=== ENTRY FOR CURRENT WEEK ==="

                    if entryValid(entry):
                        alertHeader += " (valid)"
                    else:
                        alertHeader += " (invalid!)"

                html = "<form class='%s' action='%s' " % (formClass, postUrl)
                html += "method='post' accept-charset='utf-8' enctype='multipart/form-data'>"

                if admin:
                    html += "<h3>%s</h3>" % alertHeader

                def htmlInput(entryParam, label, inputType, value):
                    nonlocal html, entry

                    html += "<div class='entry-param'>"
                    html += "<label for='%s'>%s</label>" % (entryParam, label)
                    html += "<input name='%s' type='%s' value='%s'/>" % (entryParam, inputType, value)
                    html += "</div><br>"

                def showFile(whichFile):
                    nonlocal html, entry, admin

                    if not admin:
                        return

                    html += "<div class='entry-param'>"

                    if (whichFile + "Filename") in entry:
                        fileUrl = "/files/%s/%s" % (entry["uuid"], entry[whichFile + "Filename"])
                        html += "<a href=%s>Link to %s</a>" % (fileUrl, whichFile)
                    else:
                        html += "<p>%s not uploaded.<p>" % whichFile

                    html += "</div><br>"

                def paramIfExists(param):
                    if param in entry:
                        return entry[param]
                    else:
                        return ""

                htmlInput("entryName", "Entry Name", "text", htmlLib.escape(entry["entryName"]))

                if admin:
                    htmlInput("entrantName", "Discord Username", "text", htmlLib.escape(entry["entrantName"]))
                    htmlInput("entryNotes", "Additional Notes", "text", htmlLib.escape(paramIfExists("entryNotes")))

                showFile("mp3")
                htmlInput("mp3", "Upload MP3", "file", "")

                linkLabel = "Or, if you have an external link to your submission (e.g. SoundCloud), you can enter that here."
                htmlInput("mp3Link", linkLabel, "text", "")

                showFile("pdf")
                htmlInput("pdf", "Upload PDF", "file", "")

                if admin:
                    html += "<div class='entry-param'>"
                    html += "<label for='deleteEntry'>Delete Entry</label>"
                    html += "<input type='checkbox' name='deleteEntry' value='true'/>"
                    html += "</div><br>"

                html += "<input class='entry-param submit-button' type='submit' value='Submit Entry'/>"
                html += "</form>"

                return html

    return "<p>I'm not sure how to tell you this, but that entry doesn't exist.</p>"

def getAllEntryForms(authKey):
    html = ""

    for whichWeek in [True, False]:
        w = getWeek(whichWeek)

        for entry in w["entries"]:
            html += getEditFormForEntry(entry["uuid"], authKey, admin=True)

    return html

def getEntrantName(uuid):
    for whichWeek in [True, False]:
        for e in getWeek(whichWeek)["entries"]:
            if e["uuid"] == uuid:
                return e["entrantName"]

def entryValid(e):
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

    for req in requirements:
        if not req in e:
            return False

    for param in ["mp3", "pdf"]:
        if e[param] == None:
            return False

    return True

def countValidEntries(whichWeek):
    count = 0

    for e in getWeek(whichWeek)["entries"]:
        if entryValid(e):
            count += 1

    return count

def getEntryFile(uuid, filename):
    for whichWeek in [True, False]:
        w = getWeek(whichWeek)

        for e in w["entries"]:
            if e["uuid"] == uuid:
                if False: #not entryValid(e):
                    return None, None
                elif filename == e["mp3Filename"]:
                    return e["mp3"], "audio/mpeg"
                elif filename == e["pdfFilename"]:
                    return e["pdf"], "application/pdf"

    return None, None

def getVoteControlsForWeek(whichWeek):
    w = getWeek(whichWeek)

    html = "<h2 class=\"week-title\">%s</h2>" % htmlLib.escape(w["theme"])

    html += "<h3 class=\"week-subtitle\">%s - %d entries</h3>" % (htmlLib.escape(w["date"]), countValidEntries(whichWeek))

    html += "<table cellpadding='0' class='vote-controls'>\n"

    def addNode(tag, data):
        nonlocal html
        html += "<%s>%s</%s>" % (tag, data, tag)
    def th(data):
        addNode("th", data)
    def td(data):
        addNode("td", data)

    html += "<tr>"
    th("Entrant")
    th("Composition Title")
    th("PDF")
    th("MP3")
    html += "</tr>"

    for entry in w["entries"]:

        if not entryValid(entry):
            continue

        html += "<tr>"

        td(htmlLib.escape(entry["entrantName"]))
        td(htmlLib.escape(entry["entryName"]))
        td("<button onclick=\"viewPDF('/files/%s/%s')\">View PDF</button>" % (entry["uuid"], entry["pdfFilename"]))

        if entry["mp3Format"] == "mp3":
            mp3Url = "/files/%s/%s" % (entry["uuid"], entry["mp3Filename"])

            td( "<audio controls>"
                "<source src=\"%s\" type=\"audio/mpeg\">"
                "<a href=\"%s\">mp3 link</a>"
                "</audio>"
                % (mp3Url, mp3Url))
        elif entry["mp3Format"] == "external":
            if "soundcloud.com" in entry["mp3"]: # TODO: embed soundcloud players
                td("<a href=%s>Listen on SoundCloud</a>" % htmlLib.escape(entry["mp3"]))
            else:
                td("<a href=%s>Listen here!</a>" % htmlLib.escape(entry["mp3"]))
        else:
            td("Audio format not recognized D:")

        html += "</tr>"

    html += "</table>"

    return html