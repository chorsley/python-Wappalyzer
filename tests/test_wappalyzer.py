import pytest
import asyncio

from httpretty import HTTPretty, httprettified
from aioresponses import aioresponses

from Wappalyzer import WebPage, Wappalyzer


@pytest.fixture
def async_mock():
    with aioresponses() as m:
        yield m

@httprettified
def test_new_from_url():
    HTTPretty.register_uri(HTTPretty.GET, 'http://example.com/',
                            body='snerble')

    webpage = WebPage.new_from_url('http://example.com/')

    assert webpage.html == 'snerble'

@pytest.mark.asyncio
async def test_new_from_url_async(async_mock):
    async_mock.get('http://example.com', status=200, body='snerble')

    webpage = await WebPage.new_from_url_async('http://example.com/')

    assert webpage.html == 'snerble'

def test_latest():
    analyzer = Wappalyzer.latest()

    print((analyzer.categories))
    assert analyzer.categories['1']['name'] == 'CMS'
    assert 'Apache' in analyzer.apps

def test_analyze_no_apps():
    analyzer = Wappalyzer(categories={}, apps={})
    webpage = WebPage('http://example.com', '<html></html>', {})

    detected_apps = analyzer.analyze(webpage)

    assert detected_apps == set()

def test_get_implied_apps():
    analyzer = Wappalyzer(categories={}, apps={
        'a': {
            'implies': 'b',
        },
        'b': {
            'implies': 'c',
        },
        'c': {
            'implies': 'a',
        },
    })

    implied_apps = analyzer._get_implied_apps('a')

    assert implied_apps == set(['a', 'b', 'c'])

def test_get_analyze_with_categories():
    webpage = WebPage('http://example.com', '<html>aaa</html>', {})
    categories = {
        "1": {
            "name": "cat1",
            "priority": 1
        },
        "2": {
            "name": "cat2",
            "priority": 1
        }
    }

    apps = {
        'a': {
            'html': 'aaa',
            'cats': [1],
        },
        'b': {
            'html': 'bbb',
            'cats': [1, 2],
        }
    }

    analyzer = Wappalyzer(categories=categories, apps=apps)
    result = analyzer.analyze_with_categories(webpage)

    assert result == {"a": {"categories": ["cat1"]}}
