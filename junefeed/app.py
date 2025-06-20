from textual.app import App, ComposeResult
from textual.widgets import Static
from textual import events
from junefeed.feed import EntryCollection, Feed
from junefeed.config import config

class Junefeed(App):
    

    def __init__(self, from_cached=True):
        if from_cached:
            self.entries = EntryCollection.from_cached()
        else:
            self.entries = EntryCollection.from_feeds(config.feeds)
        self.feeds = [Feed(url, name) for (name, url) in config.feeds.items()]
        super().__init__()

    def on_mount(self):
        self.screen.styles.background = '#191724'
        # for idx, widget in enumerate(self.widgets[1:]):
            # widget.update(f'{str(self.feeds[idx]}')

    def compose(self) -> ComposeResult:
        # header = [Static(f'[#eb6f92 bold]{"Feeds":>10}[/]:')]
        header = [Static(f'[#eb6f92 bold]{"Entries"}[/]:')]
        # self.widgets = header + [Static(str(feed)) for feed in self.feeds]
        self.widgets = header + [Static(str(entry)) for entry in self.entries]
        yield from self.widgets

    def on_key(self, event: events.Key) -> None:
        if event.key == 'q':
            self.exit()

