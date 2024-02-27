#!/usr/bin/env python3

import logging
import logging.handlers
import pickle
import asyncio

from . import bot
from . import http_server
from . import compo
from . import keys


def main():
    """Initialize all dependencies and launch the Bot+Web Server."""

    logging.basicConfig(
        format="%(asctime)s %(message)s",
        level=logging.INFO,
        handlers=[
            logging.handlers.TimedRotatingFileHandler(
                "logs/wvote.log", when="W0", backupCount=10
            ),
            logging.StreamHandler(),
        ],
    )

    try:
        from .botconfig import Config

        config = Config()
    except ModuleNotFoundError as e:
        logging.error(f"Error loading bot config: {e}")
        logging.warning(
            "Loading default bot config as fallback; this likely will cause problems with discord.py"
        )

        from .config import Config

        config = Config()

    compo_storage = compo.Compos(compo.PickleTool())
    keys_storage = keys.Keys(config)
    wbot = bot.WBot(config, compo_storage, keys_storage)
    loop = asyncio.new_event_loop()
    bot_task = loop.create_task(wbot.start(config.bot_key))
    http_task = loop.create_task(
        http_server.WebServer(config, wbot, compo_storage, keys_storage).start_http()
    )

    loop.run_forever()


if __name__ == "__main__":
    main()
