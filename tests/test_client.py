import requests

import pytest

from client import client as cli


class DummyResponse:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status
        self.ok = status == 200

    def json(self):
        return self._data


def make_dummy(data):
    return DummyResponse(data)


def test_verse_url(monkeypatch):
    calls = {}

    def fake_get(url):
        calls['url'] = url
        return make_dummy({})

    monkeypatch.setattr(requests, 'get', fake_get)
    cli.main(['--server', 'http://localhost:4567', 'verse', 'John 3:16', '--translation', 'kjv'])
    assert calls['url'] == 'http://localhost:4567/John+3:16?translation=kjv'


def test_translations(monkeypatch):
    calls = {}

    def fake_get(url):
        calls['url'] = url
        return make_dummy([])

    monkeypatch.setattr(requests, 'get', fake_get)
    cli.main(['--server', 'http://localhost:4567', 'translations'])
    assert calls['url'] == 'http://localhost:4567/data'


def test_books_default_translation(monkeypatch):
    calls = {}

    def fake_get(url):
        calls['url'] = url
        return make_dummy([])

    monkeypatch.setattr(requests, 'get', fake_get)
    cli.main(['--server', 'http://localhost:4567', 'books'])
    assert calls['url'] == 'http://localhost:4567/data/web'


def test_chapters(monkeypatch):
    calls = {}

    def fake_get(url):
        calls['url'] = url
        return make_dummy([])

    monkeypatch.setattr(requests, 'get', fake_get)
    cli.main(['--server', 'http://localhost:4567', 'chapters', 'JHN', '--translation', 'web'])
    assert calls['url'] == 'http://localhost:4567/data/web/JHN'


def test_random_books(monkeypatch):
    calls = {}

    def fake_get(url):
        calls['url'] = url
        return make_dummy({})

    monkeypatch.setattr(requests, 'get', fake_get)
    cli.main(['--server', 'http://localhost:4567', 'random', '--books', 'JHN,MAT'])
    assert calls['url'] == 'http://localhost:4567/data/web/random/JHN,MAT'


def test_random_testament(monkeypatch):
    calls = {}

    def fake_get(url):
        calls['url'] = url
        return make_dummy({})

    monkeypatch.setattr(requests, 'get', fake_get)
    cli.main(['--server', 'http://localhost:4567', 'random', '--testament', 'NT'])
    assert calls['url'] == 'http://localhost:4567/data/web/random/NT'
