from __future__ import annotations
import discord
from typing import Callable, TypeVar
from ayase.utils import batched

T = TypeVar("T")


class PageButton(discord.ui.Button):
    view: PaginatedView

    def __init__(self, label: str, modify_index: Callable[[int], int]):
        super().__init__(label=label, row=2)
        self.modify_index = modify_index

    async def callback(self, interaction: discord.Interaction):
        self.view.index = self.modify_index(self.view.index)
        await interaction.response.edit_message(embed=self.view.get_embed(), view=self.view)


class PaginatedView(discord.ui.View):
    data: list[list[T]]

    def __init__(self, data: list[T], *, title: str):
        super().__init__()
        self.title = title
        self.data = list(batched(data, 10))
        self.buttons = [
            PageButton("⏮️", lambda i: 0),
            PageButton("◀️", lambda i: i - 1),
            PageButton("▶️", lambda i: i + 1),
            PageButton("⏭️", lambda i: len(self.data) - 1),
        ]
        self.fill_items()
        self.index = 0

    def fill_items(self):
        for button in self.buttons:
            self.add_item(button)

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value: int):
        self._index = value
        first = value == 0
        self.buttons[0].disabled = first
        self.buttons[1].disabled = first

        last = value == len(self.data) - 1
        self.buttons[2].disabled = last
        self.buttons[3].disabled = last

    def get_embed(self):
        batch = self.data[self.index]
        embed = discord.Embed(title=self.title)
        embed.add_field(name="", value=self.format(batch))
        return embed

    def format(self, batch: list[T]) -> str:
        return "\n".join([str(x) for x in batch])


class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if original := interaction.message.reference:
            message = await interaction.channel.fetch_message(original.message_id)
            return interaction.user.id == message.author.id
        return true

    @discord.ui.button(label="❌")
    async def deny_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.deny(interaction)
        await interaction.response.edit_message(view=None)

    @discord.ui.button(label="✅")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.confirm(interaction)
        await interaction.response.edit_message(view=None)

    async def deny(self, interaction: discord.Interaction):
        pass

    async def confirm(self, interaction: discord.Interaction):
        pass


def confirm_view(callback: Callable[[discord.Interaction], None]) -> ConfirmView:
    class _Inner(ConfirmView):
        async def confirm(self, interaction: discord.Interaction):
            callback(interaction)

    return _Inner()
