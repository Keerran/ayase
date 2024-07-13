import io
from PIL import Image
from typing import TypeVar
from discord.ext import commands
from ayase.models import Card
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, DeclarativeBase

T = TypeVar("T", bound=DeclarativeBase)


def merge(im1: Image, im2: Image):
    w = im1.size[0] + im2.size[0]
    h = max(im1.size[1], im2.size[1])
    im = Image.new("RGBA", (w, h))

    im.paste(im1)
    im.paste(im2, (im1.size[0], 0))

    return im


def img_to_buf(img: Image, format="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf


def get_or_create(session: Session, model: type[T], index: dict, defaults: dict = None) -> T:
    try:
        return session.query(model).filter_by(**index).one()
    except NoResultFound:
        if defaults is not None:
            index.update(defaults)
        item = model(**index)
        session.add(item)
        session.commit()
        return item


def check_owns_card(card: Card, user_id: int):
    if card.user_id != user_id:
        raise commands.BadArgument()
