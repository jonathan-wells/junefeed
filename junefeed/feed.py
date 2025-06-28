import os
import json
from html.parser import HTMLParser
import feedparser
from junefeed.config import config


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
        is_read: bool
    ) -> None:
        """Initialize Entry instance."""
        self.feed = feed
        self.title = title
        self.summary = self._parse_html(summary).strip()
        self.link = link
        self.is_read = is_read

    @classmethod
    def from_json_obj(cls, entry: dict):
        """Returns an Entry instance from a corresponding JSON object.
        
        Arguments:
            entry: a dictionary containing data from a parsed JSON entry.
        """
        feed = entry['feed']
        title = entry['title']
        summary = entry.get('summary', '')
        link = entry.get('link', '')
        is_read = entry.get('is_read', False)
        return cls(feed, title, summary, link, is_read)

    def json_serialize(self) -> dict:
        """Return entry in JSON-compatible dictionary format."""
        json_obj = {
            'feed': self.feed,
            'title': self.title, 
            'summary': self.summary, 
            'link': self.link
        }
        return json_obj
    
    def mark_read(self) -> None:
        """Mark entry instance as read."""
        self.is_read = True

    def mark_unread(self) -> None:
        """Mark entry instance as unread."""
        self.is_read = False
    
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


class EntryCollection:
    """Class for manipulating a collection of Entry instances from an RSS feed.
    
    Attributes:
        entries: a list of Entry instances
    """

    def __init__(self, entries: list['Entry']) -> None:
        """Initialize EntryCollection."""
        self.entries = entries 

    @classmethod
    def from_cached(cls):
        """Initialize EntryCollection from locally cached RSS feed data."""
        if os.path.exists(config.history_file):
            with open(config.history_file, 'r') as file:
                return cls([Entry.from_json_obj(entry) for entry in json.load(file)])
        else:
            raise FileNotFoundError(f'History file not found: {config.history_file}')
    
    @classmethod
    def from_feeds(cls, feeds: dict):
        """Initialize EntryCollection directly from RSS feeds."""
        entries = []
        for (name, url) in feeds.items():
            entries.extend(Feed(url, name).entries)
            self = cls(entries)
            self.cache_entries()
            return self
    
    def cache_entries(self) -> None:
        """Write entry data to history file."""
        with open(config.history_file, 'w') as file:
            json.dump(
                [entry.json_serialize() for entry in self.entries], 
                file,
                indent=2
            )
    
    def __iter__(self):
        return iter(self.entries)
            

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
    
    @property
    def entries(self) -> list['Entry']:
        """Returns list of entries populated with data from feed."""
        if len(self._entries) == 0:
            rawfeed = feedparser.parse(self.url)
            if rawfeed.bozo:
                raise ValueError(f'Could not access feed "{self.url}"')
            for entry in rawfeed.entries:
                entry['feed'] = self.name
                self._entries.append(Entry.from_json_obj(entry))
        return self._entries
    
    def __str__(self):
        """Return Rich-formatted string of feed."""
        return f'[#31748f italic]{self.name:>10}[/]: {self.url}'
    
    def __iter__(self):
        """Return iterator over entries."""
        return iter(self.entries)


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
