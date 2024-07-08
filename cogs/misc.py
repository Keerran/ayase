from discord.ext import commands
from ayase.bot import Bot


class Misc(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.hybrid_command()
    async def ping(self, ctx: commands.Context):
        await ctx.send("Pong!")


async def setup(bot: Bot):
    await bot.add_cog(Misc(bot))
