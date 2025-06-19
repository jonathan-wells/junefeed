import os
import json
import feedparser
from textual.widgets import Static
from junefeed.config import config


class EntryCollection:

    def __init__(self, entries: list):
        self.entries = entries 
    
    def cache(self):
        with open(config.history_file, 'w') as file:
            json.dump(self.entries, file)

    @classmethod
    def from_cached(cls):
        if os.path.exists(config.history_file):
            with open(config.history_file, 'r') as file:
                return cls(json.load(file))
        else:
            raise FileNotFoundError(f'History file not found: {config.history_file}')


class Feed:

    def __init__(self, url, name):
        self.url = url
        self.name = name
        self.feed = feedparser.parse(url)
        if self.feed.bozo:
            raise ValueError(f'Feed "{url}" invalid')
        self.entries = self.feed['items']
    
    def __repr__(self):
        return f'[#31748f italic]{self.name:>10}[/]: {self.url}'
    
    def __iter__(self):
        return iter(self.entries)


class Entry:

    def __init__(
        self, 
        title: str,
        summary: str | None = None, 
        link: str | None = None
    ) -> None:
        self.title = title
        self.summary = summary
        self.link = link

    def __repr__(self):
        title = f'[#31748f bold]{self.title:>10}[/]'
        summary = f'{self.summary}'
        link = f'[#c4a7e7 italic underline]{self.link}'
        return '\n'.join((title, summary, link)) 

