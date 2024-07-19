import io
import click
import itertools as it
from PIL import Image, ImageDraw, ImageFont
from typing import TypeVar, Iterable, Iterator
from discord.ext import commands
from ayase.bot import Context
from ayase.models import Card
from sqlalchemy import Engine
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session, DeclarativeBase

T = TypeVar("T")
B = TypeVar("B", bound=DeclarativeBase)


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


def get_or_create(session: Session, model: type[B], index: dict, defaults: dict = None) -> B:
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


def wrap_text(draw: ImageDraw, text: str, width: int, font: ImageFont) -> str:
    lines = []
    words = text.split()
    current_line = []

    for word in words:
        new_line = " ".join(current_line + [word])
        new_width = font.getlength(new_line)

        if new_width <= width:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]

    lines.append(" ".join(current_line))

    return "\n".join([line for line in lines if line])


def fit_text(box: dict[str, float], text: str, font: ImageFont) -> Image:
    w, h = box["width"], box["height"]
    im = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(im)
    font_size = 100
    size = None
    while (size is None or size[0] > w or size[1] > h) and font_size > 0:
        font = font.font_variant(size=font_size)
        font.set_variation_by_axes([700])
        wrapped = wrap_text(draw, text, w, font)
        (x0, y0, x1, y1) = draw.multiline_textbbox((w / 2, h / 2), wrapped, font=font, anchor="mm", align="center")
        size = (x1 - x0, y1 - y0)
        font_size -= 1

    wrapped = wrap_text(draw, text, w, font)
    draw.multiline_text((w / 2, h / 2), wrapped, font=font, fill="black", anchor="mm", align="center")

    return im


def get_latest_card(ctx: Context) -> Card:
    return ctx.session.query(Card)\
        .filter(Card.user_id == ctx.author.id)\
        .order_by(Card.id.desc())\
        .first()


def batched(iterable: Iterable[T], n: int) -> Iterator[Iterable[T]]:
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    iterator = iter(iterable)
    while batch := tuple(it.islice(iterator, n)):
        yield batch


pass_engine = click.make_pass_decorator(Engine)

LatestCard = commands.parameter(
    default=get_latest_card,
    displayed_default="<latest card>",
)
