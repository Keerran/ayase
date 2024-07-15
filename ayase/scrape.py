from functional import seq
from io import BytesIO
from PIL import Image
from sqlalchemy import create_engine, insert
from sqlalchemy.orm import Session
from ayase.models import Base, Media, Character, Edition
from tqdm import tqdm
from pathlib import Path
from os import path
import time
import requests
import os


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


def scrape_characters(amount: int):
    with open(Path(__file__).with_name("query.gql"), "r") as f:
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

            req = requests.post("https://graphql.anilist.co/", json=data)
            req.raise_for_status()
            limit = int(req.headers["X-RateLimit-Remaining"])
            if limit <= 1:
                for _ in tqdm(range(60), leave=False):
                    time.sleep(1)

            res = req.json()
            characters.extend(res["data"]["Page"]["characters"])
            pbar.update(perPage)

    engine = create_engine(os.getenv("DATABASE_URL"))

    with Session(engine) as session:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()

    with Session(engine) as session:
        nodes = [get_original_media(char["media"]["edges"]) for char in characters]
        medias = [
            {
                "title": flatten_title(node["title"]),
                "type": node["type"],
                "anilist": node["id"],
            }
            for node in nodes
        ]
        medias = session.scalars(insert(Media).values(medias).returning(Media))
        medias = {media.anilist: media for media in medias}
        characters = [
            char
            for char in tqdm(seq(characters)
                             .zip(nodes)
                             .map(lambda p: create_character(medias, p[0], p[1])), total=len(characters))
        ]
        characters = session.scalars(insert(Character).values(characters).returning(Character))
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
