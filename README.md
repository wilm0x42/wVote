# wVote

Voting time!

## Install

On the server host:

* `sudo python3 -m pip install discord.py`
* `sudo python3 -m pip install aiohttp`

From home:

* `deploy.sh <user@remotehost>`

## bot.conf

bot.conf expects the following parameters:

* `command_prefix=`: this sets the string that is to precede all discord commands
* `bot_key=`: This is your bot key for the discord API
* `admin=`: This is the discord ID of someone who should be an "admin" in wVote. You can put several of these, each on its own line.

Lines that start with a # will be ignored.

## Data Structure of a Week:

```
root
|- "theme": Title of week, e.g. "Week 23: Test Drive"
|- "date": Pretty display of week's date: "June 27th 2020"
|- "submissionsOpen": whether or not !submit is allowed
'- "entries": List of submitted entries for this week
	|- "pdf": byte data of PDF
	|- "pdfFilename": Name of PDF file
	|-mp3: byte data of MP3, or URL to soundcloud/whatever
	|-mp3Format: "mp3" if is raw mp3 file, or "external" if is simply to be linked to.
	|	TODO: Support specific "soundcloud" format, so we can embed SC players in the page
	|-entryName: Formal title of this entry
	|-entrantName: Entrant's discord username. Can be edited by admins.
	|-discordID: Entrant's discord ID
	'-uuid: UUID assigned to each entry, so they can be unambiguously addressed.
```

## Workflow:

!submit

* Anyone can use this command, but only in DMs
* Bot will reply with a secret link to a submission form
* If an existing entry is found for this user in the same week, the user can revise their submission
* Only inputs are "Entry Name" and the MP3 and PDF

!manage

* Only "admins" (mods/admins in the 8bmt discord) can use this, and also only in DMs
* Bot will reply with a secret link to an administrative management interface
* This is where everything is staged and prepared for posting

!postentries

* Post entries from current week into #weekly-challenge, pinging each entrant