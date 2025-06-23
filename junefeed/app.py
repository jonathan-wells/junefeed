from textual.app import App, ComposeResult
from textual.widgets import Static, Header
from textual.screen import Screen
from textual import events

from junefeed.feed import EntryCollection, Feed
from junefeed.config import config



class FeedScreen(Screen):
    
    def __init__(self):
        super().__init__()
        self.feeds = [Feed(url, name) for (name, url) in config.feeds.items()]

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        self.sub_title = 'feeds'
        self.widgets = []
        for feed in self.feeds:
            widget = Static(str(feed))
            widget.styles.text_wrap = 'nowrap'
            widget.styles.text_overflow = 'clip'
            self.widgets.append(widget)

        yield Header(icon=b'\xF0\x9F\x90\xB1'.decode('utf8'))
        yield from self.widgets
    

class EntryCollectionScreen(Screen):
    
    def __init__(self, from_cached=True):
        if from_cached:
            self.entries = EntryCollection.from_cached()
        else:
            self.entries = EntryCollection.from_feeds(config.feeds)
        super().__init__()

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        self.sub_title = 'entries'
        self.widgets = []
        self._idx = 0
        for i, entry in enumerate(self.entries, 1):
            widget = Static(f'[#31748f bold]{i:>4}.[/] {entry.title}')
            widget.styles.text_wrap = 'nowrap'
            widget.styles.text_overflow = 'clip'
            widget.styles.color = 'grey'
            self.widgets.append(widget)
        self.widgets[0].styles.color = 'white'
        yield Header(icon=b'\xF0\x9F\x90\xB1'.decode('utf8'))
        yield from self.widgets 
 
    def on_mount(self):
        self.screen.show_horizontal_scrollbar = True
        self.screen.styles.scrollbar_size_horizontal = 10
        self.screen.styles.scrollbar_size_vertical = 0 

    def on_key(self, event: events.Key) -> None:
        if event.key == 'h':
            self.scroll_left()
        elif event.key == 'j':
            self._idx += 1
            if self._idx >= 12:
                self.scroll_down()
            self.widgets[self._idx-1].styles.color = 'grey'
            self.widgets[self._idx].styles.color = 'white'
        elif event.key == 'k':
            self._idx -= 1
            self.widgets[self._idx].styles.color = 'white'
            self.widgets[self._idx+1].styles.color = 'grey'
            self.scroll_up()

        elif event.key == 'l':
            self.scroll_right()

class SingleEntryScreen(Screen):
    
    def __init__(self):
        self.feeds = [Feed(url, name) for (name, url) in config.feeds.items()]
        super().__init__()

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        self.widgets = [Static(str(feed)) for feed in self.feeds]
        yield from self.widgets
    

class Junefeed(App):
    
    BINDINGS = [
        ('f', 'switch_mode("feeds")', 'FeedScreen'),
        ('c', 'switch_mode("entry_collection")', 'EntryCollectionScreen'),
        ('e', 'switch_mode("single_entry")', 'SingleEntryScreen')
    ]
    MODES = {
        'feeds': FeedScreen,
        'entry_collection': EntryCollectionScreen,
        'single_entry': SingleEntryScreen 
    }

    def __init__(self, from_cached=True):
        if from_cached:
            self.entries = EntryCollection.from_cached()
        else:
            self.entries = EntryCollection.from_feeds(config.feeds)
        self.feeds = [Feed(url, name) for (name, url) in config.feeds.items()]
        super().__init__()

    def on_mount(self):
        self.title = 'Junefeed'
        self.switch_mode('entry_collection')

    def on_key(self, event: events.Key) -> None:
        if event.key == 'q':
            self.exit()

