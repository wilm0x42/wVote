#!/usr/bin/env python3

import asyncio
import io
import urllib.parse
import logging

import discord
from discord.ext import commands

import compo
import http_server

dm_reminder = "_Ahem._ DM me to use this command."
client = commands.Bot(description="Musical Voting Platform",
                      pm_help=False,
                      command_prefix=[],
                      case_insensitive=True,
                      help_command=None)
test_mode = False
postentries_channel = 0
notify_admins_channel = 0


def url_prefix() -> str:
    """
    Returns a URL prefix that changes depending on whether the bot is being
    tested or is being used in production.

    Returns
    -------
    str
        The URL of the test server if in test mode, and the production server
        URL otherwise.
    """
    if test_mode:
        return "http://127.0.0.1:8251"
    else:
        return "https://%s" % http_server.server_domain


def load_config() -> None:
    """
    Loads configuration information from bot.conf.
    Specifically, bot.conf contains all information on what prefix is used
    to call the bot, which channel entries are posted in each week, which
    channel updates should be posted in, the bot key used to log in with
    discord.py, and which IDs are treated as admins.
    """
    global test_mode
    global postentries_channel
    global notify_admins_channel

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
            client.command_prefix.append(arguments[1])
        if key == "test_mode":
            test_mode = (arguments[1] == "True")
        if key == "postentries_channel":
            postentries_channel = int(arguments[1])
        if key == "notify_admins_channel":
            notify_admins_channel = int(arguments[1])
        if key == "bot_key":
            client.bot_key = arguments[1]
        if key == "admin":
            client.admins.append(arguments[1])

    logging.info("DISCORD: Loaded bot.conf")


async def notify_admins(msg: str) -> None:
    """
    Sends a message to an admin channel if it has been specified in bot.conf

    Parameters
    ----------
    msg : str
        The message that should be sent
    """
    if notify_admins_channel:
        await client.get_channel(notify_admins_channel).send(msg)

def entry_info_message(entry: dict) -> str:
    entry_message = "%s submitted \"%s\":\n" % (entry["entrantName"],
                                                       entry["entryName"])

    # If a music file was attached (including in the form of an external link),
    # make note of it in the message
    if "mp3" in entry:
        if entry["mp3Format"] == "mp3":
            entry_message += "MP3: %s/files/%s/%s %d KB\n" \
                % (url_prefix(),
                   entry["uuid"],
                   urllib.parse.quote(entry["mp3Filename"]),
                   len(entry["mp3"]) / 1000)
        elif entry["mp3Format"] == "external":
            entry_message += "MP3: %s\n" % entry["mp3"]

    # If a score was attached, make note of it in the message
    if "pdf" in entry:
        entry_message += "PDF: %s/files/%s/%s %d KB\n" \
            % (url_prefix(),
               entry["uuid"],
               urllib.parse.quote(entry["pdfFilename"]),
               len(entry["pdf"]) / 1000)

    # Mention whether the entry is valid
    if compo.entry_valid(entry):
        entry_message += "This entry is valid, and good to go!\n"
    else:
        entry_message += ("This entry isn't valid! "
                                 "(Something is missing or broken!)\n")
    return entry_message

async def submission_message(entry: dict, user_was_admin: bool) -> None:
    """
    Prepares a message to be sent to the admin channel based on an entry that
    was submitted to the website.

    Parameters
    ----------
    entry : dict
        The entry that was submitted.
    user_was_admin : bool
        True if this edit was performed via the admin interface, False if this
        edit was performed via a civilian submission link.
    """
    notification_message = entry_info_message(entry)

    if user_was_admin:
        notification_message += "(This edit was performed by an admin)"

    await notify_admins(notification_message)


def help_message() -> str:
    """
    Creates and returns a help message for guiding users in the right direction.
    Additionally lets users know whether the submissions for this week are
    currently open.

    Returns
    -------
    str
        The generated help message.
    """
    msg = ("Hey there! I'm 8Bot-- My job is to help you participate in "
           "the 8Bit Music Theory Discord Weekly Composition Competition.\n")

    if compo.get_week(True)["submissionsOpen"]:
        msg += "Submissions for this week's prompt are currently open.\n"
        msg += "If you'd like to submit an entry, DM me the command `" + \
            client.command_prefix[0] + "submit`, and I'll give you "
        msg += "a secret link to a personal submission form."
    else:
        msg += "Submissions for this week's prompt are now closed.\n"
        msg += ("To see the already submitted entries for this week, "
                "head on over to " + url_prefix())

    return msg


class IsNotAdminError(commands.CheckFailure):
    """Class to represent the `is_admin` check failure."""
    pass


class WrongChannelError(commands.CheckFailure):
    """Class to represent the `is_channel` check failure."""
    pass


def expiry_message() -> str:
    """
    Returns a message to be sent to a user based to inform them that the
    submission link will expire.

    Returns
    -------
    str
        The message itself
    """
    return "\nThis link will expire in %d minutes" % http_server.default_ttl


@client.event
async def on_ready() -> None:
    """
    Connects/logs in the bot to discord. Also outputs to the console that the
    connection was successful.
    """
    logging.info("DISCORD: Logged in as %s (ID: %s)" %
          (client.user.name, client.user.id))
    logging.info("DISCORD: Connected to %s servers, and %s users" %
          (str(len(client.guilds)), str(len(set(client.get_all_members())))))
    logging.info(("DISCORD: Invite link: "
           "https://discordapp.com/oauth2/authorize?client_id="
           "%s&scope=bot&permissions=335936592" % str(client.user.id)))
    activity = discord.Game(name="Preventing Voter Fraud")
    return await client.change_presence(activity=activity)


@client.event
async def on_command_error(context: commands.Context,
                           error: commands.CommandError) -> None:
    """Notifies the user on a failed command."""
    if isinstance(error, commands.errors.CommandNotFound):
        if context.channel.type == discord.ChannelType.private:
            await context.send(help_message())
            return

    if isinstance(error, commands.errors.PrivateMessageOnly):
        await context.send(dm_reminder)
        return

    if isinstance(error, IsNotAdminError):
        logging.warning(
              "DISCORD: %s (%d) attempted to use an admin command: %s" %
              (context.author.name, context.author.id, context.command.name))
        return

    if isinstance(error, WrongChannelError):
        await context.send("This isn't the right channel" " for this!")
        return

    logging.error("DISCORD: Unhandled command error: %s" % str(error))


async def is_admin(context: commands.Context) -> bool:
    """
    Bot command check: Returns `true` if the user is an admin.
    Throws `IsNotAdminError()` on failure.
    """

    if str(context.author.id) not in client.admins:
        raise IsNotAdminError()

    return True


def is_postentries_channel():
    """
    Bot command check: Returns `true` if the message is sent to the
    proper channel.
    Throws `WrongChannelError` on failure.
    """
    def predicate(context: commands.Context):
        if postentries_channel != 0 and context.channel.id == postentries_channel:
            return True

        raise WrongChannelError()

    return commands.check(predicate)


@client.command()
@commands.check(is_admin)
@commands.check_any(is_postentries_channel(), commands.dm_only())
async def postentries(context: commands.Context) -> None:
    """
    Post the entries of the week to the current channel.
    Works in the postentries channel or in DMs.
    """
    week = compo.get_week(False)
    await publish_entries(context, week)


@client.command()
@commands.check(is_admin)
@commands.dm_only()
async def postentriespreview(context: commands.Context) -> None:
    """
    Post the entries of the next week. Only works in DMs.
    """
    week = compo.get_week(True)
    await publish_entries(context, week)


async def publish_entries(context: commands.Context, week: dict) -> None:
    """
    Actually posts the entries of the chosen week into the proper channel.
    """
    async with context.channel.typing():
        for entry in week["entries"]:
            try:
                if not compo.entry_valid(entry):
                    continue

                discord_user = client.get_user(entry["discordID"])

                if discord_user is None:
                    entrant_ping = "@" + entry["entrantName"]
                else:
                    entrant_ping = discord_user.mention

                upload_files = []
                upload_message = "%s - %s" % (entrant_ping, entry["entryName"])

                if "entryNotes" in entry:
                    upload_message += "\n" + entry["entryNotes"]

                if entry["mp3Format"] == "mp3":
                    upload_files.append(
                        discord.File(io.BytesIO(bytes(entry["mp3"])),
                                     filename=entry["mp3Filename"]))
                elif entry["mp3Format"] == "external":
                    upload_message += "\n" + str(entry["mp3"])
                
                upload_files.append(
                    discord.File(io.BytesIO(bytes(entry["pdf"])),
                                 filename=entry["pdfFilename"]))
                
                total_len = len(bytes(entry["pdf"]))
                
                if entry["mp3Format"] == "mp3":
                    total_len += len(bytes(entry["mp3"]))
                
                # 8MB limit
                if total_len < 8000 * 1000 or entry["mp3Format"] != "mp3":
                    await context.send(upload_message, files=upload_files)
                else:
                    # Upload mp3 and pdf separately if they're too big together
                    await context.send(upload_message, files=[upload_files[0]])
                    await context.send("", files=[upload_files[1]])
                    
            except Exception as e:
                logging.error("DISCORD: Failed to upload entry: %s" % str(e))
                await context.send("(Failed to upload this entry!)")
                continue


@client.command()
@commands.check(is_admin)
@commands.dm_only()
async def manage(context: commands.Context) -> None:
    """Shows link to management panel"""
    key = http_server.create_admin_key()

    url = "%s/admin/%s" % (url_prefix(), key)
    await context.send("Admin interface: " + url + expiry_message())


@client.command()
@commands.dm_only()
async def submit(context: commands.Context) -> None:
    """
    Creates a submission entry for the user.
    Replies with a link to the management panel with options to create or edit.
    """
    week = compo.get_week(True)

    if not week["submissionsOpen"]:
        closed_info = "Sorry! Submissions are currently closed."
        await context.send(closed_info)
        return

    for entry in week["entries"]:
        if entry["discordID"] == context.author.id:
            key = http_server.create_edit_key(entry["uuid"])
            url = "%s/edit/%s" % (url_prefix(), key)
            edit_info = ("Link to edit your existing "
                         "submission: " + url + expiry_message())
            await context.send(edit_info)
            return

    new_entry = compo.create_blank_entry(context.author.name,
                                         context.author.id)
    key = http_server.create_edit_key(new_entry)
    url = "%s/edit/%s" % (url_prefix(), key)

    await context.send("Submission form: " + url + expiry_message())

@client.command()
@commands.dm_only()
async def vote(context: commands.Context) -> None:
    """Sends the user a vote key to be used in the voting interface"""
    key = http_server.create_vote_key(context.author.id, context.author.name)
    
    
    message = "Your key:\n```%s```\nThank you for voting!\n" % key
    message += "This key will expire in %s minutes. " % http_server.default_ttl
    message += "If you need another key, including if you want to revise your "
    message += "vote, you can use this command again to obtain a new one."
    
    await context.send(message)

@client.command()
@commands.check(is_admin)
async def googleformslist(context: commands.Context) -> None:
    """
    Generates the list of Google forms for the entries.
    """
    entries = compo.get_week(False)["entries"]

    response = "```\n"

    for e in entries:
        if not compo.entry_valid(e):
            continue
        response += "%s - %s\n" % (e["entrantName"], e["entryName"])

    response += "\n```"

    await context.channel.send(response)


@client.command()
async def howmany(context: commands.Context) -> None:
    """
    Prints how many entries are currently submitted for the upcoming week.
    """

    response = "%d, so far." % compo.count_valid_entries(True)

    await context.channel.send(response)

@client.command()
async def help(context: commands.Context) -> None:
    await context.send(help_message())

@client.command()
@commands.dm_only()
async def status(context: commands.Context) -> None:
    
    week = compo.get_week(True)

    for entry in week["entries"]:
        if entry["discordID"] == context.author.id:
            await context.send(entry_info_message(entry))
            return
    
    await context.send("You haven't submitted anything yet! But if you want to you can with %ssubmit !" % client.command_prefix[0])

if __name__ == "__main__":
    load_config()

    loop = asyncio.get_event_loop()

    loop.create_task(client.start(client.bot_key))
    loop.run_forever()
