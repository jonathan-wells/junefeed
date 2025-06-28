from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.screen import Screen
from textual import events

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
            self.entries = EntryCollection.from_cached()
        else:
            self.entries = EntryCollection.from_feeds(config.feeds)
        self.read_entries = []
        self.build_widgets()
        self.idx = 0
    
    @property
    def nwidgets(self):
        return len(self.widgets)

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
        for i, entry in enumerate(self.entries, 1):
            widget = self._entry_to_widget(entry, i)
            self.widgets.append(widget)

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        yield from self.widgets 
 
    def on_mount(self):
        self.screen.show_horizontal_scrollbar = True
        self.screen.styles.scrollbar_size_horizontal = 10
        self.screen.styles.scrollbar_size_vertical = 0
        self.highlight_current()

    def on_key(self, event: events.Key) -> None:
        if event.key == 'h':
            self.scroll_left()
        elif event.key == 'j':
            self.idx += 1
            if self.idx >= 11:
                self.scroll_down()
            self.highlight_current()
        elif event.key == 'k':
            print('k')
            self.idx -= 1
            if self.idx < self.nwidgets - 12:
                self.scroll_up()
            self.highlight_current()
        elif event.key == 'l':
            self.scroll_right()
 
    def highlight_current(self):
        if self.nwidgets == 0:
            return
        if self.idx < 0:
            self.idx = 0
        elif self.idx >= self.nwidgets - 1:
            self.idx = self.nwidgets - 1
            self.widgets[self.idx-1].styles.color = '#908caa' 
        else:
            self.widgets[self.idx-1].styles.color = '#908caa' 
            self.widgets[self.idx+1].styles.color = '#908caa'
        self.widgets[self.idx].styles.color = '#f6c177'

    def mark_read(self):
        if self.nwidgets == 0:
            return
        entry = self.entries.entries.pop(self.idx)
        entry.mark_read()
        self.read_entries.append(entry)
        self.widgets.pop(self.idx).remove()
        self.highlight_current()
        
class SingleEntryScreen(Screen):
    
    def __init__(self, entries: list[Entry] = [], idx: int = 0):
        super().__init__()
        if entries == []: 
            self.entries = EntryCollection.from_cached().entries
        else:
            self.entries = entries
        self.widgets = [Static(str(entry)) for entry in self.entries]
        self.idx = idx

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        yield self.widgets[self.idx]


class Junefeed(App):
    
    BINDINGS = [
        ('c', 'push_screen("entry_collection")'),
        ('f', 'push_screen("feeds")'),
    ]
    
    def on_mount(self):
        self.install_screen(EntryCollectionScreen(), 'entry_collection')
        self.install_screen(FeedScreen(), 'feeds')
        self.push_screen('entry_collection')

    async def refresh_feeds(self):
        entry_collection = EntryCollectionScreen(from_cached=False)
        await self.push_screen(entry_collection)

    async def switch_to_entry(self):
        entry_collection = self.screen
        assert isinstance(entry_collection, EntryCollectionScreen), type(entry_collection)
        single_entry = SingleEntryScreen(entry_collection.entries.entries, entry_collection.idx)
        await self.push_screen(single_entry)
    
    def open_entry_link(self):
        entry = self.screen
        assert isinstance(entry, SingleEntryScreen)
        entry = entry.entries[entry.idx]
        self.open_url(entry.link)
            
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
        elif isinstance(self.screen, Feed):
            if event.key == 'q':
                self.exit()

