from typing import Optional
from asyncio import sleep

from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.screen import Screen
from textual import events, work


from junefeed.feed import EntryCollection, Entry, Feed
from junefeed.config import config


class Junefeed(App):
    """Junefeed is a terminal RSS reader.

    This class provides the core functionality for the Junefeed app. The user
    interface relies on three different screens: EntryCollectionScreen, which
    serves all of the entries for the feeds you have subscribed to. FeedScreen,
    which presents a simple list of subscribed feeds, and SingleEntryScreen,
    which displays more information on a given entry.
    """

    BINDINGS = [
        ('c', 'push_screen("entry_collection")'),
        ('f', 'push_screen("feeds")'),
    ]

    async def on_mount(self) -> None:
        self.install_screen(EntryCollectionScreen(), 'entry_collection')
        self.install_screen(FeedScreen(), 'feeds')
        self._prefetch_refreshed()
        self.push_screen('entry_collection')

    @work(exclusive=True)
    async def _prefetch_refreshed(self):
        self._refreshed_ec_screen = None
        refreshed_entry_collection = EntryCollection.from_feeds()
        self._refreshed_ec_screen = EntryCollectionScreen(
            await refreshed_entry_collection
        )

    async def refresh_feeds(self) -> None:
        """Fetches new data from the subscribed feeds."""
        while self._refreshed_ec_screen is None:
            await sleep(0.1)  # Wait for prefetch to complete
        self.pop_screen()
        self.push_screen(self._refreshed_ec_screen)
        self._refreshed_ec_screen = None
        self._prefetch_refreshed()

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
        """From a SingleEntryScreen, opens the associated link in the default
        web browser."""
        entry_screen = self.screen
        assert isinstance(entry_screen, SingleEntryScreen)
        self.open_url(entry_screen.entry.link)

    async def toggle_read(self):
        """Toggles display of entries marked as read."""
        current_ec_screen = self.screen
        assert isinstance(current_ec_screen, EntryCollectionScreen)
        new_idx = current_ec_screen.idx

        # Upon toggling:
        # If displaying read, move idx to the closest preceding unread entry.
        if current_ec_screen.display_read:
            num_hidden = 0
            for j in range(new_idx + 1):
                if current_ec_screen.entry_collection.entries[j].is_read:
                    num_hidden -= 1
            new_idx += num_hidden

        # Else, add all previously read entries to the current index.
        else:
            j = 0
            while j <= new_idx:
                if not current_ec_screen.entry_collection.entries[j].is_read:
                    j += 1
                    continue
                # Begin counting number of get_entries in current block
                k = j
                num_hidden = 0
                while current_ec_screen.entry_collection.entries[k].is_read:
                    num_hidden += 1
                    k += 1
                j += num_hidden
                new_idx += num_hidden

        # Instantiate the toggled screen and replace current.
        entry_collection_screen = EntryCollectionScreen(
            current_ec_screen.entry_collection,
            display_read=not current_ec_screen.display_read,
            idx=new_idx,
        )

        self.pop_screen()
        await self.push_screen(entry_collection_screen)
        entry_collection_screen.widgets[0].scroll_to_widget(
            entry_collection_screen.widgets[
                min(entry_collection_screen.nwidgets - 1, new_idx + 15)
            ],
            animate=False,
            immediate=True,
        )

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
            elif event.key == 'u':
                self.screen.mark_unread()
            elif event.key == 't':
                await self.toggle_read()
            elif event.key == 'q':
                self.screen.entry_collection.cache_entries()
                self.exit()
        elif isinstance(self.screen, FeedScreen):
            if event.key == 'q':
                self.get_screen(
                    'entry_collection', EntryCollectionScreen
                ).entry_collection.cache_entries()
                await self.pop_screen()


class EntryCollectionScreen(Screen):
    """The primary screen for browsing feed data.

    EntryCollectionScreen is the landing screen upon opening the app. It
    provides functionality for scrolling through reads, marking them as read or
    unread, and searching for specific keywords.

    Attributes:
        entry_collection: an EntryCollection instance containing all data from
        feeds. read_entry_collection: an EntryCollection instance containing
        entries marked as read. nwidgets: the number of currently availabe
        widgets. current_entry: the currently highlighted entry.
    """

    def __init__(
        self,
        entry_collection: Optional['EntryCollection'] = None,
        display_read: bool = False,
        idx: int = 0,
    ) -> None:
        """Initialize new EntryCollectionScreen instance."""
        super().__init__()
        if entry_collection is None:
            self.entry_collection = EntryCollection.from_cached()
        else:
            self.entry_collection = entry_collection
        self.display_read = display_read
        if not self.display_read:
            self.visible_entries = EntryCollection(
                [e for e in self.entry_collection if not e.is_read]
            )
        else:
            self.visible_entries = self.entry_collection
        self.idx = idx
        self._feedpad = max(len(feed) for feed in config.feeds.keys()) + 2

    @property
    def nwidgets(self) -> int:
        """Return the number of currently available widgets."""
        return len(self.widgets)

    @property
    def current_entry(self) -> Entry:
        """Return the currently active/highlighted entry."""
        entry = self[self.idx]
        if entry is None:
            raise ValueError(f'No entry found at index {self.idx}')
        return entry

    def entry_to_widget(self, entry):
        widget = Static(entry.oneliner(self._feedpad))
        widget.styles.text_wrap = 'nowrap'
        widget.styles.text_overflow = 'clip'
        return widget

    def build_widgets(self, entry_collection: EntryCollection) -> list:
        widgets = []
        for entry in entry_collection:
            if entry.is_read and self.display_read is False:
                continue
            widget = self.entry_to_widget(entry)
            widgets.append(widget)
        return widgets

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        self.widgets = self.build_widgets(self.visible_entries)
        yield from self.widgets

    def on_mount(self) -> None:
        self.screen.show_horizontal_scrollbar = True
        self.screen.styles.scrollbar_size_horizontal = 10
        self.screen.styles.scrollbar_size_vertical = 0
        self.highlight_current()

    def go_to(self):
        self.set_focus(self.widgets[self.idx])

    def on_key(self, event: events.Key) -> None:
        """Key-bindings for EntryCollectionScreen."""
        if event.key == 'j':
            self.idx += 1
            self.highlight_current()
            if self.idx >= 15:
                self.scroll_down()

        elif event.key == 'k':
            self.idx -= 1
            self.highlight_current()
            if self.idx <= self.nwidgets - 15:
                self.scroll_up()

    def highlight_current_old(self) -> None:
        """Highlight the currently active entry."""
        if self.nwidgets == 0:
            return
        if self.idx < 0:
            self.idx = 0
        elif self.idx >= self.nwidgets - 1:
            self.idx = self.nwidgets - 1
            above = self[self.idx - 1]
            if above is None:
                return
            self.widgets[self.idx - 1].update(above.oneliner(self._feedpad))
        else:
            above = self[self.idx - 1]
            if above is None:
                raise ValueError(f'No entry found at index {self.idx - 1}')
            below = self[self.idx + 1]
            if below is None:
                raise ValueError(f'No entry found at index {self.idx + 1}')
            self.widgets[self.idx - 1].update(above.oneliner(self._feedpad))
            self.widgets[self.idx + 1].update(below.oneliner(self._feedpad))
        current = self.current_entry
        self.widgets[self.idx].update(current.oneliner(self._feedpad, True))

    def highlight_current(self) -> None:
        """Highlight the currently active entry."""
        if self.nwidgets == 0:  # i.e. nothing to highlight
            return
        # Tether index to bounds of list
        if self.idx < 0:
            self.idx = 0
        elif self.idx >= self.nwidgets - 1:
            self.idx = self.nwidgets - 1

        above = self[self.idx - 1]
        below = self[self.idx + 1]
        current = self.current_entry

        # If idx is at start of list, do not update above, and vice versa.
        self.widgets[self.idx].update(current.oneliner(self._feedpad, True))
        if above is not None:
            self.widgets[self.idx - 1].update(above.oneliner(self._feedpad))
        if below is not None:
            self.widgets[self.idx + 1].update(below.oneliner(self._feedpad))

    def mark_read(self) -> None:
        """Mark the currently highlighted entry as read."""
        self.current_entry.mark_read()
        if self.display_read:
            self.widgets[self.idx].update(self.current_entry.oneliner(self._feedpad))
        else:
            self.widgets[self.idx].remove()
            self.widgets.pop(self.idx)
            self.visible_entries.pop(self.idx)
        self.highlight_current()

    def mark_unread(self) -> None:
        """Mark the currently highlighted entry as read."""
        self.current_entry.mark_unread()
        self.highlight_current()

    def __getitem__(self, idx) -> Optional['Entry']:
        """Get entry by index."""
        if len(self.visible_entries) == 0:
            return None
        elif idx >= len(self.visible_entries):
            return None
        else:
            return self.visible_entries.entries[idx]


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
