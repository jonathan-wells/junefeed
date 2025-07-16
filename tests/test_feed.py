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
    def test_from_json_obj(self, entry, json_entry):
        assert entry == Entry.from_json_obj(json_entry)
        for key in ['summary', 'link', 'is_read']:
            json_entry.pop(key)
        entry = Entry.from_json_obj(json_entry)
        assert entry.summary == ''
        assert entry.link == ''
        assert entry.is_read is False

    def test_json_serialize(self, entry, json_entry):
        assert entry.json_serialize() == json_entry


class TestEntryCollection:
    def test_ec(self):
        assert True


class TestFeed:
    def test_ec(self):
        assert True
