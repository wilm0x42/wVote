#!/usr/bin/env python3

import io
import urllib.parse
import logging
import statistics
import datetime
import random

import discord
from discord.ext import commands

from . import config
from . import compo
from . import keys

logger = logging.getLogger(__name__)

DM_REMINDER = "_Ahem._ DM me to use this command."


class WBot(commands.Bot):
    def __init__(self, options: config.Config, compos: compo.Compos, keys: keys.Keys):
        """Initializes the bot and defines the commands for bot interaction."""
        intents = discord.Intents.default()
        intents.messages = True
        intents.emojis = True
        intents.members = True
        intents.message_content = True

        super().__init__(
            description="Musical Voting Platform",
            pm_help=False,
            command_prefix=options.command_prefix,
            case_insensitive=True,
            help_command=None,
            intents=intents,
            # **options,
        )

        self.compos = compos
        self.options = options

        @self.event
        async def on_ready() -> None:
            """
            Fires when the bot is successfully connected and logged-in.
            """
            user = self.user
            if user is None:
                user_name = None
                user_id = None
            else:
                user_name = user.name
                user_id = user.id

            logger.info(f"DISCORD: Logged in as {user_name} (ID: {user_id})")

            logger.info(
                f"DISCORD: Connected to {len(self.guilds)} servers, and {len(set(self.get_all_members()))} users"
            )
            logger.info(
                (
                    f"DISCORD: Invite link: https://discordapp.com/oauth2/authorize?self_id={user_id}&scope=bot&permissions=335936592"
                )
            )
            activity = discord.Game(name="Preventing Voter Fraud Again")
            return await self.change_presence(activity=activity)

        @self.listen("on_message")
        async def unhandled_dm(message):
            """
            When a DM is received and it didn't match any known commands, show the help prompt.
            """
            # Don't reply to self
            if message.author == self.user:
                return

            # Only DMs
            if message.channel != message.author.dm_channel:
                return

            if any(
                message.content.startswith(prefix)
                for prefix in self.options.command_prefix
            ):
                return

            await message.channel.send(self.help_message())

        @self.event
        async def on_command_error(
            context: commands.Context, error: commands.CommandError
        ) -> None:
            """Notifies the user on a failed command."""
            if isinstance(error, commands.errors.CommandNotFound):
                if context.channel.type == discord.ChannelType.private:
                    await context.send(self.help_message())
                else:
                    await context.author.send(self.help_message())
                return

            if isinstance(error, commands.errors.PrivateMessageOnly):
                await context.send(DM_REMINDER)
                return

            if isinstance(error, IsNotAdminError):
                command_name = context.command.name if context.command else ""
                logger.warning(
                    f"DISCORD: {context.author.name} ({context.author.id}) attempted to use an admin command: {command_name}"
                )
                return

            if isinstance(error, WrongChannelError):
                await context.send("This isn't the right channel for this!")
                return

            logger.error("DISCORD: Unhandled command error: %s" % str(error))

        def is_admin(context: commands.Context) -> bool:
            """
            Bot command check: Returns `true` if the user is an admin.
            Throws `IsNotAdminError()` on failure.
            """

            return context.author.id in options.admins

        def is_admin_check(context: commands.Context) -> bool:
            """
            Bot command check: Returns `true` if the user is an admin.
            Throws `IsNotAdminError()` on failure.
            """

            if not is_admin(context):
                raise IsNotAdminError()

            return True

        def is_postentries_channel():
            """
            Bot command check: Returns `true` if the message is sent to the
            proper channel.
            Throws `WrongChannelError` on failure.
            """

            def predicate(context: commands.Context):
                if context.channel.id == options.postentries_channel:
                    return True

                raise WrongChannelError()

            return commands.check(predicate)

        @self.command()
        @commands.check(is_admin_check)
        @commands.check_any(is_postentries_channel(), commands.dm_only())
        async def postentries(context: commands.Context) -> None:
            """
            Post the entries of the week to the current channel.
            Works in the postentries channel or in DMs.
            """
            week = compos.get_week(compo.THIS_WEEK)
            await _publish_entries(context, week)

        @self.command()
        @commands.check(is_admin_check)
        @commands.dm_only()
        async def postentriespreview(context: commands.Context) -> None:
            """
            Post the entries of the next week. Only works in DMs.
            """
            week = compos.get_week(compo.NEXT_WEEK)
            await _publish_entries(context, week)

        async def _publish_entries(context: commands.Context, week: compo.Week) -> None:
            """
            Actually posts the entries of the chosen week into the proper channel.
            """
            async with context.channel.typing():
                for entry in week["entries"]:
                    try:
                        if not compo.validate_entry(entry):
                            continue

                        discord_user = self.get_user(entry["discordID"])
                        # get_user relies on cache, so if it's not cached, let's try to
                        # get it from the API (which should also cache it afaik)
                        if discord_user is None:
                            discord_user = await self.fetch_user(entry["discordID"])

                        if discord_user is None:
                            entrant_ping = "@" + entry["entrantName"]
                        else:
                            entrant_ping = discord_user.mention

                        upload_files = []
                        upload_message = f"{entrant_ping} - {entry['entryName']}"

                        if "entryNotes" in entry:
                            upload_message += "\n" + entry["entryNotes"]

                        if entry["mp3Format"] == "mp3":
                            upload_files.append(
                                discord.File(
                                    io.BytesIO(bytes(entry["mp3"])),
                                    filename=entry["mp3Filename"],
                                )
                            )
                        elif entry["mp3Format"] == "external":
                            upload_message += "\n" + entry["mp3"]

                        upload_files.append(
                            discord.File(
                                io.BytesIO(bytes(entry["pdf"])),
                                filename=entry["pdfFilename"],
                            )
                        )

                        total_len = len(bytes(entry["pdf"]))

                        if entry["mp3Format"] == "mp3":
                            total_len += len(bytes(entry["mp3"]))

                        # 8MB limit
                        if total_len < 8_000_000 or entry["mp3Format"] != "mp3":
                            await context.send(upload_message, files=upload_files)
                        else:
                            # Upload mp3 and pdf separately if they're too big together
                            await context.send(upload_message, files=[upload_files[0]])
                            if len(upload_files) > 1:
                                await context.send("", files=[upload_files[1]])

                    except Exception as e:
                        logger.error("DISCORD: Failed to upload entry: %s" % str(e))
                        await context.send("(Failed to upload this entry!)")
                        continue

        @self.command()
        @commands.check(is_admin_check)
        @commands.dm_only()
        async def manage(context: commands.Context) -> None:
            """Shows link to management panel"""

            key = keys.create_admin_key()

            url = f"{options.url_prefix}/admin/?key={key}"
            await context.send("Admin interface: " + url + self.expiry_message())

        @self.command()
        @commands.dm_only()
        async def submit(context: commands.Context) -> None:
            """Provides a link to submit your entry."""

            week = compos.get_week(compo.NEXT_WEEK)

            if not week["submissionsOpen"]:
                closed_info = "Sorry! Submissions are currently closed."
                await context.send(closed_info)
                return

            for entry in week["entries"]:
                if entry["discordID"] == context.author.id:
                    key = keys.create_edit_key(entry["uuid"])
                    url = f"{options.url_prefix}/edit/?key={key}"
                    edit_info = (
                        "Link to edit your existing "
                        "submission: " + url + self.expiry_message()
                    )
                    await context.send(edit_info)
                    return

            new_entry = compo.create_blank_entry(context.author.name, context.author.id)
            compo.add_to_week(week, new_entry)

            key = keys.create_edit_key(new_entry["uuid"])
            url = f"{options.url_prefix}/edit/?key={key}"

            await context.send("Submission form: " + url + self.expiry_message())

        @self.command()
        @commands.dm_only()
        async def vote(context: commands.Context) -> None:
            """Sends the user a vote key to be used in the voting interface"""

            # TODO: Return a whole-ass link

            key = keys.create_vote_key(context.author.id, context.author.name)

            await context.send(f"```{key}```")

            message = "Thank you for voting!\n"
            message += "This key will expire in %s minutes. " % options.default_ttl
            message += "If you need another key, including if you want to revise your "
            message += "vote, you can use this command again to obtain a new one."

            await context.send(message)

        @self.command(aliases=["getentryplacements"])
        @commands.check(is_admin_check)
        @commands.dm_only()
        async def results(context: commands.Context) -> None:
            """Prints the entries ranked according to the STAR algoritm."""
            ranked = compos.get_ranked_entrant_list(compos.get_week(compo.THIS_WEEK))

            message = "```\n"

            for e in ranked:
                message += "%d - %s - %s (%f)\n" % (
                    e["votePlacement"],
                    e["entrantName"],
                    e["entryName"],
                    e["voteScore"],
                )

            message += "\n```\n"
            message += f"Use `{self.options.command_prefix[0]}closevoting` to close voting for this week."

            await context.send(message)

        @self.command()
        async def howmany(context: commands.Context) -> None:
            """
            Prints how many entries are currently submitted for the upcoming week.
            """

            response = "%d, so far." % len(
                compo.valid_entries(compos.get_week(compo.NEXT_WEEK))
            )

            await context.send(response)

        @self.command()
        async def howlong(context: commands.Context) -> None:
            """
            Prints how long is left until the deadline
            """
            # This *should* be the timezone offset between where 8bot is hosted and the
            # local timezone where the weeklies are hosted
            # TODO: Remove this and launch with `TZ=<Host timezone> python -m wbot.`
            timezone_offset = datetime.timedelta(hours=options.timezone_offset)

            # An offset of 15:30 in the bot config would mean it would close at
            # 3:30pm Eastern on a given date
            deadline_time_offset = datetime.datetime.strptime(
                options.deadline_time_offset, "%H:%M"
            )
            # Any date information is redundant
            deadline_time_offset = deadline_time_offset.time()

            today = datetime.date.today()
            # In the config file, monday is 0, tuesday is 1, etc.
            date_offset = datetime.timedelta(
                (options.deadline_weekday - today.weekday()) % 7
            )

            # If the next friday is not the target date, it should be manually chosen
            # target_date = datetime.date(2020, 12, 25)
            target_date = today + date_offset

            # We only want to add 7 days if we are already past the time offset
            if (
                today == target_date
                and datetime.datetime.now().time() > deadline_time_offset
            ):
                target_date += datetime.timedelta(days=7)
            
            # Target time is Friday at midnight EST
            target_time = datetime.datetime.combine(target_date, deadline_time_offset)

            time_difference = target_time - datetime.datetime.now() + timezone_offset

            # TODO: Use a time formatter like https://babel.pocoo.org/en/latest/dates.html#time-delta-formatting
            # It even supports timezone lol.
            days = time_difference.days
            hours = time_difference.seconds // 3600
            minutes = (time_difference.seconds % 3600) // 60
            minutes = round(minutes)
            result = ""
            if days != 1:
                result += f"{days} days"
            else:
                result += f"{days} day"

            if days > 0:
                if hours > 0 and minutes > 0:
                    result += ", "
                elif (hours > 0) ^ (minutes > 0):
                    result += " and "
                else:
                    result += " "

            if hours > 1:
                result += "{} hours".format(hours)
            elif hours > 0:
                result += "{} hour".format(hours)
            if hours > 0:
                if days > 0 and minutes > 0:
                    result += ", and "
                elif minutes > 0:
                    result += " and "
                else:
                    result += " "

            if days == 0 and hours == 0:
                result += "Approximately "
            if minutes != 1:
                result += "{} minutes ".format(minutes)
            else:
                result += "{} minute ".format(minutes)

            if days == 0 and hours == 0 and minutes == 0:
                result = "Less than 60 seconds "
            result += "until submissions close."

            # a very serious feature
            if random.random() <= (1 / 10000):
                result = "longer than yours *lmao*"

            await context.send(result)

        @self.command()
        async def help(context: commands.Context) -> None:
            admin_context = False
            if isinstance(context.channel, discord.DMChannel):
                admin_context = is_admin(context)

            await context.send(self.help_message(True, admin_context))

        @self.command()
        @commands.dm_only()
        async def status(context: commands.Context) -> None:
            """Displays the status of your entry for this week."""

            week = compos.get_week(compo.NEXT_WEEK)

            for entry in week["entries"]:
                if entry["discordID"] == context.author.id:
                    await context.send(self.entry_info_message(entry))
                    return

            await context.send(
                "You haven't submitted anything yet! "
                "But if you want to you can with %ssubmit !"
                % self.options.command_prefix[0]
            )

        @self.command()
        @commands.dm_only()
        async def myresults(context: commands.Context) -> None:
            """Shows you your results on the latest vote."""
            week = compos.get_week(compo.THIS_WEEK)

            if week["votingOpen"]:
                await context.send(
                    "You can't really get results while they're still coming "
                    "in, despite what election coverage would lead you to believe; sorry."
                )
                return

            user_entry = None

            if context.author.id in options.results_blacklist:
                await context.send("Sorry but I'm too sleeby to calculate results")
                return

            for entry in week["entries"]:
                if entry["discordID"] == context.author.id:
                    user_entry = entry
                    break

            if not user_entry:
                await context.send("You didn't submit anything for this week!")
                return

            compo.verify_votes(week)
            scores = compo.fetch_votes_for_entry(week["votes"], user_entry["uuid"])

            if len(scores) == 0:
                await context.send(
                    "Well this is awkward, no one voted on your entry..."
                )
                return

            message = []
            message.append(
                "Please keep in mind that music is subjective, and that "
                "these scores shouldn't be taken to represent the quality of"
                " your entry-- your artistic work is valuable, regardless of"
                " what results it was awarded, so don't worry too much about it"
            )
            message.append("And with that out of the way...")
            message.append("*drumroll please*")
            for category in week["voteParams"]:
                category_scores = [
                    s["rating"] for s in scores if s["voteParam"] == category
                ]
                if len(category_scores) == 0:
                    # The user received votes, but not in this category
                    category_scores = [0]
                text = "%s: You got an average score of %1.2f" % (
                    category,
                    statistics.mean(category_scores),
                )
                message.append(text)

            message.append(
                "Your total average was: %1.2f!"
                % statistics.mean(s["rating"] for s in scores)
            )

            await context.send("\n".join(message))

        @self.command()
        @commands.check(is_admin_check)
        async def closevoting(context: commands.Context) -> None:
            week = compos.get_week(compo.THIS_WEEK)
            week["votingOpen"] = False

            await context.send("Voting for the current week is now closed.")
            compos.save_weeks()

        @self.command()
        @commands.check(is_admin_check)
        async def openvoting(context: commands.Context) -> None:
            week = compos.get_week(compo.THIS_WEEK)
            week["votingOpen"] = True

            await context.send("Voting for the current week is now open.")
            compos.save_weeks()

        @self.command()
        async def crudbroke(context: commands.Context) -> None:
            week = compos.get_week(compo.NEXT_WEEK)

            if not "crudbroke" in week:
                week["crudbroke"] = 0

            week["crudbroke"] += 1

            message = "Dang, that's happened %d times this week." % week["crudbroke"]

            await context.send(message)

    async def notify_admins(self, msg: str) -> None:
        """
        Sends a message to an admin channel if it has been specified in bot.conf

        Parameters
        ----------
        msg : str
            The message that should be sent
        """

        admin_channel = self.get_channel(self.options.notify_admins_channel)
        if admin_channel is not None:
            await admin_channel.send(msg)

    async def submission_message(
        self, entry: compo.Entry, user_was_admin: bool
    ) -> None:
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
        notification_message = self.entry_info_message(entry)

        if user_was_admin:
            notification_message += "\n(This edit was performed by an admin)"

        await self.notify_admins(notification_message)

    def help_message(self, full: bool = False, is_admin: bool = False) -> str:
        """
        Creates and returns a help message for guiding users in the right direction.
        Additionally lets users know whether the submissions for this week are
        currently open.

        Returns
        -------
        str
            The generated help message.
        """

        commands = ["howmany", "submit", "vote", "status", "myresults"]
        admin_commands = ["results", "postentries", "postentriespreview", "manage"]

        msg = (
            "Hey there! I'm 8Bot-- My job is to help you participate in "
            "the 8Bit Music Theory Discord Weekly Composition Competition.\n"
        )

        if self.compos.get_week(compo.NEXT_WEEK)["submissionsOpen"]:
            msg += "Submissions for this week's prompt are currently open.\n"
            msg += (
                "If you'd like to submit an entry, DM me the command `"
                + self.options.command_prefix[0]
                + "submit`, and I'll give you "
            )
            msg += "a secret link to a personal submission form. \n"
        else:
            msg += "Submissions for this week's prompt are now closed.\n"
            msg += (
                "To see the already submitted entries for this week, "
                "head on over to " + self.options.url_prefix
            ) + "\n"

        if not full:
            msg += (
                f"Send `{self.options.command_prefix[0]}"
                + "help` to see all available "
            )
            msg += "commands."
        else:
            msg += "\nI understand the following commands: \n"

            for command in commands:
                msg += f"`{self.options.command_prefix[0]}{command}`: "
                msg += self.get_command(command).short_doc + "\n"

            if is_admin:
                msg += "\nAlso since you're an admin, here are some secret commands: \n"

                for command in admin_commands:
                    msg += f"`{self.options.command_prefix[0]}{command}`: "
                    msg += self.get_command(command).short_doc + "\n"

            if len(self.options.command_prefix) > 1:
                msg += "\n"
                msg += (
                    f"Besides `{self.options.command_prefix[0]}" + "` I understand the "
                )
                msg += "following prefixes: " + ", ".join(
                    f"`{prefix}`" for prefix in self.options.command_prefix[1:]
                )

        return msg

    def entry_info_message(self, entry: compo.Entry) -> str:
        # TODO: Use fstrings
        entry_message = '%s submitted "%s":\n' % (
            entry["entrantName"],
            entry["entryName"],
        )

        # If a music file was attached (including in the form of an external link),
        # make note of it in the message
        mp3 = entry.get("mp3")
        mp3Format = entry.get("mp3Format")
        mp3Filename = entry.get("mp3Filename")
        if mp3 and mp3Format :
            if mp3Format == "mp3" and mp3Filename:
                entry_message += "MP3: %s/files/%s/%s %d KB\n" % (
                    self.options.url_prefix,
                    entry["uuid"],
                    urllib.parse.quote(mp3Filename),
                    len(mp3) / 1000,
                )
            elif mp3Format == "external":
                entry_message += "MP3: %s\n" % mp3

        # If a score was attached, make note of it in the message
        pdf = entry.get("pdf")
        pdf_filename = entry.get("pdfFilename")
        if pdf and pdf_filename:
            entry_message += "PDF: %s/files/%s/%s %d KB\n" % (
                self.options.url_prefix,
                entry["uuid"],
                urllib.parse.quote(pdf_filename),
                len(pdf) / 1000,
            )

        # Mention whether the entry is valid
        if compo.validate_entry(entry):
            entry_message += "This entry is valid, and good to go!\n"
        else:
            entry_message += (
                "This entry isn't valid! " "(Something is missing or broken!)\n"
            )
        return entry_message

    def expiry_message(self) -> str:
        """
        Returns a message to be sent to a user based to inform them that the
        submission link will expire.

        Returns
        -------
        str
            The message itself
        """

        return "\nThis link will expire in %d minutes" % self.options.default_ttl


class IsNotAdminError(commands.CheckFailure):
    """Class to represent the `is_admin` check failure."""

    pass


class WrongChannelError(commands.CheckFailure):
    """Class to represent the `is_channel` check failure."""

    pass
