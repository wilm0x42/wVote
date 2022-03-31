#!/usr/bin/env python3

import logging
import logging.handlers

import json
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
    config = json.load(open("botconf.json", "r"))

    logging.info("MAIN: Loaded bot.conf")

    return config


logging.basicConfig(format="%(asctime)s %(message)s",
                    level=logging.INFO,
                    handlers=[
                        logging.handlers.TimedRotatingFileHandler(
                            "logs/wvote.log", when="W0", backupCount=10),
                        logging.StreamHandler()
                    ])

loop = asyncio.get_event_loop()

config = load_config()
keys.configure(config)
bot_task = loop.create_task(bot.start(config))
http_task = loop.create_task(http_server.start_http(config))

loop.run_forever()
