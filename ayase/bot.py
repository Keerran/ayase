import os
import discord
from discord.ext import commands
from sqlalchemy import create_engine

extensions = [
    "cogs.cards",
    "cogs.misc",
]


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="d", intents=intents)
        self.engine = create_engine(os.getenv("DATABASE_URL"))

    async def setup_hook(self):
        for ext in extensions:
            await self.load_extension(ext)
