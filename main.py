import os
import asyncio
from ayase.bot import Bot
from dotenv import load_dotenv


async def main():
    load_dotenv()
    bot = Bot()
    await bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
