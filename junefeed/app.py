from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.screen import Screen
from textual import events

from typing import Optional

from junefeed.feed import EntryCollection, Entry, Feed
from junefeed.config import config


class Junefeed(App):
    """Junefeed is a terminal RSS reader.

    This class provides the core functionality for the Junefeed app. The user interface relies on
    three different screens: EntryCollectionScreen, which serves all of the entries for the feeds
    you have subscribed to. FeedScreen, which presents a simple list of subscribed feeds, and
    SingleEntryScreen, which displays more information on a given entry.
    """

    BINDINGS = [
        ('c', 'push_screen("entry_collection")'),
        ('f', 'push_screen("feeds")'),
    ]

    def on_mount(self) -> None:
        self.install_screen(EntryCollectionScreen(), 'entry_collection')
        self.install_screen(FeedScreen(), 'feeds')
        self.push_screen('entry_collection')

    async def refresh_feeds(self) -> None:
        """Fetches new data from the subscribed feeds."""
        entry_collection = EntryCollectionScreen()
        await self.push_screen(entry_collection)

    async def switch_to_entry(self) -> None:
        """Switches to the currently active, highlighted entry."""
        entry_collection = self.screen
        assert isinstance(entry_collection, EntryCollectionScreen), type(
            entry_collection
        )
        current_entry = entry_collection.current_entry
        if current_entry is not None:
            await self.push_screen(SingleEntryScreen(current_entry))

    def open_entry_link(self) -> None:
        """From a SingleEntryScreen, opens the associated link in the default web browser."""
        entry_screen = self.screen
        assert isinstance(entry_screen, SingleEntryScreen)
        self.open_url(entry_screen.entry.link)

    async def on_key(self, event: events.Key) -> None:
        """Key-bindings for interacting with the Junefeed app.

        Attributes:
            event: an individual key-press event.
        """
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
            elif event.key == 't':
                if self.screen.display_read:
                    self.pop_screen()
                else:
                    entry_collection = self.screen.entry_collection
                    self.push_screen(
                        EntryCollectionScreen(entry_collection, display_read=True)
                    )
            elif event.key == 'q':
                self.exit()
        elif isinstance(self.screen, FeedScreen):
            if event.key == 'q':
                await self.pop_screen()


class EntryCollectionScreen(Screen):
    """The primary screen for browsing feed data.

    EntryCollectionScreen is the landing screen upon opening the app. It provides functionality for
    scrolling through reads, marking them as read or unread, and searching for specific keywords.

    Attributes:
        entry_collection: an EntryCollection instance containing all data from feeds.
        read_entry_collection: an EntryCollection instance containing entries marked as read.
        nwidgets: the number of currently availabe widgets.
        current_entry: the currently highlighted entry.
    """

    def __init__(
        self,
        entry_collection: Optional['EntryCollection'] = None,
        display_read: bool = False,
    ) -> None:
        """Initialize new EntryCollectionScreen instance."""
        super().__init__()
        if entry_collection is None:
            self.entry_collection = EntryCollection.from_cached()
        else:
            self.entry_collection = entry_collection
        self.display_read = display_read
        self._feedpad = max(len(feed) for feed in config.feeds.keys())

    @property
    def nwidgets(self) -> int:
        """Return the number of currently available widgets."""
        return len(self.widgets)

    @property
    def current_entry(self) -> Optional['Entry']:
        """Return the currently active/highlighted entry."""
        return self[self.idx]

    def entry_to_widget(self, entry, idx):
        widget = Static(
            f'[#6e6a86]{idx:>4}. {entry.feed:>{self._feedpad}}[/] {entry.title}'
        )
        widget.styles.text_wrap = 'nowrap'
        widget.styles.text_overflow = 'clip'
        if not entry.is_read:
            widget.styles.color = '#908caa'
        else:
            widget.styles.color = '#6e6a86'
        return widget

    def build_widgets(self, entry_collection: EntryCollection) -> list:
        widgets = []
        for i, entry in enumerate(entry_collection, 1):
            if entry.is_read and self.display_read is False:
                continue
            widget = self.entry_to_widget(entry, i)
            widgets.append(widget)
        return widgets

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        self.widgets = self.build_widgets(self.entry_collection)
        self.idx = 0
        yield from self.widgets

    def on_mount(self) -> None:
        self.screen.show_horizontal_scrollbar = True
        self.screen.styles.scrollbar_size_horizontal = 10
        self.screen.styles.scrollbar_size_vertical = 0
        self.highlight_current()

    def on_key(self, event: events.Key) -> None:
        """Key-bindings for EntryCollectionScreen."""
        if event.key == 'j':
            self.idx += 1
            if self.idx >= 15:
                self.scroll_down()
            self.highlight_current()
        elif event.key == 'k':
            self.idx -= 1
            if self.idx <= self.nwidgets - 15:
                self.scroll_up()
            self.highlight_current()

    def highlight_current(self) -> None:
        """Highlight the currently active entry."""
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

    def mark_read(self) -> None:
        """Mark the currently highlighted entry as read."""
        entry = self.entry_collection[self.idx]
        entry.mark_read()
        self.widgets[self.idx].remove()
        self.highlight_current()

    def toggle_unread(self) -> None:
        for i, entry in enumerate(self.entry_collection):
            if not entry.is_read:
                continue
            widget = self.entry_to_widget(entry, i)
            self.widgets[i].mount(widget)
            # self.widgets.insert(i, widget)

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
