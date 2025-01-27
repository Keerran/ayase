import os
import json
import asyncio
import discord
import click
from typing import TextIO
from ayase.labelling import labels
from ayase.bot import Bot
from ayase.models import Frame
from ayase.scrape import characters
from ayase.utils import pass_engine
from dotenv import load_dotenv
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from ayase.modify import modify


async def run_bot(engine: Engine):
    load_dotenv()
    bot = Bot(engine)
    await bot.start(os.getenv("DISCORD_TOKEN"))


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    load_dotenv()
    ctx.obj = create_engine(os.getenv("DATABASE_URL"))
    if not ctx.invoked_subcommand:
        discord.utils.setup_logging()
        asyncio.run(run_bot(ctx.obj))


@cli.group()
def add():
    pass


@add.command()
@click.argument("file", type=click.File("r"))
@pass_engine
def frames(engine: Engine, file: TextIO):
    frames = json.load(file)

    rows = [Frame(name=name, image=f"frames/{image}") for name, image in frames.items()]

    with Session(engine) as session:
        session.add_all(rows)
        session.commit()


cli.add_command(modify)
add.add_command(characters)
add.add_command(labels)
