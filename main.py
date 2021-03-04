#!/usr/bin/env python3

import logging
import logging.handlers

import asyncio

import keys
import http_server
import bot


def load_config() -> dict:
    """
    Loads configuration information from bot.conf.
    Specifically, bot.conf contains all information on what prefix is used
    to call the bot, which channel entries are posted in each week, which
    channel updates should be posted in, the bot key used to log in with
    discord.py, and which IDs are treated as admins.
    """

    conf = open("bot.conf", "r")

    # TODO: Take these values from the config file
    config = {
        "command_prefix": [],
        "test_mode": False,
        "admins": [],
        "default_ttl": 30
    }

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
            config["command_prefix"].append(arguments[1])
        if key == "test_mode":
            config["test_mode"] = (arguments[1] == "True")
        if key == "postentries_channel":
            config["postentries_channel"] = int(arguments[1])
        if key == "notify_admins_channel":
            config["notify_admins_channel"] = int(arguments[1])
        if key == "bot_key":
            config["bot_key"] = arguments[1]
        if key == "admin":
            config["admins"].append(arguments[1])

    if config["test_mode"]:
        config["server_domain"] = "127.0.0.1:8251"
        config["url_prefix"] = "http://%s" % config["server_domain"]
    else:
        config["server_domain"] = "8bitweekly.xyz"
        config["url_prefix"] = "https://%s" % config["server_domain"]

    logging.info("MAIN: Loaded bot.conf")

    return config

logging.basicConfig(format="%(asctime)s %(message)s",
                    level=logging.INFO,
                    handlers=[
                        logging.handlers.TimedRotatingFileHandler(
                            "logs/wvote.log",
                            when="W0",
                            backupCount=10),
                        logging.StreamHandler()
                    ])

loop = asyncio.get_event_loop()

config = load_config()
keys.configure(config)
bot_task = loop.create_task(bot.start(config))
http_task = loop.create_task(http_server.start_http(config))

loop.run_forever()
