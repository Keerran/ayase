from __future__ import annotations
import string
from discord.ext import commands
from PIL import Image
from ayase.bot import Context
from sqlalchemy import String, BigInteger, Integer, DateTime, ForeignKey, MetaData
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint
from datetime import datetime

digits = string.digits + string.ascii_lowercase


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
    anilist: Mapped[int] = mapped_column(Integer(), nullable=True)


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())
    gender: Mapped[str] = mapped_column(String())
    anilist: Mapped[str] = mapped_column(Integer(), nullable=True)
    media_id: Mapped[int] = mapped_column(ForeignKey("medias.id"))

    media: Mapped[Media] = relationship()


class Edition(Base):
    __tablename__ = "editions"

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id"))
    num: Mapped[int] = mapped_column(Integer())
    image: Mapped[str] = mapped_column(String())

    character: Mapped[Character] = relationship()

    __table_args__ = (UniqueConstraint("character_id", "num"),)


class Frame(Base):
    __tablename__ = "frames"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(), unique=True)
    image: Mapped[str] = mapped_column(String(), unique=True)


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("editions.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    frame_id: Mapped[int] = mapped_column(ForeignKey("frames.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())

    edition: Mapped[Edition] = relationship()
    frame: Mapped[Frame] = relationship()

    @property
    def image(self) -> Image:
        frame_image = self.frame.image if self.frame else f"frames/ed{self.edition.num}.png"
        frame = Image.open(frame_image)
        char = Image.open(self.edition.image)
        img = Image.new("RGBA", frame.size)
        img.paste(char, (27, 86))
        img.paste(frame, (0, 0), mask=frame)
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
            result += digits[r]
        return result.zfill(6)

    @classmethod
    async def convert(cls: type, ctx: Context, slug: str) -> Card:
        try:
            id = int(slug, len(digits))
        except ValueError:
            raise commands.BadArgument()
        session = Session(ctx.engine)
        card = session.get(Card, id)
        if card is None:
            raise commands.BadArgument()
        return card

    def display(self) -> str:
        return f"`{self.slug}` {self.character.name}"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    last_drop: Mapped[datetime] = mapped_column(DateTime(), nullable=True)
    last_grab: Mapped[datetime] = mapped_column(DateTime(), nullable=True)
