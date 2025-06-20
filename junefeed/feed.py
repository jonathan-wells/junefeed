import os
import json
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
            entries.extend(Feed(url, name).fetch_entries())
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

    def __init__(self, url, name):
        self.url = url
        self.name = name

    def fetch_entries(self):
        rawfeed = feedparser.parse(self.url)
        if rawfeed.bozo:
            raise ValueError(f'Feed "{self.url}" invalid')
        return [Entry.from_json_obj(entry) for entry in rawfeed.entries]
    
    # def __repr__(self):
    #     return f'[#31748f italic]{self.name:>10}[/]: {self.url}'
    
    def __str__(self):
        return f'[#31748f italic]{self.name:>10}[/]: {self.url}'
    
    def __iter__(self):
        return iter(self.fetch_entries())


class Entry:

    def __init__(self,
        title: str,
        summary, 
        link 
    ) -> None:
        self.title = title
        self.summary = summary
        self.link = link

    @classmethod
    def from_json_obj(cls, entry):
        title = entry['title']
        summary = entry.get('summary')
        link = entry.get('link')
        return cls(title, summary, link)

    def json_serialize(self):
        json_obj = {
            'title': self.title, 
            'summary': self.summary, 
            'link': self.link
        }
        return json_obj

    def __repr__(self):
        title = f'[#31748f bold]{self.title:>10}[/]\n'
        summary = f'{self.summary}\n'
        link = f'[#c4a7e7 italic underline]{self.link}[/]\n'
        footer = '-'*60 + '\n'
        return '\n'.join((title, summary, link, footer)) 

if __name__ == '__main__':
    entry = Entry('test', 'Lorem ipsum', 'https://www.google.com')
    print(entry.title)
    feeds = {
        'Nature': 'https://www.nature.com/nature.rss',
        'Science': 'https://www.sciencemag.org/rss/current.xml'
    }
    nature_feed = Feed(feeds['Nature'], 'Nature')
    print(nature_feed)
    for entry in nature_feed.fetch_entries()[:2]:
        print(entry.title)
    ec = EntryCollection.from_cached()
    print(list(ec)[0])
    ec2 = EntryCollection.from_feeds(feeds)
