import os
from ayase.bot import Bot
from dotenv import load_dotenv

load_dotenv()
bot = Bot()
bot.run(os.getenv("DISCORD_TOKEN"))
