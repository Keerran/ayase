import os
import asyncio
import discord
from ayase.bot import Bot
from dotenv import load_dotenv


async def main():
    load_dotenv()
    bot = Bot()
    await bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    discord.utils.setup_logging()
    asyncio.run(main())
