import os
import json
import asyncio
import discord
import click
from typing import TextIO
from ayase.bot import Bot
from ayase.models import Frame
from ayase.scrape import scrape_characters
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


async def run_bot():
    load_dotenv()
    bot = Bot()
    await bot.start(os.getenv("DISCORD_TOKEN"))


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    load_dotenv()
    if not ctx.invoked_subcommand:
        discord.utils.setup_logging()
        asyncio.run(run_bot())


@cli.group("add")
def add():
    pass


@add.command("frames")
@click.argument("file", type=click.File("r"))
def import_frames(file: TextIO):
    frames = json.load(file)
    engine = create_engine(os.getenv("DATABASE_URL"))

    rows = [Frame(name=name, image=f"frames/{image}") for name, image in frames.items()]

    with Session(engine) as session:
        session.add_all(rows)
        session.commit()


@add.command("characters")
@click.argument("amount", type=int)
def import_characters(amount: int):
    scrape_characters(amount)
