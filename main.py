import os
import discord
import functools as ft
from datetime import datetime
from ayase.utils import merge, img_to_buf, get_or_create
from ayase.models import Edition, Card, User
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
        with Session(bot.engine) as session:
            user = get_or_create(session, User, {"id": interaction.user.id})
            if user.last_grab:
                time = 600 - (datetime.now() - user.last_grab).seconds
                if time > 0:
                    await interaction.response.send_message(f"You must wait `{time // 60}m` before grabbing again.")
                    return
            user.last_grab = datetime.now()
            session.add(Card(
                edition_id=choice.id,
                user_id=interaction.user.id,
            ))
            session.commit()
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
    user = get_or_create(session, User, {"id": ctx.author.id})
    if user.last_drop:
        time = 1800 - (datetime.now() - user.last_drop).seconds
        if time > 0:
            await ctx.send(f"You must wait `{time // 60}m` before dropping again.")
            return
    user.last_drop = datetime.now()
    session.commit()
    query = select(Edition).order_by(func.random()).limit(3)
    chars = tuple(session.scalars(query))
    images = [Image.open(char.image) for char in chars]
    choices = img_to_buf(ft.reduce(merge, images))

    message = await ctx.send(file=discord.File(choices, "drop.png"), view=Drop())
    drops[message.id] = chars


@bot.hybrid_command(aliases=["c"])
async def collection(ctx: commands.Context):
    session = Session(bot.engine)
    query = select(Card).where(Card.user_id == ctx.author.id)
    cards = session.scalars(query)
    embed = discord.Embed()
    embed.add_field(name="Collection", value="\n".join([card.edition.character.name for card in cards]))
    await ctx.send(embed=embed)


bot.run(os.getenv("DISCORD_TOKEN"))
