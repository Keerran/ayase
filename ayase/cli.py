import os
import asyncio
import discord
import click
from ayase.bot import Bot
from dotenv import load_dotenv


async def run_bot():
    load_dotenv()
    bot = Bot()
    await bot.start(os.getenv("DISCORD_TOKEN"))


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
def main():
    discord.utils.setup_logging()
    asyncio.run(run_bot())
