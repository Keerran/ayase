from __future__ import annotations
import os
import discord
from discord.ext import commands
from sqlalchemy import Engine
from sqlalchemy.orm import Session

extensions = [
    "ayase.cogs.admin",
    "ayase.cogs.cards",
    "ayase.cogs.collection",
    "ayase.cogs.misc",
]


class Context(commands.Context):
    bot: Bot

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = self.bot.engine
        self.session = Session(self.engine)


class Bot(commands.Bot):
    def __init__(self, engine: Engine):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="d", intents=intents)
        self.engine = engine

    async def setup_hook(self):
        self.bot_info = await self.application_info()
        self.owner_id = self.bot_info.owner.id
        for ext in extensions:
            await self.load_extension(ext)

        await self.tree.sync()

    async def get_context(self, message, *, cls=Context):
        return await super().get_context(message, cls=cls)

    @commands.after_invoke
    async def close_session(self, ctx: Context):
        ctx.session.close()
