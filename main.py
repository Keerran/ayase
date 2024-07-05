import os
import discord
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from discord.ext import commands


class Bot(commands.Bot):
    def __init__(
        self,
        *args,
        engine: Engine,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.engine = engine


load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
intents = discord.Intents.default()
intents.message_content = True

bot = Bot(command_prefix="d", engine=engine, intents=intents)


@bot.hybrid_command()
async def ping(ctx: commands.Context):
    await ctx.send("Pong!")


bot.run(os.getenv("DISCORD_TOKEN"))
