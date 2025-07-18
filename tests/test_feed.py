import pytest
import tempfile
import os
import json

import yaml

from junefeed.feed import Entry, EntryCollection, Feed
from junefeed.config import Config


@pytest.fixture(autouse=True, scope='module')
def mock_config_file():
    """Fixture that provides a temporary config file and patches Config.config_file"""
    test_config = {
        'feeds': [
            {'name': 'nature', 'url': 'https://www.nature.com/nature.rss'},
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as file:
        yaml.dump(test_config, file)
        temp_config_path = file.name

    # Store original and patch
    original_config_file = Config.config_file
    Config.config_file = temp_config_path

    yield  # Execute the tests with the patched config file

    # Cleanup
    Config.config_file = original_config_file
    os.unlink(temp_config_path)


@pytest.fixture(autouse=True)
def mock_history_file(json_entry):
    """Fixture that provides a temporary history file and patches Config.history_file"""
    test_history = [json_entry]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as file:
        json.dump(test_history, file)
        temp_history_path = file.name

    # Store original and patch
    original_history_file = Config.history_file
    Config.history_file = temp_history_path

    yield Config.history_file  # Execute the tests with the patched config file

    # Cleanup
    Config.history_file = original_history_file
    os.unlink(temp_history_path)


@pytest.fixture
def entry():
    return Entry(
        feed='nature',
        title='test',
        summary='abstract goes here',
        link='www.nature.com',
        date='15/07/2025',
        is_read=True,
    )


@pytest.fixture()
def json_entry():
    return {
        'feed': 'nature',
        'title': 'test',
        'summary': 'abstract goes here',
        'link': 'www.nature.com',
        'date': '15/07/2025',
        'is_read': True,
    }


@pytest.fixture
def feed(entry):
    """Fixture that provides a dummy Feed instance."""
    test_feed = Feed(url='https://www.nature.com/nature.rss', name='nature')
    test_feed._entries = [entry]


@pytest.fixture
def entry_collection(entry):
    """Fixture that provides a dummy EntryCollection instance."""
    return EntryCollection(entries=[entry])


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

    def test_from_cached(self):
        """Test class method to generate from cached history."""
        entry_collection = EntryCollection.from_cached()
        assert isinstance(entry_collection, EntryCollection)
        assert len(entry_collection.entries) == 1
        assert entry_collection.entries[0].feed == 'nature'

    @pytest.mark.asyncio
    async def test_from_feed(self, monkeypatch, entry):
        """Test class method to generate from feeds"""

        @pytest.mark.asyncio
        async def mock_refresh(self: EntryCollection):
            # Instead of fetching data from real feed, just insert entry fixture.
            entry.title = 'changed_test_title'
            self.entries.insert(0, entry)

        # Replace EntryCollection.refresh method with mocked version
        monkeypatch.setattr(EntryCollection, 'refresh', mock_refresh)
        entry_collection = await EntryCollection.from_feeds()

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

        # Replace EntryCollection.refresh method with mocked version
        monkeypatch.setattr(Feed, 'get_entries', mock_get_entries)
        await entry_collection.refresh()
        assert isinstance(entry_collection, EntryCollection)
        assert len(entry_collection.entries) == 2  # 1 from history, 1 from feed.
        assert entry_collection.entries[0].title == 'another new title'

    def test_cache_entries(self, entry, entry_collection):
        """Test writing of entry data to history file."""
        entry_collection.cache_entries()
        with open(Config.history_file, 'r') as file:
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
