import os
import json
import asyncio
import discord
import click
from typing import TextIO
from ayase.bot import Bot
from ayase.models import Frame
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


async def run_bot():
    load_dotenv()
    bot = Bot()
    await bot.start(os.getenv("DISCORD_TOKEN"))


def import_frames(ctx: click.Context, param: click.Parameter, file: TextIO):
    load_dotenv()
    frames = json.load(file)
    engine = create_engine(os.getenv("DATABASE_URL"))

    rows = [Frame(name=name, image=f"frames/{image}") for name, image in frames.items()]

    with Session(engine) as session:
        session.add_all(rows)
        session.commit()

    ctx.exit()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("-f", "--frames", type=click.File("r"), callback=import_frames, is_eager=True, expose_value=True)
def cli():
    discord.utils.setup_logging()
    asyncio.run(run_bot())
