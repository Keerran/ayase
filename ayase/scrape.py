from functional import seq
from io import BytesIO
from PIL import Image
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from ayase.utils import pass_engine
from ayase.models import Media, Character, Edition
from tqdm import tqdm
from pathlib import Path
from typing import Any
from os import path
from typing import TextIO
import click
import time
import requests


@click.group()
def characters():
    pass


def anilist_request(data: dict) -> dict:
    req = requests.post("https://graphql.anilist.co/", json=data)
    req.raise_for_status()
    limit = int(req.headers["X-RateLimit-Remaining"])
    if limit <= 1:
        for _ in tqdm(range(60), leave=False):
            time.sleep(1)

    return req.json()["data"]


def flatten_name(name: dict[str, str]) -> str:
    arr = [name["first"], name["middle"], name["last"]]
    return " ".join([n for n in arr if n is not None])


def flatten_title(title: dict[str, str]) -> str:
    return title["english"] or title["romaji"] or title["native"]


def get_original_media(medias: list[dict]) -> dict:
    try:
        return (
            seq(medias)
            .map(lambda e: e["node"])
            .filter(lambda n: n["source"] == "ORIGINAL")
            .first()
        )
    except IndexError:
        return medias[0]["node"]


def create_character(medias: dict[int, Media], char: dict, node: dict) -> dict:
    file = f"images/{flatten_name(char['name'])}_1.png"
    if not path.isfile(file):
        res = requests.get(char["image"]["large"])
        img = Image.open(BytesIO(res.content))
        img.save(file)
    return {
        "name": flatten_name(char["name"]),
        "gender": char["gender"] or "",
        "anilist": char["id"],
        "media_id": medias[node["id"]].id
    }


@characters.command("medias")
@click.argument("file", type=click.File("r"))
def medias(file: TextIO):
    with open(Path(__file__).with_name("animes.gql"), "r") as f:
        query = f.read()
    with file:
        medias = [int(id) for id in file.read().splitlines(keepends=False)]
    res = anilist_request({
        "query": query,
        "variables": {
            "medias": medias,
            "page": 1,
            "perPage": 100,
        }
    })
    characters = []
    for media in res["Page"]["media"]:
        new = media.pop("characters")["nodes"]
        for character in new:
            character["media"] = media

        characters.extend(new)

    return characters


@characters.command("top")
@click.argument("amount", type=int)
def top_characters(amount: int) -> dict[str, Any]:
    with open(Path(__file__).with_name("top.gql"), "r") as f:
        query = f.read()
    characters = []
    page = 1
    perPage = 100

    with tqdm(total=amount) as pbar:
        while len(characters) < amount:
            data = {
                "query": query,
                "variables": {
                    "page": page,
                    "perPage": perPage,
                }
            }
            page += 1
            res = anilist_request(data)
            new = res["Page"]["characters"]
            pbar.update(len(new))
            characters.extend(new)
    for char in characters:
        char["media"] = get_original_media(char["media"]["edges"])
    return characters


@characters.result_callback()
@pass_engine
def anilist_to_db(engine: Engine, characters: dict[str, Any]):
    with Session(engine) as session:
        nodes = [char["media"] for char in characters]
        medias = [
            {
                "title": flatten_title(node["title"]),
                "type": node["type"],
                "anilist": node["id"],
            }
            for node in nodes
        ]
        existing = session.scalars(select(Media).where(Media.anilist.in_([media["anilist"] for media in medias])))
        medias = session.scalars(insert(Media).values(medias).on_conflict_do_nothing(index_elements=["anilist"]).returning(Media))
        medias = {media.anilist: media for media in medias.all() + existing.all()}
        characters = [
            char
            for char in tqdm(seq(characters)
                             .zip(nodes)
                             .map(lambda p: create_character(medias, p[0], p[1])), total=len(characters))
        ]
        characters = session.scalars(insert(Character).on_conflict_do_nothing(index_elements=["anilist"]).values(characters).returning(Character))
        editions = [
            {
                "character_id": char.id,
                "num": 1,
                "image": f"images/{char.name}_1.png",
            }
            for char in characters
        ]
        session.execute(insert(Edition).values(editions))
        session.commit()
