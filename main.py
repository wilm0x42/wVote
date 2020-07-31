#!/usr/bin/env python3

import asyncio

from aiohttp import web

import http_server
import bot
import compo

bot.load_config()

loop = asyncio.get_event_loop()

loop.create_task(bot.client.start(bot.client.bot_key))
loop.create_task(http_server.start_http())

loop.run_forever()