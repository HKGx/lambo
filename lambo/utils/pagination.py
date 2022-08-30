from ast import Call
from math import ceil
from typing import Callable, Generic, TypeVar

from discord import ButtonStyle, Interaction, Message
from discord.ext.commands import Context
from discord.ui import Button, View, button

T = TypeVar("T")


class Paginator(Generic[T]):
    _current_page: int = 1
    _display: Callable[[T], str] = str
    _join: Callable[[list[str]], str] = "\n".join
    _page_cache: tuple[int, str] | None = None
    _per_page: int = 10
    _wrap_left: str = ""
    _wrap_right: str = ""
    values: list[T]

    def __init__(
        self,
        values: list[T],
        *,
        current_page: int | None = None,
        join: Callable[[list[str]], str] | None = None,
        display: Callable[[T], str] | None = None,
        per_page: int | None = None,
        wrap_around: tuple[str, str] | str | None = None,
    ) -> None:
        self.values = values
        if current_page:
            self._current_page = current_page
        if join:
            self._join = join
        if display:
            self._display = display
        if per_page:
            self._per_page = per_page
        if wrap_around and isinstance(wrap_around, tuple):
            self._wrap_left, self._wrap_right = wrap_around
        elif wrap_around:
            self._wrap_left = self._wrap_right = wrap_around

    def page(self) -> str:
        if self._page_cache:
            cached_page, page = self._page_cache
            if self._current_page == cached_page:
                return page
        start_index = (self._current_page - 1) * self._per_page
        end_index = start_index + self._per_page
        display = self._display
        page = self._join(
            [display(value) for value in self.values[start_index:end_index]]
        )
        wrapped_page = f"{self._wrap_left}{page}{self._wrap_right}"
        self._page_cache = (self._current_page, wrapped_page)
        return wrapped_page

    @property
    def can_go_back(self) -> bool:
        return self._current_page > 1

    def go_back(self):
        if self.can_go_back:
            self._current_page -= 1

    @property
    def can_go_forward(self) -> bool:
        return self._current_page < self.all_pages_count

    def go_forward(self):
        if self.can_go_forward:
            self._current_page += 1

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def all_pages_count(self) -> int:
        return ceil(len(self.values) / self._per_page)


class PaginatorView(Generic[T], View):
    _paginator: Paginator[T]

    def get_indicator(self) -> str:
        return f"{self._paginator.current_page}/{self._paginator.all_pages_count}"

    def __init__(self, paginator: Paginator[T]) -> None:
        print("8")
        super().__init__()
        print("9")
        self._paginator = paginator
        print("10")
        self.page_indicator.label = self.get_indicator()
        self.go_back.disabled = not self._paginator.can_go_back
        self.go_forward.disabled = not self._paginator.can_go_forward
        print("11")

    @button(label="◀", style=ButtonStyle.blurple)
    async def go_back(self, interaction: Interaction, button: Button):
        if self._paginator.can_go_back:
            self._paginator.go_back()
            self.page_indicator.label = self.get_indicator()
        if not self._paginator.can_go_back:
            button.disabled = True
        await interaction.edit_original_message(
            content=self._paginator.page(), view=self
        )

    @button(label="0/0", style=ButtonStyle.blurple, disabled=True)
    async def page_indicator(self, interaction: Interaction, button: Button):
        pass

    @button(label="▶", style=ButtonStyle.blurple)
    async def go_forward(self, interaction: Interaction, button: Button):
        if self._paginator.can_go_forward:
            self._paginator.go_forward()
            self.page_indicator.label = self.get_indicator()
        if not self._paginator.can_go_forward:
            button.disabled = True
        await interaction.edit_original_message(
            content=self._paginator.page(), view=self
        )

    async def send(self, ctx: Context) -> Message:
        return await ctx.send(content=self._paginator.page(), view=self)
