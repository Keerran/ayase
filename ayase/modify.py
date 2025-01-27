from ayase.utils import pass_engine
from ayase.models import Character
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, joinedload
import click
from ayase.models import Media


def intinput(prompt: str) -> int | None:
    while True:
        val = input(prompt)
        if val == "":
            return None
        elif val.isnumeric():
            return int(val)


@click.group()
def modify():
    pass


@modify.command()
@pass_engine
@click.option("--name", "-n", type=str)
@click.option("--media", "-m", type=str)
def names(engine: Engine, name: str, media: str):
    query = select(Character).options(joinedload(Character.aliases))

    if not name and not media:
        raise click.UsageError("You must specify at least one of --name or --media")

    if name:
        query = query.where(Character.name == name)

    if media:
        query = query.where(Character.media.has(Media.title == media))

    with Session(engine) as session:
        characters = session.scalars(query).unique().all()

        for character in characters:
            assert isinstance(character, Character)
            if not character.aliases:
                continue

            print(character.name)
            for i, alias in enumerate(character.aliases):
                print(f"{i + 1}) {alias.name}")

            index = intinput("Select an alias: ")
            if index is None:
                continue
            alias = character.aliases[index - 1]
            character.name, alias.name = alias.name, character.name

        session.commit()
