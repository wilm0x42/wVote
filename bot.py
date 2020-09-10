#!/usr/bin/env python3

import io
import asyncio

import discord
from discord.ext.commands import Bot

import compo
import http_server

client = Bot(description="Musical Voting Platform",
             pm_help=False, command_prefix="vote!")


def load_config():
    conf = open("bot.conf", "r")

    client.admins = []

    for line in conf:
        if line[0] == "#":
            continue

        if line[-1:] == "\n":  # remove newlines from string
            line = line[:-1]

        arguments = line.split("=")

        if len(arguments) < 2:
            continue

        key = arguments[0]

        if key == "command_prefix":
            client.command_prefix = arguments[1]
        if key == "bot_key":
            client.bot_key = arguments[1]
        if key == "admin":
            client.admins.append(arguments[1])

    print("DISCORD: Loaded bot.conf")


def helpMessage():
    msg = "Hey there! I'm 8Bot-- My job is to help you participate in the 8Bit Music Theory Discord Weekly Composition Competition.\n"

    if compo.getWeek(True)["submissionsOpen"]:
        msg += "Submissions for this week's prompt are currently open.\n"
        msg += "If you'd like to submit an entry, DM me the command `" + \
            client.command_prefix + "submit`, and I'll give you "
        msg += "a secret link to a personal submission form."
    else:
        msg += "Submissions for this week's prompt are now closed.\n"
        msg += "To see the already submitted entries for this week, head on over to https://" + \
            http_server.serverDomain

    return msg


@client.event
async def on_ready():
    print("DISCORD: Logged in as %s (ID: %s)" %
          (client.user.name, client.user.id))
    print("DISCORD: Connected to %s servers, and %s users" %
          (str(len(client.guilds)), str(len(set(client.get_all_members())))))
    print("DISCORD: Invite link: https://discordapp.com/oauth2/authorize?client_id=%s&scope=bot&permissions=335936592" % str(client.user.id))
    return await client.change_presence(activity=discord.Game(name="Preventing Voter Fraud"))


@client.event
async def on_message(message):
    if message.author.id != client.user.id:
        if message.content.startswith(client.command_prefix):
            command = message.content[len(client.command_prefix):].lower()

            if command in ["postentries", "postentriespreview"] and str(message.author.id) in client.admins:
                w = compo.getWeek(False)

                if command == "postentriespreview":
                    if not message.channel.type == discord.ChannelType.private:
                        await message.channel.send("_Ahem._ DM me to use this command.")
                        return
                    w = compo.getWeek(True)

                async with message.channel.typing():
                    for e in w["entries"]:
                        if not compo.entryValid(e):
                            continue

                        discordUser = client.get_user(e["discordID"])

                        entrantPing = "@" + e["entrantName"]

                        if discordUser != None:
                            entrantPing = discordUser.mention

                        uploadFiles = []
                        uploadMessage = "%s - %s" % (entrantPing,
                                                     e["entryName"])

                        if "entryNotes" in e:
                            uploadMessage += "\n" + e["entryNotes"]

                        if e["mp3Format"] == "mp3":
                            uploadFiles.append(discord.File(io.BytesIO(
                                bytes(e["mp3"])), filename=e["mp3Filename"]))
                        elif e["mp3Format"] == "external":
                            uploadMessage += "\n" + e["mp3"]

                        uploadFiles.append(discord.File(io.BytesIO(
                            bytes(e["pdf"])), filename=e["pdfFilename"]))

                        await message.channel.send(uploadMessage, files=uploadFiles)

            if command == "manage" and str(message.author.id) in client.admins:
                if message.channel.type == discord.ChannelType.private:
                    key = http_server.createAdminKey()
                    url = "https://%s/admin/%s" % (
                        http_server.serverDomain, key)
                    await message.channel.send("Admin interface: " + url)
                    return

                else:
                    await message.channel.send("_Ahem._ DM me to use this command.")
                    return

            if command == "submit":
                if message.channel.type == discord.ChannelType.private:
                    if not compo.getWeek(True)["submissionsOpen"]:
                        await message.channel.send("Sorry! Submissions are currently closed.")
                        return

                    week = compo.getWeek(True)

                    for e in week["entries"]:
                        if e["discordID"] == message.author.id:
                            key = http_server.createEditKey(e["uuid"])
                            url = "https://%s/edit/%s" % (
                                http_server.serverDomain, key)
                            await message.channel.send("Link to edit your existing submission: " + url)
                            return

                    newEntry = compo.createBlankEntry(
                        message.author.name, message.author.id)
                    key = http_server.createEditKey(newEntry)
                    url = "https://%s/edit/%s" % (
                        http_server.serverDomain, key)
                    await message.channel.send("Submission form: " + url)
                    return

                else:
                    await message.channel.send("_Ahem._ DM me to use this command.")
                    return

            if command == "help":
                await message.channel.send(helpMessage())
                return
        else:
            if message.channel.type == discord.ChannelType.private:
                await message.channel.send(helpMessage())
                return

            if str(client.user.id) in message.content:
                await message.channel.send(helpMessage())
                return


if __name__ == "__main__":
    load_config()

    loop = asyncio.get_event_loop()

    loop.create_task(client.start(client.bot_key))
    loop.run_forever()
