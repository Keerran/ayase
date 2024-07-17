from discord.ext import commands
from ayase.bot import Bot, Context


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_check(self, ctx: Context) -> bool:
        return await self.bot.is_owner(ctx.author.id)

    @commands.hybrid_command(aliases=["!r"])
    async def reload(self, ctx: Context, cog: str):
        await self.bot.reload_extension(cog)
        await ctx.send(f"🔃 {cog} reloaded!")


async def setup(bot: Bot):
    await bot.add_cog(Admin(bot))
