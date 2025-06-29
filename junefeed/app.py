from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.screen import Screen
from textual import events

from typing import Optional

from junefeed.feed import EntryCollection, Entry, Feed
from junefeed.config import config


class FeedScreen(Screen):
    def __init__(self):
        super().__init__()
        self.feeds = [Feed(url, name) for (name, url) in config.feeds.items()]

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        self.widgets = []
        for feed in self.feeds:
            widget = Static(str(feed))
            widget.styles.text_wrap = 'nowrap'
            widget.styles.text_overflow = 'clip'
            self.widgets.append(widget)
        yield from self.widgets


class EntryCollectionScreen(Screen):
    def __init__(self, from_cached=True):
        super().__init__()
        if from_cached:
            self.entry_collection = EntryCollection.from_cached()
        else:
            self.entry_collection = EntryCollection.from_feeds(config.feeds)
        self.read_entries = []

    @property
    def nwidgets(self) -> int:
        return len(self.widgets)
     
    @property
    def current_entry(self) -> Optional['Entry']:
        return self[self.idx]

    def _entry_to_widget(self, entry, idx):
        pad = self._feedpad
        widget = Static(f'[#6e6a86]{idx:>4}. {entry.feed:>{pad}}[/] {entry.title}')
        widget.styles.text_wrap = 'nowrap'
        widget.styles.text_overflow = 'clip'
        if not entry.is_read:
            widget.styles.color = '#908caa'
        else:
            widget.styles.color = '#6e6a86'
        return widget

    def build_widgets(self):
        self._feedpad = max(len(feed) for feed in config.feeds.keys())
        self.widgets = []
        for i, entry in enumerate(self.entry_collection, 1):
            widget = self._entry_to_widget(entry, i)
            self.widgets.append(widget)

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        self.build_widgets()
        self.idx = 0
        yield from self.widgets

    def on_mount(self):
        self.screen.show_horizontal_scrollbar = True
        self.screen.styles.scrollbar_size_horizontal = 10
        self.screen.styles.scrollbar_size_vertical = 0
        self.highlight_current()

    def on_key(self, event: events.Key) -> None:
        if event.key == 'j':
            self.idx += 1
            if self.idx >= 11:
                self.scroll_down()
            self.highlight_current()
        elif event.key == 'k':
            self.idx -= 1
            if self.idx <= self.nwidgets - 11:
                self.scroll_up()
            self.highlight_current()

    def highlight_current(self):
        if self.nwidgets == 0:
            return
        if self.idx < 0:
            self.idx = 0
        elif self.idx >= self.nwidgets - 1:
            self.idx = self.nwidgets - 1
            self.widgets[self.idx - 1].styles.color = '#908caa'
        else:
            self.widgets[self.idx - 1].styles.color = '#908caa'
            self.widgets[self.idx + 1].styles.color = '#908caa'
        self.widgets[self.idx].styles.color = '#f6c177'

    def mark_read(self):
        if self.nwidgets == 0:
            return
        entry = self.entry_collection.entries.pop(self.idx)
        entry.mark_read()
        self.read_entries.append(entry)
        self.widgets.pop(self.idx).remove()
        self.highlight_current()
    
    def __getitem__(self, idx) -> Optional['Entry']:
        """Get entry by index."""
        if len(self.entry_collection) == 0:
            return None
        else:
            return self.entry_collection.entries[idx]


class SingleEntryScreen(Screen):
    def __init__(self, entry: Entry):
        super().__init__()
        self.entry = entry

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        self.widget = Static(str(self.entry))
        yield self.widget


class Junefeed(App):
    BINDINGS = [
        ('c', 'push_screen("entry_collection")'),
        ('f', 'push_screen("feeds")'),
    ]

    def on_mount(self) -> None:
        self.install_screen(EntryCollectionScreen(), 'entry_collection')
        self.install_screen(FeedScreen(), 'feeds')
        self.push_screen('entry_collection')

    async def refresh_feeds(self) -> None:
        entry_collection = EntryCollectionScreen(from_cached=False)
        await self.push_screen(entry_collection)

    async def switch_to_entry(self) -> None:
        entry_collection = self.screen
        assert isinstance(entry_collection, EntryCollectionScreen), type(
            entry_collection
        )
        single_entry = SingleEntryScreen(entry_collection.current_entry)
        await self.push_screen(single_entry)

    def open_entry_link(self) -> None:
        entry_screen = self.screen
        assert isinstance(entry_screen, SingleEntryScreen)
        self.open_url(entry_screen.entry.link)

    async def on_key(self, event: events.Key) -> None:
        # Universal keys:
        if event.key == 'r':
            await self.refresh_feeds()
        if isinstance(self.screen, SingleEntryScreen):
            if event.key == 'c':
                await self.pop_screen()
            elif event.key == 'o':
                self.open_entry_link()
            elif event.key == 'q':
                await self.pop_screen()
        elif isinstance(self.screen, EntryCollectionScreen):
            if event.key == 'o':
                await self.switch_to_entry()
            elif event.key == 'm':
                self.screen.mark_read()
            elif event.key == 'q':
                self.exit()
        elif isinstance(self.screen, FeedScreen):
            if event.key == 'q':
                await self.pop_screen()
