import os
import json
from typing import TypeVar, Type
import asyncio

from html.parser import HTMLParser
import feedparser

from junefeed.config import config


EntryType = TypeVar('EntryType', bound='Entry')
EntryCollectionType = TypeVar('EntryCollectionType', bound='EntryCollection')


class Entry:
    """A single entry in an RSS feed.

    Attributes:
        feed: the feed from which this entry originates.
        title: entry title
        summary: plain string containing the entry data
        link: URL for entry web page
        is_read: True if entry has been marked as read.
    """

    def __init__(
        self,
        feed: str,
        title: str,
        summary: str,
        link: str,
        date: str,
        is_read: bool = False,
    ) -> None:
        """Initialize Entry instance."""
        self.feed = feed
        self.title = title
        self.summary = self._parse_html(summary).strip()
        self.date = date
        self.link = link
        self.is_read = is_read

    @classmethod
    def from_json_obj(cls: Type[EntryType], entry: dict) -> EntryType:
        """Intialize Entry from a JSON object.

        Arguments:
            entry: a dictionary containing data from a parsed JSON entry.
        """
        feed = entry['feed']
        title = entry['title']
        summary = entry.get('summary', '')
        link = entry.get('link', '')
        date = entry.get('date', '')
        is_read = entry.get('is_read', False)
        return cls(feed, title, summary, link, date, is_read)

    def json_serialize(self) -> dict:
        """Return entry in JSON-compatible dictionary format."""
        json_obj = {
            'feed': self.feed,
            'title': self.title,
            'summary': self.summary,
            'link': self.link,
            'date': self.date,
            'is_read': self.is_read,
        }
        return json_obj

    def mark_read(self) -> None:
        """Mark entry instance as read."""
        self.is_read = True

    def mark_unread(self) -> None:
        """Mark entry instance as unread."""
        self.is_read = False

    def oneliner(self, pad: int = 0, highlighted: bool = False) -> str:
        """Return single-line string reflecting read/unread status."""
        if highlighted:
            # dotfeed = '\u2022 ' + self.feed
            dotfeed = '󰄛 ' + self.feed
            if not self.is_read:
                return f'[#f6c177]{dotfeed:>{pad}}:  {self.title}[/]'
            else:
                return f'[#ebbcba]{dotfeed:>{pad}}:  {self.title}[/]'
        else:
            if not self.is_read:
                return f'[#908caa]{self.feed:>{pad}}: [#e0def4] {self.title}[/]'
            else:
                return f'[#908caa]{self.feed:>{pad}}: [#6e6a86] {self.title}[/]'

    def _parse_html(self, data: str) -> str:
        """Converts input HTML data into Rich-formatted string."""
        if not ('<' in data and '</' in data):
            return data
        parser = RSSEntryParser()
        parser.feed(data)
        return parser.string

    def __repr__(self) -> str:
        """Return Rich-formatted entry string."""
        title = f'[#eb6f92 bold]{self.title:>10}[/]\n'
        link = f'[#c4a7e7 italic underline]{self.link}[/]\n'
        return f'{title}\n{link}\n{self.summary}'

    def __eq__(self, other):
        for attr, value in vars(self).items():
            if vars(other)[attr] != value:
                return False
        return True


class EntryCollection:
    """Class for manipulating a collection of Entry instances from an RSS feed.

    Attributes:
        entries: a list of Entry instances
        read_entries: a list of Entrys marked as read
    """

    def __init__(self, entries: list['Entry']) -> None:
        """Initialize EntryCollection."""
        self.entries = entries

    @classmethod
    def from_cached(cls: Type[EntryCollectionType]) -> EntryCollectionType:
        """Initialize EntryCollection from locally cached RSS feed data."""
        if os.path.exists(config.history_file):
            with open(config.history_file, 'r') as file:
                return cls([Entry.from_json_obj(entry) for entry in json.load(file)])
        else:
            raise FileNotFoundError(f'History file not found: {config.history_file}')

    @classmethod
    async def from_feeds(cls: Type[EntryCollectionType]) -> EntryCollectionType:
        """Initialize EntryCollection directly from RSS feeds."""
        cached_collection = EntryCollection.from_cached()
        await cached_collection.refresh()
        return cls(cached_collection.entries)

    async def refresh(self) -> None:
        """Fetch new entries from source feeds."""
        cached_entry_titles = [entry.title for entry in self.entries]
        for name, url in config.feeds.items():
            # Reverse list so most recent items in feed are displayed first.
            feed = Feed(url, name)
            feed_entries = await feed.get_entries()
            for entry in feed_entries[::-1]:
                if entry.title in cached_entry_titles:
                    continue
                self.entries.insert(0, entry)

    def cache_entries(self) -> None:
        """Write entry data to history file."""
        with open(config.history_file, 'w') as file:
            json.dump(
                [entry.json_serialize() for entry in self.entries], file, indent=2
            )

    def append(self, entry: Entry) -> None:
        self.entries.append(entry)

    def pop(self, index: int = -1) -> Entry:
        nents = len(self.entries)
        if index >= len(self.entries):
            raise IndexError(
                f'Index {index} out of range for unread_list of len {nents}'
            )
        return self.entries.pop(index)

    def __iter__(self):
        return EntryCollectionIterator(self.entries)

    def __len__(self) -> int:
        return len(self.entries)

    def __getitem__(self, index: int) -> Entry:
        nents = len(self.entries)
        if index >= len(self.entries):
            raise IndexError(
                f'Index {index} out of range for unread_list of len {nents}'
            )
        return self.entries[index]


class EntryCollectionIterator:
    def __init__(self, entries: list['Entry'] = []):
        self.entries = entries
        self.nentries = len(entries)
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= self.nentries:
            raise StopIteration
        entry = self.entries[self.index]
        self.index += 1
        return entry


class Feed:
    """RSS Feed class

    Attributes:
        url: the url from which feed data will be collected.
        name: the name of the feed
        entries: the list of entries from the feed
    """

    def __init__(self, url: str, name: str) -> None:
        """Intialize Feed"""
        self.url = url
        self.name = name
        self._entries: list['Entry'] = []

    async def get_entries(self) -> list['Entry']:
        """Returns list of entries populated with data from feed."""
        if len(self._entries) == 0:
            rawfeed = await asyncio.to_thread(feedparser.parse, self.url)
            if rawfeed.bozo:
                raise ValueError(f'Could not access feed "{self.url}"')
            for entry in rawfeed.entries:
                entry['feed'] = self.name
                self._entries.append(Entry.from_json_obj(entry))
        return self._entries

    def __str__(self):
        """Return Rich-formatted string of feed."""
        return f'[#31748f italic]{self.name:>10}[/]: {self.url}'

    async def __iter__(self):
        """Return iterator over entries."""
        return iter(await self.get_entries())


class RSSEntryParser(HTMLParser):
    """Simple HTML parser for converting HTML into Rich-formatted text.

    Attributes:
        string: the rich-formatted string
    """

    def __init__(self):
        """Intialize base HTMLParser and string attribute."""
        super().__init__()
        self.string = ''

    def handle_data(self, data):
        """Overides base HTMLParser method."""
        self.string += f'{data}\n\n'
