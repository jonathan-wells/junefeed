import os
import json
from html.parser import HTMLParser
import feedparser
from junefeed.config import config


class EntryCollection:

    def __init__(self, entries: list['Entry']):
        self.entries = entries 

    @classmethod
    def from_cached(cls):
        if os.path.exists(config.history_file):
            with open(config.history_file, 'r') as file:
                return cls([Entry.from_json_obj(entry) for entry in json.load(file)])
        else:
            raise FileNotFoundError(f'History file not found: {config.history_file}')
    
    @classmethod
    def from_feeds(cls, feeds: dict):
        entries = []
        for (name, url) in feeds.items():
            entries.extend(Feed(url, name).entries)
        self = cls(entries)
        self.cache()
        return self
    
    def cache(self):
        with open(config.history_file, 'w') as file:
            json.dump(
                [entry.json_serialize() for entry in self.entries], 
                file,
                indent=2
            )
    
    def __iter__(self):
        return iter(self.entries)
            
class Feed:

    def __init__(self, url: str, name: str) -> None:
        self.url = url
        self.name = name
        self._entries = []
    
    @property
    def entries(self):
        if len(self._entries) == 0:
            rawfeed = feedparser.parse(self.url)
            if rawfeed.bozo:
                raise ValueError(f'Feed "{self.url}" invalid')
            for entry in rawfeed.entries:
                entry['feed'] = self.name
                self._entries.append(Entry.from_json_obj(entry))
        return self._entries
    
    def __str__(self):
        return f'[#31748f italic]{self.name:>10}[/]: {self.url}'
    
    def __iter__(self):
        return iter(self.entries)


class Entry:

    def __init__(self,
        feed: str,
        title: str,
        summary, 
        link 
    ) -> None:
        self.feed = feed
        self.title = title
        self.summary = summary
        self.link = link

    @classmethod
    def from_json_obj(cls, entry):
        feed = entry['feed']
        title = entry['title']
        summary = entry.get('summary')
        link = entry.get('link')
        return cls(feed, title, summary, link)

    def json_serialize(self):
        json_obj = {
            'feed': self.feed,
            'title': self.title, 
            'summary': self.summary, 
            'link': self.link
        }
        return json_obj

    def _parse_html(self, data):
        if not ('<' in data and '</' in data):
           return data 
        parser = RSSEntryParser()
        parser.feed(self.summary) 
        return parser.string

    def __repr__(self):
        title = f'[#eb6f92 bold]{self.title:>10}[/]\n'
        link = f'[#c4a7e7 italic underline]{self.link}[/]\n'
        summary = self._parse_html(self.summary).strip()
        return f'{title}\n{link}\n{summary}'


class RSSEntryParser(HTMLParser):
 
    def __init__(self):
        super().__init__()
        self.string = '' 

    def handle_data(self, data):
        self.string += f'{data}\n\n'


if __name__ == '__main__':
    entry = Entry('Nature',
                  'test', 
                  '<p>Nature Plants, Published online: 25 June 2025; <a href="https://www.nature.com/articles/s41477-025-02025-6">doi:10.1038/s41477-025-02025-6</a></p>Recent advances have brought virus-induced gene editing closer to achieving its promise to simplify and democratize plant gene editing by weaning it from its dependence on tissue-culture-based transformation.', 
                  'https://www.google.com')
    p = RSSEntryParser()
    p.feed(entry.summary)
