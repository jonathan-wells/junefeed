from textual.app import App, ComposeResult
from textual.color import Color
from textual.widgets import Static
from junefeed.config import Config
from junefeed.feed import Feed


class Junefeed(App):

    def __init__(self):
        self.config = Config()
        self.feeds = self._load_feeds()
    
    def _load_feeds(self, cached=True):
        if cached:
            print(self.config.history)
            feeds = []
        else:
            feeds = [Feed(feed['url'], feed['name']) for feed in self.config.feeds]
        return feeds

    def on_mount(self):
        self.screen.styles.background = '#191724'
        # for idx, widget in enumerate(self.widgets[1:]):
        #     widget.update(f'{self.feeds[idx].to_static()}')
    
    def compose(self) -> ComposeResult:
        header = [Static(f'[#eb6f92 bold]{"Feeds":>10}[/]:')]
        self.widgets = header + [feed.to_static() for feed in self.feeds]
        yield from self.widgets

if __name__ == '__main__':
    june = Junefeed()

