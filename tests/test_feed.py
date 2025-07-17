import pytest
from junefeed.feed import Entry


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


@pytest.fixture
def json_entry():
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
    def test_ec(self):
        assert True


class TestFeed:
    def test_ec(self):
        assert True
