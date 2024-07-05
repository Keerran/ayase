from sqlalchemy import String, Integer, ForeignKey, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint


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
