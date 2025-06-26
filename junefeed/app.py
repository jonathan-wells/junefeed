from textual.app import App, ComposeResult
from textual.widgets import Static
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
        self.idx = 0

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        self.sub_title = 'entries'
        self.widgets = []
        for i, entry in enumerate(self.entries, 0):
            widget = Static(f'[#6e6a86]{i:>4}.[/]  [#31748f]{entry.feed:<12}[/] {entry.title}')
            widget.styles.text_wrap = 'nowrap'
            widget.styles.text_overflow = 'clip'
            widget.styles.color = '#908caa'
            self.widgets.append(widget)
        self.widgets[0].styles.color = '#f6c177'
        yield from self.widgets 
 
    def on_mount(self):
        self.screen.show_horizontal_scrollbar = True
        self.screen.styles.scrollbar_size_horizontal = 10
        self.screen.styles.scrollbar_size_vertical = 0
        self.nwidgets = len(self.widgets)
    
    def on_key(self, event: events.Key) -> None:
        if event.key == 'h':
            self.scroll_left()
        elif event.key == 'j':
            self.idx += 1
            if self.idx >= 11:
                self.scroll_down()
            self.highlight_current()
        elif event.key == 'k':
            self.idx -= 1
            if self.idx < self.nwidgets - 12:
                self.scroll_up()
            self.highlight_current()
        elif event.key == 'l':
            self.scroll_right()
 
    def open_entry(self):
        pass

    def highlight_current(self):
        if self.idx < 0:
            self.idx = 0
        elif self.idx >= self.nwidgets - 1:
            self.idx = self.nwidgets - 1
            self.widgets[self.idx-1].styles.color = '#908caa' 
        else:
            self.widgets[self.idx-1].styles.color = '#908caa' 
            self.widgets[self.idx+1].styles.color = '#908caa'
        self.widgets[self.idx].styles.color = '#f6c177'

        
class SingleEntryScreen(Screen):
    
    def __init__(self):
        super().__init__()
        self.entries = list(EntryCollection.from_cached())

    def compose(self) -> ComposeResult:
        self.screen.styles.background = '#191724'
        self.widgets = [Static(str(entry)) for entry in self.entries]
        self.idx = 0
        yield self.widgets[self.idx]

    def on_mount(self):
        pass 

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
    
    def refresh_feeds(self):
        # This won't work because it is not the same entries as displayed in the screen 
        self.entries = EntryCollection.from_feeds(config.feeds)

    def on_mount(self):
        self.title = 'Junefeed'
        self.switch_mode('entry_collection')
    
    def switch_to_entry(self):
        current_index = self.MODES['entry_collection'].idx
        print(current_index)



    def on_key(self, event: events.Key) -> None:
        if event.key == 'q':
            self.exit()
        elif event.key == 'r':
            self.refresh_feeds()
            self.mount()
        elif event.key == 'o':
            self.switch_to_entry()

