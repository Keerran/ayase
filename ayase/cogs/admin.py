import discord
from discord.ext import commands
from ayase.bot import Bot, Context
from ayase.models import Character
from ayase.utils import get_or_create
from ayase.models import User, Card


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context) -> bool:
        return await self.bot.is_owner(ctx.author)

    @commands.hybrid_command(aliases=["!r"])
    async def reload(self, ctx: Context, cog: str):
        await self.bot.reload_extension(f"ayase.cogs.{cog}")
        await ctx.send(f"🔃 {cog} reloaded!")

    @commands.hybrid_command(aliases=["!s"])
    async def spawn(self, ctx: Context, recipient: discord.User, *, character: str):
        char = ctx.session.query(Character).filter(Character.name == character).one()
        char = char.editions[0]
        user = get_or_create(ctx.session, User, {"id": recipient.id})
        card = Card(
            edition_id=char.id,
            user_id=user.id,
        )
        ctx.session.add(card)
        ctx.session.commit()
        await recipient.send(f"{ctx.author.mention} gave you a **{char.character.name}** card `{card.slug}`!")


async def setup(bot: Bot):
    await bot.add_cog(Admin(bot))
