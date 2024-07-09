import discord
from discord.ext import commands
from ayase.bot import Bot


class Admin(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context) -> bool:
        return self.bot.is_owner(ctx.author.id)

    @commands.hybrid_command(aliases=["!r"])
    async def reload(self, ctx: commands.Context, cog: str):
        await self.bot.reload_extension(cog)
        ctx.send(f"🔃 {cog} reloaded!")


async def setup(bot: Bot):
    await bot.add_cog(Admin(bot))
