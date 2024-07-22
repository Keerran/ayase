from functional import seq
from io import BytesIO
from PIL import Image
from sqlalchemy import Engine, select, delete
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from ayase.utils import pass_engine, upsert
from ayase.models import Media, Character, Edition, Alias
from tqdm import tqdm
from pathlib import Path
from typing import Any
from os import path
from typing import TextIO
import click
import time
import requests
import re

JAPANESE_CHARACTERS = r"[\u3000-\u303F]|[\u3040-\u309F]|[\u30A0-\u30FF]|[\uFF00-\uFFEF]|[\u4E00-\u9FAF]"
KOREAN_CHARACTERS = r"[\uAC00-\uD7A3]"
REGEX = re.compile(JAPANESE_CHARACTERS + "|" + KOREAN_CHARACTERS)


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
    aliases = [Alias(name=name) for name in set(char["name"]["alternative"]) if REGEX.search(name) is None]
    spoiler_aliases = [Alias(name=name, is_spoiler=True) for name in set(char["name"]["alternativeSpoiler"]) if REGEX.search(name) is None]
    return {
        "name": flatten_name(char["name"]).strip(),
        "gender": char["gender"] or "",
        "anilist": char["id"],
        "media_id": medias[node["id"]].id,
        "aliases": aliases + spoiler_aliases
    }


@characters.command("update")
@pass_engine
def update(engine: Engine):
    session = Session(engine)
    with open(Path(__file__).with_name("update.gql"), "r") as f:
        query = f.read()
    page = 1
    ids = session.scalars(select(Character.anilist)).all()
    results = []
    for _ in tqdm(range((len(ids) // 100) + 1)):
        res = anilist_request({
            "query": query,
            "variables": {
                "characters": ids,
                "page": page,
                "perPage": 100,
            }
        })
        results.extend(res["Page"]["characters"])
        page += 1
        if not res["Page"]["pageInfo"]["hasNextPage"]:
            break
    for char in results:
        char["media"] = get_original_media(char["media"]["edges"])
    return results


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
        medias = {
            node["id"]: {
                "title": flatten_title(node["title"]),
                "type": node["type"],
                "anilist": node["id"],
            }
            for node in nodes
        }
        existing = session.scalars(select(Media).where(Media.anilist.in_([media["anilist"] for media in medias.values()])))
        medias = session.scalars(
            upsert(Media, list(medias.values()), ["anilist"], ["title", "type"]).returning(Media)
        )
        medias = {media.anilist: media for media in medias.all() + existing.all()}
        characters = [
            char
            for char in tqdm(seq(characters)
                             .zip(nodes)
                             .map(lambda p: create_character(medias, p[0], p[1])), total=len(characters))
        ]
        session.execute(delete(Alias))
        aliases = {char["anilist"]: char.pop("aliases") for char in characters}
        existing = session.query(Character).filter(Character.anilist.in_([char["anilist"] for char in characters])).all()
        characters = existing + session.scalars(
            upsert(Character, characters, ["anilist"], ["name", "gender"]).returning(Character)
        ).all()

        for char in characters:
            char.aliases = aliases[char.anilist]

        editions = [
            {
                "character_id": char.id,
                "num": 1,
                "image": f"images/{char.name}_1.png",
            }
            for char in characters
        ]
        session.execute(insert(Edition).on_conflict_do_nothing(constraint="uq_editions_character_id").values(editions))
        session.commit()
