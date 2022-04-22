#!/usr/bin/env python3

import logging
import logging.handlers

import asyncio

import http_server
import bot





logging.basicConfig(format="%(asctime)s %(message)s",
                    level=logging.INFO,
                    handlers=[
                        logging.handlers.TimedRotatingFileHandler(
                            "logs/wvote.log", when="W0", backupCount=10),
                        logging.StreamHandler()
                    ])

loop = asyncio.get_event_loop()


bot_task = loop.create_task(bot.start())
http_task = loop.create_task(http_server.start_http())

loop.run_forever()
