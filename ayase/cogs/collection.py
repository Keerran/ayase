from ayase.utils import LatestCard
import discord
import emoji
from typing import Annotated, Optional
from discord.ext import commands
from ayase.bot import Bot, Context
from ayase.models import Tag
from sqlalchemy import exc
from sqlalchemy import select
from ayase.views import PaginatedView, ConfirmView
from ayase.models import Card
from ayase.utils import check_owns_card
from ayase.models import Edition
from ayase.models import Character


class CollectionView(PaginatedView):
    def __init__(self, data: list[Card]):
        super().__init__(data, title="Collection")

    def format(self, batch: list[Card]):
        return "\n".join([card.display() for card in batch])


class BurnView(ConfirmView):
    def __init__(self, ctx: Context, card: Card):
        super().__init__()
        self.confirm_button.label = "🔥"

    async def confirm(self, interaction: discord.Interaction):
        await self.ctx.session.delete(self.card)
        await self.ctx.session.commit()


def unicode_emoji(arg: str):
    if not emoji.is_emoji(arg):
        raise commands.BadArgument()
    return arg


# move to different file for use elsewhere?
FILTERS = {}


def filter(aliases: Optional[list[str]] = None):
    def inner(f: callable):
        for alias in aliases or []:
            FILTERS[alias] = f
        FILTERS[f.__name__] = f
    return inner


@filter(["t"])
def tag(name: str):
    return Card.tag.has(name=name)


@filter(["c", "char"])
def character(name: str):
    return Card.edition.has(Edition.character.has(Character.name.icontains(name)))


class Collection(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.engine = bot.engine

    @commands.hybrid_command(aliases=["c"])
    async def collection(self, ctx: Context, user: Optional[discord.User] = commands.Author, *, filters: str = ""):
        # need to parse the filters way better than this...
        # maybe get sort out first, then parse each filter sequentially by split once-ing on =
        # will have to manually allow the first word to contain a = maybe
        try:
            filters = [f.split("=") for f in filters.split()]
            filters = [
                FILTERS[f[0]](f[1]) for f in filters
            ]
        except (KeyError, ValueError):
            raise commands.BadArgument()
        query = select(Card).where(Card.user_id == user.id, *filters)
        cards = ctx.session.scalars(query)
        view = CollectionView(cards)
        await ctx.send(embed=view.get_embed(), view=view)

    @commands.hybrid_command(aliases=["tc"])
    async def tag_create(self, ctx: Context, name: str, emoji: Annotated[str, unicode_emoji]):
        tag = Tag(user_id=ctx.author.id, name=name, emoji=emoji)
        ctx.session.add(tag)
        try:
            ctx.session.commit()
        except exc.IntegrityError:
            # TODO: handle duplicates
            return
        await ctx.send("✅ Tag created!")

    @commands.hybrid_command(aliases=["tl"])
    async def tag_list(self, ctx: Context):
        query = select(Tag).where(Tag.user_id == ctx.author.id)
        tags = ctx.session.scalars(query)
        lines = [
            f"{tag.emoji} `{tag.name}` · **{len(tag.cards)}** cards"
            for tag in tags
        ]
        view = PaginatedView(lines, title="Tags")
        await ctx.send(embed=view.get_embed(), view=view)

    @commands.hybrid_command(aliases=["t"])
    async def tag(self, ctx: Context, tag: Tag, card: Optional[Card] = LatestCard):
        check_owns_card(card, ctx.author.id)
        card.tag_id = tag.id
        ctx.session.commit()
        await ctx.reply(f"{ctx.author.mention}, the **{card.name}** has been tagged successfully.")

    @commands.hybrid_command(aliases=["tr"])
    async def tag_remove(self, ctx: Context, card: Optional[Card] = LatestCard):
        check_owns_card(card, ctx.author.id)
        card.tag_id = None
        ctx.session.commit()
        await ctx.reply(f"{ctx.author.mention}, the **{card.name}** has been untagged successfully.")

    @commands.hybrid_command(aliases=["b"])
    async def burn(self, ctx: Context, card: Optional[Card] = LatestCard):
        check_owns_card(card, ctx.author.id)
        view = BurnView(ctx, card)
        await ctx.reply("Burn?", view=view)


async def setup(bot: Bot):
    await bot.add_cog(Collection(bot))
