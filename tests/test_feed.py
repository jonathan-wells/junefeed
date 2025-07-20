import pytest
import tempfile
from pathlib import Path
import json
from typing import Iterator
from feedparser.util import FeedParserDict

from junefeed.feed import Entry, EntryCollection, Feed
from junefeed.config import Config, History


@pytest.fixture
def config():
    """Mocked Config instance fixture."""
    mock_config = Config()
    temp_config_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.yaml', delete=False
    )
    mock_config.config_file = Path(temp_config_file.name)
    mock_config._config = {
        'feeds': [
            {'name': 'nature', 'url': 'https://www.nature.com/nature.rss'},
        ]
    }
    mock_config.feeds = {'nature': 'https://www.nature.com/nature.rss'}
    return mock_config


@pytest.fixture
def history():
    """Mocked History instance fixture."""
    mock_history = History()
    mock_history._history = [
        {
            'feed': 'nature',
            'title': 'test',
            'summary': 'abstract goes here',
            'link': 'www.nature.com',
            'date': '15/07/2025',
            'is_read': True,
        }
    ]
    temp_history_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False
    )
    mock_history.history_file = Path(temp_history_file.name)
    with open(mock_history.history_file, 'w') as file:
        json.dump(mock_history._history, file)
    return mock_history


@pytest.fixture
def entry():
    """Mocked Entry instance fixture."""
    return Entry(
        feed='nature',
        title='test',
        summary='abstract goes here',
        link='www.nature.com',
        date='15/07/2025',
        is_read=True,
    )


@pytest.fixture
def entry_collection(entry, config, history):
    """Mocked EntryCollection instance fixture."""
    mock_entry_collection = EntryCollection(entries=[entry])
    mock_entry_collection.config = config
    mock_entry_collection.history = history
    return mock_entry_collection


@pytest.fixture
def feed(entry):
    """Mocked Feed instance fixture."""
    mock_feed = Feed(url='https://www.nature.com/nature.rss', name='nature')
    mock_feed._entries = [entry]
    return mock_feed


@pytest.fixture()
def json_entry():
    """JSON entry data fixture."""
    return {
        'feed': 'nature',
        'title': 'test',
        'summary': 'abstract goes here',
        'link': 'www.nature.com',
        'date': '15/07/2025',
        'is_read': True,
    }


class TestEntry:
    """Tests for all Entry methods."""

    def test_from_json_obj(self, entry, json_entry):
        """Test that Entry instance is correctly generated from json object."""
        assert entry == Entry.from_json_obj(json_entry)
        for key in ['summary', 'link', 'is_read']:
            json_entry.pop(key)
        entry = Entry.from_json_obj(json_entry)
        assert entry.summary == ''
        assert entry.link == ''
        assert entry.is_read is False

    def test_json_serialize(self, entry, json_entry):
        """Test that entry is correctly converted to json for caching."""
        assert entry.json_serialize() == json_entry

    def test_mark_read(self, entry):
        """Test correct 'read' marking"""
        entry.is_read = False
        entry.mark_read()
        assert entry.is_read is True

    def test_mark_unread(self, entry):
        """Test correct 'unread' marking"""
        entry.is_read = True
        entry.mark_unread()
        assert entry.is_read is False

    def test_oneliner(self, entry):
        """Test that all possible current-line states produce unique output."""
        oneliners = []
        for read_status in [True, False]:
            entry.is_read = read_status
            for highlighted in [True, False]:
                oneliners.append(entry.oneliner(highlighted=highlighted))
        assert len(set(oneliners)) == 4
        for ol in oneliners:
            assert entry.title in ol
            assert entry.feed in ol

    def test_parse_html(self):
        """Test parsing of HTML-structured text. Probably should remove newlines."""
        assert Entry.parse_entry_html('test') == 'test\n\n'
        assert Entry.parse_entry_html('<html>test</html>') == 'test\n\n'

    def test_repr(self, entry):
        """Test that string repr of entry contains relevant attributes."""
        for entity in [entry.title, entry.link, entry.summary]:
            assert entity in str(entry)

    def test_eq(self, entry):
        """Test equality checking of entries."""
        other_entry = Entry(
            feed='nature',
            title='test',
            summary='abstract goes here',
            link='www.nature.com',
            date='15/07/2025',
            is_read=True,
        )
        assert entry == other_entry
        other_entry.title = 'science'
        assert entry != other_entry


class TestEntryCollection:
    """Tests for all EntryCollection methods."""

    def test_from_cached(self, history):
        """Test class method to generate from cached history."""
        entry_collection = EntryCollection.from_cached(history)
        assert isinstance(entry_collection, EntryCollection)
        assert len(entry_collection.entries) == 1
        assert entry_collection.entries[0].feed == 'nature'

    @pytest.mark.asyncio
    async def test_from_feed(self, monkeypatch, entry, history):
        """Test EntryCollection classmethod to generate from refreshed feeds."""

        @pytest.mark.asyncio
        async def mock_refresh(self: EntryCollection):
            # Instead of fetching data from real feed, just insert entry fixture.
            entry.title = 'changed_test_title'
            self.entries.insert(0, entry)

        # Replace EntryCollection.refresh method with mocked version
        monkeypatch.setattr(EntryCollection, 'refresh', mock_refresh)
        entry_collection = await EntryCollection.from_feeds(history)

        assert isinstance(entry_collection, EntryCollection)
        assert len(entry_collection.entries) == 2  # 1 from history, 1 from feed.
        assert entry_collection.entries[0].title == 'changed_test_title'

    @pytest.mark.asyncio
    async def test_refresh(self, monkeypatch, entry, entry_collection):
        """Test refresh entry collection."""

        @pytest.mark.asyncio
        async def mock_get_entries(self: Feed):
            # Mocks Feed.get_entries by returning list containing entry fixture.
            entry.title = 'another new title'
            self._entries = [entry]
            return self._entries

        # Replaces EntryCollection.refresh method with mocked version
        monkeypatch.setattr(Feed, 'get_entries', mock_get_entries)
        await entry_collection.refresh()
        assert isinstance(entry_collection, EntryCollection)
        assert len(entry_collection.entries) == 2  # 1 from history, 1 from feed.
        assert entry_collection.entries[0].title == 'another new title'

    def test_cache_entries(self, entry, entry_collection):
        """Test writing of entry data to history file."""
        entry_collection.cache_entries()
        with open(entry_collection.history.history_file, 'r') as file:
            data = json.load(file)
            assert data[0]['title'] == entry.title

    def test_append(self, entry_collection, entry):
        """Test that append adds to entries list."""
        start_len = len(entry_collection.entries)
        entry_collection.append(entry)
        assert len(entry_collection.entries) == start_len + 1

    def test_pop(self, entry_collection):
        """Test that pop removes an item from entries list."""
        start_len = len(entry_collection.entries)
        popped = entry_collection.pop()
        assert isinstance(popped, Entry)
        assert len(entry_collection.entries) == start_len - 1

    def test_iter(self, entry_collection):
        eciterator = iter(entry_collection)
        assert isinstance(eciterator, Iterator)
        assert isinstance(next(eciterator), Entry)
        # Should fail because entry_collection has only one entry.
        with pytest.raises(StopIteration):
            next(eciterator)

    def test_len(self, entry_collection, entry):
        """Test that __len__ returns number of entries in collection."""
        assert len(entry_collection) == 1
        entry_collection.entries.append(entry)
        assert len(entry_collection) == 2

    def test_get_item(self, entry_collection):
        """Test that __getitem__ returns correct entry."""
        assert entry_collection[0].title == 'test'
        with pytest.raises(IndexError):
            # Should fail because entry_collection has only one entry.
            entry_collection[1]


class TestFeed:
    """Tests for all Feed methods."""

    @pytest.mark.asyncio
    async def test_get_entries(self, monkeypatch, feed, json_entry, entry):
        """Test that entries are correctly parsed from output of feedparser."""

        def mock_parse(*_):
            """Mocks valid return from feedparser.parse"""
            return FeedParserDict(bozo=False, entries=[json_entry])

        def mock_bozo_parse(*_):
            """Mocks failed return from feedparser.parse"""
            return FeedParserDict(bozo=True)

        monkeypatch.setattr(Feed, '_parse', mock_parse)
        feed = Feed('test_url', 'test_name')
        entries = await feed.get_entries()
        assert entries[0].title == entry.title
        feed = Feed('test_url', 'test_name')
        monkeypatch.setattr(Feed, '_parse', mock_bozo_parse)
        with pytest.raises(ValueError):
            entries = await feed.get_entries()

    def test_str(self, feed):
        """Test that __str__ returns a string containg name and url."""
        feedstring = str(feed)
        assert feed.url in feedstring
        assert feed.name in feedstring
