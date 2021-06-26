#!/usr/bin/env python3

import asyncio
import io
import urllib.parse
import logging
import statistics
import datetime
import random

import discord
from discord.ext import commands

import compo
import keys

dm_reminder = "_Ahem._ DM me to use this command."
client = commands.Bot(description="Musical Voting Platform",
                      pm_help=False,
                      command_prefix=[],
                      case_insensitive=True,
                      help_command=None)
config = None


async def start(_config):
    global config

    config = _config
    client.command_prefix = config["command_prefix"]

    await client.start(config["bot_key"])


async def notify_admins(msg: str) -> None:
    """
    Sends a message to an admin channel if it has been specified in bot.conf

    Parameters
    ----------
    msg : str
        The message that should be sent
    """
    global config

    if config.get("notify_admins_channel"):
        await client.get_channel(config["notify_admins_channel"]).send(msg)


def entry_info_message(entry: dict) -> str:
    global config

    entry_message = '%s submitted "%s":\n' % (entry["entrantName"],
                                              entry["entryName"])

    # If a music file was attached (including in the form of an external link),
    # make note of it in the message
    if "mp3" in entry:
        if entry["mp3Format"] == "mp3":
            entry_message += "MP3: %s/files/%s/%s %d KB\n" \
                % (config["url_prefix"],
                   entry["uuid"],
                   urllib.parse.quote(entry["mp3Filename"]),
                   len(entry["mp3"]) / 1000)
        elif entry["mp3Format"] == "external":
            entry_message += "MP3: %s\n" % entry["mp3"]

    # If a score was attached, make note of it in the message
    if "pdf" in entry:
        entry_message += "PDF: %s/files/%s/%s %d KB\n" \
            % (config["url_prefix"],
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


def help_message(full: bool = False, is_admin: bool = False) -> str:
    """
    Creates and returns a help message for guiding users in the right direction.
    Additionally lets users know whether the submissions for this week are
    currently open.

    Returns
    -------
    str
        The generated help message.
    """
    global config

    commands = ["howmany", "submit", "vote", "status"]
    admin_commands = [
        "getentryplacements", "postentries", "postentriespreview", "manage"
    ]

    msg = ("Hey there! I'm 8Bot-- My job is to help you participate in "
           "the Pokemonth Competition.\n")

    if not full:
        msg += "Send `" + client.command_prefix[
            0] + "help` to see all available "
        msg += "commands."
    else:
        msg += "\nI understand the following commands: \n"

        for command in commands:
            msg += "`" + client.command_prefix[0] + command + "`: "
            msg += client.get_command(command).short_doc + "\n"

        if is_admin:
            msg += "\nAlso since you're an admin, here are some secret commands: \n"

            for command in admin_commands:
                msg += "`" + client.command_prefix[0] + command + "`: "
                msg += client.get_command(command).short_doc + "\n"

        if len(client.command_prefix) > 1:
            msg += "\n"
            msg += "Besides `" + client.command_prefix[
                0] + "` I understand the "
            msg += "following prefixes: " + ", ".join(
                "`" + prefix + "`" for prefix in client.command_prefix[1:])

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
    global config

    return "\nThis link will expire in %d minutes" % config["default_ttl"]


@client.event
async def on_ready() -> None:
    """
    Connects/logs in the bot to discord. Also outputs to the console that the
    connection was successful.
    """
    logging.info("DISCORD: Logged in as %s (ID: %s)" %
                 (client.user.name, client.user.id))
    logging.info("DISCORD: Connected to %d servers, and %d users" %
                 (len(client.guilds), len(set(client.get_all_members()))))
    logging.info(("DISCORD: Invite link: "
                  "https://discordapp.com/oauth2/authorize?client_id="
                  "%d&scope=bot&permissions=335936592" % client.user.id))
    activity = discord.Game(name="Preventing Voter Fraud")
    return await client.change_presence(activity=activity)


@client.event
async def on_command_error(context: commands.Context,
                           error: commands.CommandError) -> None:
    """Notifies the user on a failed command."""
    if isinstance(error, commands.errors.CommandNotFound):
        if context.channel.type == discord.ChannelType.private:
            await context.send(help_message())
        else:
            await context.author.send(help_message())
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
        await context.send("This isn't the right channel for this!")
        return

    logging.error("DISCORD: Unhandled command error: %s" % str(error))


async def is_admin(context: commands.Context) -> bool:
    """
    Bot command check: Returns `true` if the user is an admin.
    Throws `IsNotAdminError()` on failure.
    """
    global config

    if context.author.id not in config["admins"]:
        raise IsNotAdminError()

    return True


def is_postentries_channel():
    """
    Bot command check: Returns `true` if the message is sent to the
    proper channel.
    Throws `WrongChannelError` on failure.
    """
    def predicate(context: commands.Context):
        if context.channel.id == config.get("postentries_channel"):
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
                    upload_message += "\n" + entry["mp3"]

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
    global config

    key = keys.create_admin_key()

    url = "%s/admin/%s" % (config["url_prefix"], key)
    await context.send("Admin interface: " + url + expiry_message())


@client.command()
@commands.dm_only()
async def submit(context: commands.Context) -> None:
    """Provides a link to submit your entry."""
    global config

    week = compo.get_week(True)

    if not week["submissionsOpen"]:
        closed_info = "Sorry! Submissions are currently closed."
        await context.send(closed_info)
        return

    for entry in week["entries"]:
        if entry["discordID"] == context.author.id:
            key = keys.create_edit_key(entry["uuid"])
            url = "%s/edit/%s" % (config["url_prefix"], key)
            edit_info = ("Link to edit your existing "
                         "submission: " + url + expiry_message())
            await context.send(edit_info)
            return

    new_entry = compo.create_blank_entry(context.author.name,
                                         context.author.id)
    week["entries"].append(new_entry)
    key = keys.create_edit_key(new_entry["uuid"])
    url = "%s/edit/%s" % (config["url_prefix"], key)

    await context.send("Submission form: " + url + expiry_message())


@client.command()
@commands.dm_only()
async def vote(context: commands.Context) -> None:
    """Sends the user a vote key to be used in the voting interface"""
    global config

    key = keys.create_vote_key(context.author.id, context.author.name)

    await context.send("```%s```" % key)

    message = "Thank you for voting!\n"
    message += "This key will expire in %s minutes. " % config["default_ttl"]
    message += "If you need another key, including if you want to revise your "
    message += "vote, you can use this command again to obtain a new one."

    await context.send(message)


@client.command()
@commands.check(is_admin)
@commands.dm_only()
async def getentryplacements(context: commands.Context) -> None:
    """Prints the entries ranked according to the STAR algoritm."""
    ranked = compo.get_ranked_entrant_list(compo.get_week(False))

    message = "```\n"

    for e in ranked:
        message += "%d - %s - %s (%f)\n" \
            % (e["votePlacement"], e["entrantName"],
               e["entryName"], e["voteScore"])

    message += "\n```\n"
    message += "Use `%sclosevoting` to close voting for this week." \
        % client.command_prefix[0]

    await context.send(message)


@client.command()
async def howmany(context: commands.Context) -> None:
    """
    Prints how many entries are currently submitted for the upcoming week.
    """

    response = "%d, so far." % compo.count_valid_entries(compo.get_week(True))

    await context.send(response)


@client.command()
async def howlong(context: commands.Context) -> None:
    """
    Prints how long is left until the deadline
    """

    timezone_offset = datetime.timedelta(hours=config["timezone_offset"])

    today = datetime.date.today()
    #date_offset = datetime.timedelta((4 - today.weekday()) % 7)

    # If the next friday is not the target date, it should be manually chosen
    # friday_date = datetime.date(2020, 12, 25)
    #friday_date = today + date_offset

    # Target time is Friday at midnight EST
    #target_time = datetime.datetime.combine(friday_date, datetime.time(0))
    target_time = datetime.datetime(2021, 7, 11)

    time_difference = target_time - datetime.datetime.now() + timezone_offset
    days = time_difference.days
    hours = time_difference.seconds // 3600
    minutes = (time_difference.seconds % 3600) / 60
    minutes = round(minutes)

    result = ""
    if days > 1:
        result += '{} days, '.format(days)
    elif days > 0:
        result += '{} day, '.format(days)

    if hours > 1:
        result += '{} hours, '.format(hours)
    elif hours > 0:
        result += '{} hour, '.format(hours)

    if minutes > 1:
        result += '{} minutes, '.format(minutes)
    elif minutes > 0:
        result += '{} minute, '.format(minutes)
    result += 'until submissions close.'

    # a very serious feature
    if random.random() <= (1/10000):
        result = "longer than yours *lmao*"

    await context.send(result)


@client.command()
async def help(context: commands.Context) -> None:
    try:
        await is_admin(context)
        admin_context = True
    except IsNotAdminError:
        admin_context = False

    await context.send(help_message(True, admin_context))

    if not admin_context:
        raise IsNotAdminError()


@client.command()
@commands.dm_only()
async def status(context: commands.Context) -> None:
    """Displays the status of your entry for this week."""
    global config

    week = compo.get_week(True)

    for entry in week["entries"]:
        if entry["discordID"] == context.author.id:
            await context.send(entry_info_message(entry))
            return

    await context.send("You haven't submitted anything yet! "
                       "But if you want to you can with %ssubmit !" %
                       client.command_prefix[0])


@client.command()
@commands.check(is_admin)
@commands.dm_only()
async def myresults(context: commands.Context) -> None:
    """Shows you your results on the latest vote."""
    week = compo.get_week(False)

    if week["votingOpen"]:
        await context.send(
            "You can't really get results while they're still coming "
            "in, despite what election coverage would lead you to believe; sorry."
        )
        return

    user_entry = None

    for entry in week["entries"]:
        if entry["discordID"] == context.author.id:
            user_entry = entry
            break

    if not user_entry:
        await context.send("You didn't submit anything for this week!")
        return

    compo.verify_votes(week)
    scores = compo.fetch_votes_for_entry(week["votes"], entry["uuid"])

    if len(scores) == 0:
        await context.send(
            "Well this is awkward, no one voted on your entry...")
        return

    message = []
    message.append(
        "Please keep in mind that music is subjective, and that "
        "these scores shouldn't be taken to represent the quality of"
        " your entry-- your artistic work is valuable, regardless of"
        " what results it was awarded, so don't worry too much about it")
    message.append("And with that out of the way...")
    message.append("*drumroll please*")
    for category in week["voteParams"]:
        category_scores = [
            s['rating'] for s in scores if s['voteParam'] == category
        ]
        if len(category_scores) == 0:
            # The user received votes, but not in this category
            category_scores = [0]
        text = "%s: You got an average score of %1.2f" \
            % (category, statistics.mean(category_scores))
        message.append(text)

    message.append("Your total average was: %1.2f!" %
                   statistics.mean(s['rating'] for s in scores))

    await context.send("\n".join(message))


@client.command()
@commands.check(is_admin)
async def closevoting(context: commands.Context) -> None:
    week = compo.get_week(False)
    week["votingOpen"] = False
    
    await context.send("Voting for the current week is now closed.")
    compo.save_weeks()

@client.command()
@commands.check(is_admin)
async def openvoting(context: commands.Context) -> None:
    week = compo.get_week(False)
    week["votingOpen"] = True
    
    await context.send("Voting for the current week is now open.")
    compo.save_weeks()

@client.command()
async def crudbroke(context: commands.Context) -> None:
    week = compo.get_week(True)

    if not "crudbroke" in week:
        week["crudbroke"] = 0

    week["crudbroke"] += 1

    message = "Dang, that's happened %d times this week." % week["crudbroke"]

    await context.send(message)
