#!/usr/bin/env python3

import io
import asyncio

import discord
from discord.ext.commands import Bot

import compo
import http_server

dm_reminder = "_Ahem._ DM me to use this command."
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


def help_message():
    msg = ("Hey there! I'm 8Bot-- My job is to help you participate in "
           "the 8Bit Music Theory Discord Weekly Composition Competition.\n")

    if compo.get_week(True)["submissionsOpen"]:
        msg += "Submissions for this week's prompt are currently open.\n"
        msg += "If you'd like to submit an entry, DM me the command `" + \
            client.command_prefix + "submit`, and I'll give you "
        msg += "a secret link to a personal submission form."
    else:
        msg += "Submissions for this week's prompt are now closed.\n"
        msg += ("To see the already submitted entries for this week, "
                "head on over to https://" + http_server.serverDomain)

    return msg


@client.event
async def on_ready():
    print("DISCORD: Logged in as %s (ID: %s)" %
          (client.user.name, client.user.id))
    print("DISCORD: Connected to %s servers, and %s users" %
          (str(len(client.guilds)), str(len(set(client.get_all_members())))))
    print(("DISCORD: Invite link: "
           "https://discordapp.com/oauth2/authorize?client_id="
           "%s&scope=bot&permissions=335936592" % str(client.user.id)))
    activity = discord.Game(name="Preventing Voter Fraud")
    return await client.change_presence(activity=activity)


@client.event
async def on_message(message):
    if message.author.id != client.user.id:
        if message.content.startswith(client.command_prefix):
            command = message.content[len(client.command_prefix):].lower()

            if command in ["postentries", "postentriespreview"] \
                    and str(message.author.id) in client.admins:
                week = compo.get_week(False)

                if command == "postentriespreview":
                    if not message.channel.type == discord.ChannelType.private:
                        await message.channel.send(dm_reminder)
                        return
                    week = compo.get_week(True)

                async with message.channel.typing():
                    for entry in week["entries"]:
                        if not compo.entry_valid(entry):
                            continue

                        discord_user = client.get_user(entry["discordID"])

                        if discord_user is None:
                            entrant_ping = "@" + entry["entrantName"]
                        else:
                            entrant_ping = discord_user.mention

                        upload_files = []
                        upload_message = "%s - %s" % (entrant_ping,
                                                      entry["entryName"])

                        if "entryNotes" in entry:
                            upload_message += "\n" + entry["entryNotes"]

                        if entry["mp3Format"] == "mp3":
                            upload_files.append(
                                discord.File(io.BytesIO(bytes(entry["mp3"])),
                                             filename=entry["mp3Filename"]))
                        elif entry["mp3Format"] == "external":
                            upload_message += "\n" + entry["mp3"]

                        upload_files.append(
                            discord.File(io.BytesIO(bytes(entry["pdf"])),
                                         filename=entry["pdfFilename"]))

                        await message.channel.send(upload_message,
                                                   files=upload_files)

            if command == "manage" and str(message.author.id) in client.admins:
                if message.channel.type == discord.ChannelType.private:
                    key = http_server.create_admin_key()
                    url = "https://%s/admin/%s" % (
                        http_server.server_domain, key)
                    await message.channel.send("Admin interface: " + url)
                    return

                else:

                    await message.channel.send(dm_reminder)
                    return

            if command == "submit":
                if message.channel.type == discord.ChannelType.private:
                    if not compo.get_week(True)["submissionsOpen"]:
                        closed_info = "Sorry! Submissions are currently closed."
                        await message.channel.send(closed_info)
                        return

                    week = compo.get_week(True)

                    for entry in week["entries"]:
                        if entry["discordID"] == message.author.id:
                            key = http_server.create_edit_key(entry["uuid"])
                            url = "https://%s/edit/%s" % (
                                http_server.server_domain, key)
                            edit_info = ("Link to edit your existing "
                                         "submission: " + url)
                            await message.channel.send(edit_info)
                            return

                    new_entry = compo.create_blank_entry(
                        message.author.name, message.author.id)
                    key = http_server.create_edit_key(new_entry)
                    url = "https://%s/edit/%s" % (
                        http_server.server_domain, key)
                    await message.channel.send("Submission form: " + url)
                    return

                else:
                    await message.channel.send(dm_reminder)
                    return

            if command == "help":
                await message.channel.send(help_message())
                return
        else:
            if message.channel.type == discord.ChannelType.private:
                await message.channel.send(help_message())
                return

            if str(client.user.id) in message.content:
                await message.channel.send(help_message())
                return


if __name__ == "__main__":
    load_config()

    loop = asyncio.get_event_loop()

    loop.create_task(client.start(client.bot_key))
    loop.run_forever()
