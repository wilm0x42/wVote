#!/usr/bin/env python3

import datetime
import asyncio
import html as htmlLib
import string
import random

from aiohttp import web

import bot
import compo

voteTemplate = open("vote.html", "r").read()
submitTemplate = open("submit.html", "r").read()
submitSuccess = open("submitted.html", "r").read()
adminTemplate = open("admin.html", "r").read()

favicon = open("static/favicon.ico", "rb").read()

serverDomain = "8bitweekly.xyz"

editKeys = {
	#"a1b2c3d4":
	#{
	#	"entryUUID": "cf56f9c3-e81f-43b0-b16b-de2144b54b02",
	#	"creationTime": datetime.datetime.now(),
	#	"timeToLive": 200
	#}
}

adminKeys = {
	#"a1b2c3d4":
	#{
	#	"creationTime": datetime.datetime.now(),
	#	"timeToLive": 200
	#}
}

def keyValid(key, keystore):
	if not key in keystore:
		return False

	now = datetime.datetime.now()
	ttl = datetime.timedelta(minutes=int(keystore[key]["timeToLive"]))
		
	if now - keystore[key]["creationTime"] < ttl:
		return True
	else:
		keystore.pop(key)
		return False

def createEditKey(entryUUID):
	keyCharacters = string.ascii_uppercase + string.ascii_lowercase + string.digits
	key = ''.join(random.SystemRandom().choice(keyCharacters) for _ in range(8))
	
	editKeys[key] = {
		"entryUUID": entryUUID,
		"creationTime": datetime.datetime.now(),
		"timeToLive": 30
	}
	
	return key

def createAdminKey():
	keyCharacters = string.ascii_uppercase + string.ascii_lowercase + string.digits
	key = ''.join(random.SystemRandom().choice(keyCharacters) for _ in range(8))
	
	adminKeys[key] = {
		"creationTime": datetime.datetime.now(),
		"timeToLive": 30
	}
	
	return key

def getAdminControls(authKey):
	thisWeek = compo.getWeek(False)
	nextWeek = compo.getWeek(True)
	
	html = ""
	
	def textField(field, label, value):
		nonlocal html
		html += "<form action='/admin/edit/%s' " % authKey
		html += "onsubmit='setTimeout(function(){window.location.reload();},100);' "
		html += "method='post' accept-charset='utf-8' enctype='application/x-www-form-urlencoded'>"
		
		html += "<label for='%s'>%s</label>" % (field, label)
		html += "<input name='%s' type='text' value='%s' />" % (field, htmlLib.escape(value))
		html += "<input type='submit' value='Submit'/>"
		html += "</form><br>"
	
	textField("currentWeekTheme", "Theme/title of current week", thisWeek["theme"])
	textField("currentWeekDate", "Date of current week", thisWeek["date"])
	textField("nextWeekTheme", "Theme/title of next week", nextWeek["theme"])
	textField("nextWeekDate", "Date of next week", nextWeek["date"])
	
	if compo.submissionsOpen:
		html += "<p>Submissions are currently OPEN</p>"
	else:
		html += "<p>Submissions are currently CLOSED</p>"
	
	html += "<form action='/admin/edit/%s' " % authKey
	html += "onsubmit='setTimeout(function(){window.location.reload();},100);' "
	html += "method='post' accept-charset='utf-8' enctype='application/x-www-form-urlencoded'>"
	html += "<label for='submissionsOpen'>Submissions Open</label>"
	html += "<input type='radio' name='submissionsOpen' value='Yes'>"
	html += "<label for='Yes'>Yes</label>"
	html += "<input type='radio' name='submissionsOpen' value='No'>"
	html += "<label for='No'>No</label>"
	html += "<input type='submit' value='Submit'/>"
	html += "</form><br>"
	
	html += "<form action='/admin/edit/%s' " % authKey
	html += "onsubmit='setTimeout(function(){window.location.reload();},100);' "
	html += "method='post' accept-charset='utf-8' enctype='application/x-www-form-urlencoded'>"
	html += "<label for='rolloutWeek'>Archive current week, and make next week current</label>"
	html += "<input type='checkbox' name='rolloutWeek' value='do it'>"
	html += "<input type='submit' value='Submit'/>"
	html += "</form>"
	
	return html

async def admin_control_handler(request):
	authKey = request.match_info["authKey"]
	
	if keyValid(authKey, adminKeys):
		thisWeek = compo.getWeek(False)
		nextWeek = compo.getWeek(True)
		
		data = await request.post()
		
		def dataParam(week, param, field):
			nonlocal data
			
			if field in data:
				week[param] = data[field]
		
		dataParam(thisWeek, "theme", "currentWeekTheme")
		dataParam(thisWeek, "date", "currentWeekDate")
		dataParam(nextWeek, "theme", "nextWeekTheme")
		dataParam(nextWeek, "date", "nextWeekDate")
		
		if "submissionsOpen" in data:
			if data["submissionsOpen"] == "Yes":
				compo.submissionsOpen = True
			if data["submissionsOpen"] == "No":
				compo.submissionsOpen = False
		
		if "rolloutWeek" in data:
			if data["rolloutWeek"] == "do it":
				compo.moveToNextWeek()
		
		compo.saveWeeks()
		return web.Response(status=204, text="Nice")
	else:
		return web.Response(status=404, text="File not found")

async def vote_handler(request):
	html = None
	
	html = voteTemplate.replace("[VOTE-CONTROLS]", compo.getVoteControlsForWeek(False))
	
	return web.Response(text=html, content_type="text/html")

async def week_files_handler(request):
	data, contentType = compo.getEntryFile(request.match_info["uuid"], request.match_info["filename"])
	
	if not data:
		return web.Response(status=404, text="File not found")
	
	return web.Response(status=200, body=data, content_type=contentType)
		
async def favicon_handler(request):
	return web.Response(body=favicon)

async def edit_handler(request):
	authKey = request.match_info["authKey"]
	
	if not compo.submissionsOpen:
		return web.Response(status=404, text="Submissions are currently closed!")
	
	if keyValid(authKey, editKeys):
		key = editKeys[authKey]
		
		form = compo.getEditFormForEntry(key["entryUUID"], authKey)
		html = submitTemplate.replace("[ENTRY-FORM]", form)
		html = html.replace("[ENTRANT-NAME]", compo.getEntrantName(key["entryUUID"]))
		
		return web.Response(status=200, body=html, content_type="text/html")
	else:
		return web.Response(status=404, text="File not found")

async def admin_handler(request):
	authKey = request.match_info["authKey"]
	
	if keyValid(authKey, adminKeys):
		key = adminKeys[authKey]
		
		html = adminTemplate.replace("[ENTRY-LIST]", compo.getAllEntryForms(authKey))
		html = html.replace("[VOTE-CONTROLS]", compo.getVoteControlsForWeek(True))
		html = html.replace("[ADMIN-CONTROLS]", getAdminControls(authKey))
		
		return web.Response(status=200, body=html, content_type="text/html")
	else:
		return web.Response(status=404, text="File not found")

async def file_post_handler(request):
	authKey = request.match_info["authKey"]
	uuid = request.match_info["uuid"]
	
	if (keyValid(authKey, editKeys) and editKeys[authKey]["entryUUID"] == uuid and compo.submissionsOpen) or keyValid(authKey, adminKeys):
		for whichWeek in [True, False]:
			week = compo.getWeek(whichWeek)
		
			for e in week["entries"]:
				if e["uuid"] != uuid:
					continue
			
				reader = await request.multipart()
				
				if reader == None:
					return web.Response(status=400, text="Not happening babe")
				
				while True:
					field = await reader.next()
					
					if field == None:
						break
					
					if field.name == "entryName":
						e["entryName"] = (await field.read(decode=True)).decode("utf-8")
					elif field.name == "entrantName" and keyValid(authKey, adminKeys):
						e["entrantName"] = (await field.read(decode=True)).decode("utf-8")
						
					elif field.name == "deleteEntry" and keyValid(authKey, adminKeys):
						week["entries"].remove(e)
						return web.Response(status=200, text="Entry successfully deleted.")
					
					elif field.name == "mp3Link":
						url = (await field.read(decode=True)).decode("utf-8")
						if len(url) > 1:
							e["mp3"] = url
							e["mp3Format"] = "external"
							e["mp3Filename"] = ""
						
					elif field.name == "mp3" or field.name == "pdf":
						if field.filename == "":
							continue
					
						size = 0
						e[field.name] = None
						
						e[field.name + "Filename"] = field.filename
						
						if field.name == "mp3":
							e["mp3Format"] = "mp3"
						
						while True:
							chunk = await field.read_chunk()
							
							if not chunk:
								break
							
							size += len(chunk)
							
							if size > 1024 * 1024 * 32: # 32MB limit
								e[field.name] = None
								e[field.name + "Filename"] = None
								return web.Response(status=413, text="File too big! Must be 32MB or less.")
							
							if e[field.name] == None:
								e[field.name] = chunk
							else:
								e[field.name] += chunk
				
				compo.saveWeeks()
				return web.Response(status=200, body=submitSuccess, content_type="text/html")
		
		return web.Response(status=400, text="That entry doesn't seem to exist")
					
	else:
		return web.Response(status=403, text="Not happening babe")

#async def debug_handler(request):
#	cmd = request.match_info["command"]
#	
#	if cmd == "save":
#		compo.saveWeeks()
#	
#	return web.Response(status=200, text="Nice.")

#for member in bot.client.guilds[0].members:
#
#async def yeet_handler(request):
#	await bot.client.get_channel(720055562573840384).send("yeet yate yote")
#	return web.Response(text="lmao")
	
server = web.Application()

server.add_routes([ web.get("/", vote_handler),
					web.get("/files/{uuid}/{filename}", week_files_handler),
					web.get("/favicon.ico", favicon_handler),
					web.get("/edit/{authKey}", edit_handler),
					web.get("/admin/{authKey}", admin_handler),
					web.post("/admin/edit/{authKey}", admin_control_handler),
					web.post("/edit/post/{uuid}/{authKey}", file_post_handler),
					#web.get("/debug/{command}", debug_handler),
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