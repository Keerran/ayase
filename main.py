import os
import io
import discord
import functools as ft
from ayase.utils import merge, img_to_buf
from ayase.models import Edition
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from discord.ext import commands
from PIL import Image

drops: dict[int, tuple[Edition]] = {}


class Bot(commands.Bot):
    def __init__(
        self,
        *args,
        engine: Engine,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.engine = engine


class DropButton(discord.ui.Button):
    def __init__(self, index: int):
        super().__init__(style=discord.ButtonStyle.secondary, label=str(index + 1))
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        choice = drops[interaction.message.id][self.index]
        await interaction.response.send_message(choice.character.name)


class Drop(discord.ui.View):
    def __init__(self):
        super().__init__()
        for i in range(3):
            self.add_item(DropButton(i))


load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
intents = discord.Intents.default()
intents.message_content = True

bot = Bot(command_prefix="d", engine=engine, intents=intents)


@bot.hybrid_command()
async def ping(ctx: commands.Context):
    await ctx.send("Pong!")


@bot.hybrid_command(aliases=["d"])
async def drop(ctx: commands.Context):
    session = Session(bot.engine)
    query = select(Edition).order_by(func.random()).limit(3)
    chars = tuple(session.scalars(query))
    images = [Image.open(char.image) for char in chars]
    choices = img_to_buf(ft.reduce(merge, images))
    message = await ctx.send(file=discord.File(choices, "drop.png"), view=Drop())
    drops[message.id] = chars


bot.run(os.getenv("DISCORD_TOKEN"))
