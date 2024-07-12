import discord
import functools as ft
from datetime import datetime
from discord.ext import commands
from ayase.bot import Bot, Context
from ayase.models import Edition, User, Card
from ayase.utils import merge, img_to_buf, get_or_create
from sqlalchemy import Engine, select, update
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func

drops: dict[int, tuple[Edition]] = {}


class DropButton(discord.ui.Button):
    def __init__(self, engine: Engine, index: int):
        super().__init__(style=discord.ButtonStyle.secondary, label=str(index + 1))
        self.engine = engine
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        choice = drops[interaction.message.id][self.index]
        with Session(self.engine) as session:
            user = get_or_create(session, User, {"id": interaction.user.id})
            if user.last_grab:
                time = 600 - (datetime.now() - user.last_grab).seconds
                if time > 0:
                    await interaction.response.send_message(f"You must wait `{time // 60}m` before grabbing again.")
                    return
            user.last_grab = datetime.now()
            session.add(Card(
                edition_id=choice.id,
                user_id=interaction.user.id,
            ))
            session.commit()
        await interaction.response.send_message(choice.character.name)


class Drop(discord.ui.View):
    def __init__(self, engine: Engine):
        super().__init__()
        for i in range(3):
            self.add_item(DropButton(engine, i))


class Cards(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.engine = bot.engine

    @commands.is_owner()
    @commands.hybrid_command(aliases=["!rcd"])
    async def refresh_cooldowns(self, ctx: Context):
        with ctx.session as session:
            session.execute(update(User).values(last_drop=None, last_grab=None))
            session.commit()
        await ctx.send("🔃 Cooldowns reset!")

    @commands.hybrid_command(aliases=["d"])
    async def drop(self, ctx: Context):
        user = get_or_create(ctx.session, User, {"id": ctx.author.id})
        if user.last_drop:
            time = 1800 - (datetime.now() - user.last_drop).seconds
            if time > 0:
                await ctx.send(f"You must wait `{time // 60}m` before dropping again.")
                return
        user.last_drop = datetime.now()
        ctx.session.commit()
        query = select(Edition).order_by(func.random()).limit(3)
        chars = tuple(ctx.session.scalars(query))
        images = [Card(edition_id=char.id, edition=char).image for char in chars]
        choices = img_to_buf(ft.reduce(merge, images))

        message = await ctx.send(file=discord.File(choices, "drop.png"), view=Drop(self.engine))
        drops[message.id] = chars

    @commands.hybrid_command(aliases=["c"])
    async def collection(self, ctx: Context):
        query = select(Card).where(Card.user_id == ctx.author.id)
        cards = ctx.session.scalars(query)
        embed = discord.Embed(title="Collection")
        embed.add_field(name="", value="\n".join([card.display() for card in cards]))
        await ctx.send(embed=embed)

    @commands.hybrid_command(aliases=["v"])
    async def view(self, ctx: Context, card: Card):
        embed = discord.Embed(title="Card Details")
        embed.add_field(name="", value=card.display())
        embed.set_image(url=f"attachment://{card.id}.png")
        await ctx.send(embed=embed, file=discord.File(img_to_buf(card.image), f"{card.id}.png"))


async def setup(bot: Bot):
    await bot.add_cog(Cards(bot))
