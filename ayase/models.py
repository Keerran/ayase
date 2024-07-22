from __future__ import annotations
import string
import discord
from os import path
from discord.ext import commands
from PIL import Image, ImageFont
from ayase.bot import Context
from sqlalchemy import String, BigInteger, Integer, Boolean, DateTime, ForeignKey, MetaData
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime
import json

digits = string.digits + string.ascii_lowercase
with open("frames/boxes.json") as f:
    boxes = json.load(f)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_`%(constraint_name)s`",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

    def __repr__(self):
        values = [f"{k}={v!r}" for k, v in self.__dict__.items() if not k.startswith("_")]
        return f"{self.__class__.__name__}({', '.join(values)})"


class Media(Base):
    __tablename__ = "medias"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String())
    type: Mapped[str] = mapped_column(String())
    anilist: Mapped[int] = mapped_column(Integer(), nullable=True, unique=True)


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    gender: Mapped[str] = mapped_column(String())
    anilist: Mapped[str] = mapped_column(Integer(), nullable=True, unique=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("medias.id"))

    media: Mapped[Media] = relationship()
    editions: Mapped[list[Edition]] = relationship(back_populates="character")
    aliases: Mapped[list[Alias]] = relationship(back_populates="character")

    def display(self) -> str:
        return f"{self.media.title} · **{self.name}**"


class Alias(Base):
    __tablename__ = "aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    is_spoiler: Mapped[bool] = mapped_column(Boolean(), default=False)

    character: Mapped[Character] = relationship(back_populates="aliases")

    __table_args__ = (UniqueConstraint("character_id", "name"),)


class Edition(Base):
    __tablename__ = "editions"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    num: Mapped[int] = mapped_column(Integer())
    image: Mapped[str] = mapped_column(String())

    character: Mapped[Character] = relationship(back_populates="editions")

    __table_args__ = (UniqueConstraint("character_id", "num"),)

    def to_embed(self, *, title: str) -> discord.Embed:
        embed = discord.Embed(title="Character Lookup")
        embed.add_field(name="", value=f"Character: **{self.character.name}**")
        embed.set_thumbnail(url=f"attachment://{path.basename(self.image)}")
        return embed


class Frame(Base):
    __tablename__ = "frames"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(), unique=True)
    image: Mapped[str] = mapped_column(String(), unique=True)

    @classmethod
    async def convert(cls: type, ctx: Context, name: str) -> Frame:
        try:
            return ctx.session.query(Frame).filter(Frame.name.ilike(name)).one()
        except NoResultFound:
            raise commands.BadArgument()


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("editions.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    frame_id: Mapped[int] = mapped_column(ForeignKey("frames.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    grabbed_by: Mapped[int] = mapped_column(ForeignKey("users.id"), default=lambda ctx: ctx.get_current_parameters()["user_id"])

    edition: Mapped[Edition] = relationship()
    frame: Mapped[Frame] = relationship()

    @property
    def image(self) -> Image:
        frame_image = self.frame.image if self.frame else f"frames/ed{self.edition.num}.png"
        mask_image = frame_image.replace(".png", "mask.png")

        mask = Image.open(mask_image) if path.isfile(mask_image) else None
        frame = Image.open(frame_image).convert("RGBA")
        char = Image.open(self.edition.image).convert("RGBA")
        if mask:
            mask = mask.crop((27, 86, 27 + char.size[0], 86 + char.size[1]))

        img = Image.new("RGBA", frame.size)
        img.paste(char, (27, 86), mask=mask)
        img.paste(frame, (0, 0), mask=frame)

        if info := boxes.get(path.basename(frame_image), None):
            from ayase.utils import fit_text

            top, bottom = info["top"], info["bottom"]
            font = ImageFont.truetype("frames/JosefinSans.ttf")
            top_img = fit_text(top, self.character.name, font)
            bot_img = fit_text(bottom, self.character.media.title, font)
            img.paste(top_img, (top["x"], top["y"]), mask=top_img)
            img.paste(bot_img, (bottom["x"], bottom["y"]), mask=bot_img)

        return img

    @property
    def character(self) -> Character:
        return self.edition.character

    @property
    def slug(self) -> str:
        n = self.id
        base = len(digits)
        if n == 0:
            return "0"
        result = ""
        while n:
            n, r = divmod(n, base)
            result = digits[r] + result
        return result.zfill(6)

    @classmethod
    async def convert(cls: type, ctx: Context, slug: str) -> Card:
        try:
            id = int(slug, len(digits))
        except ValueError:
            raise commands.BadArgument()
        card = ctx.session.get(Card, id)
        if card is None:
            raise commands.BadArgument()
        return card

    def display(self) -> str:
        return f"`{self.slug}` · `◈{self.edition.num}` · {self.character.media.title} · **{self.character.name}**"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    last_drop: Mapped[datetime] = mapped_column(DateTime(), nullable=True)
    last_grab: Mapped[datetime] = mapped_column(DateTime(), nullable=True)

    @property
    def drop_cooldown(self) -> int:
        if self.last_drop is None:
            return 0
        return 1800 - (datetime.now() - self.last_drop).seconds

    @property
    def grab_cooldown(self) -> int:
        if self.last_grab is None:
            return 0
        return 600 - (datetime.now() - self.last_grab).seconds
