import os
import asyncio
import discord
from ayase.bot import Bot
from dotenv import load_dotenv


async def run_bot():
    load_dotenv()
    bot = Bot()
    await bot.start(os.getenv("DISCORD_TOKEN"))


def main():
    discord.utils.setup_logging()
    asyncio.run(run_bot())
