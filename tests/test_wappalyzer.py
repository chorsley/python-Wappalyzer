import pytest
import asyncio
import requests
import json
import os

from contextlib import redirect_stdout
from io import StringIO

from httpretty import HTTPretty, httprettified
from aioresponses import aioresponses

from Wappalyzer import WebPage, Wappalyzer
from Wappalyzer.__main__ import get_parser, main

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
    assert 'Apache' in analyzer.technologies

def test_latest_update():
    
    # Get the lastest file
    lastest_technologies_file=requests.get('https://raw.githubusercontent.com/AliasIO/wappalyzer/master/src/technologies.json')

    # Write the content to a tmp file
    with open('/tmp/lastest_technologies_file.json', 'w') as t_file:
        t_file.write(lastest_technologies_file.text)

    # Create Wappalyzer with this file in argument
    wappalyzer1=Wappalyzer.latest(technologies_file='/tmp/lastest_technologies_file.json')

    wappalyzer2=Wappalyzer.latest(update=True)

    assert wappalyzer1.technologies==wappalyzer2.technologies
    assert wappalyzer1.categories==wappalyzer2.categories

def test_analyze_no_technologies():
    analyzer = Wappalyzer(categories={}, technologies={})
    webpage = WebPage('http://example.com', '<html></html>', {})

    detected_technologies = analyzer.analyze(webpage)

    assert detected_technologies == set()

def test_get_implied_technologies():
    analyzer = Wappalyzer(categories={}, technologies={
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

    implied_technologies = analyzer._get_implied_technologies('a')

    assert implied_technologies == set(['a', 'b', 'c'])

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

    technologies = {
        'a': {
            'html': 'aaa',
            'cats': [1],
        },
        'b': {
            'html': 'bbb',
            'cats': [1, 2],
        }
    }

    analyzer = Wappalyzer(categories=categories, technologies=technologies)
    result = analyzer.analyze_with_categories(webpage)

    assert result == {"a": {"categories": ["cat1"]}}

def test_get_analyze_with_versions():

    webpage = WebPage('http://wordpress-example.com', '<html><head><meta name="generator" content="WordPress 5.4.2"></head></html>', {})
    
    categories = {
        "1": {
            "name": "CMS",
            "priority": 1
        },
        "11": {
            "name": "Blog",
            "priority": 1
        }
    }

    technologies = {
        "WordPress": {
            "cats": [
                1,
                11
            ],
            "html": [],
            "icon": "WordPress.svg",
            "implies": [
                "PHP",
                "MySQL"
            ],
            "meta": {
                "generator": "^WordPress ?([\\d.]+)?\\;version:\\1"
            },
            "website": "https://wordpress.org"
            },
        'b': {
            'html': 'bbb',
            'cats': [1, 2],
        },
        "PHP": {
            "website": "http://php.net"
        },
        "MySQL": {
            "website": "http://mysql.com"
        },
    }

    analyzer = Wappalyzer(categories=categories, technologies=technologies)
    result = analyzer.analyze_with_versions(webpage)

    assert ("WordPress", {"versions": ["5.4.2"]}) in result.items()

def test_analyze_with_versions_and_categories():
    
    webpage = WebPage('http://wordpress-example.com', '<html><head><meta name="generator" content="WordPress 5.4.2"></head></html>', {})
    
    categories = {
        "1": {
            "name": "CMS",
            "priority": 1
        },
        "11": {
            "name": "Blog",
            "priority": 1
        }
    }

    technologies = {
        "WordPress": {
            "cats": [
                1,
                11
            ],
            "html": [],
            "icon": "WordPress.svg",
            "implies": [
                "PHP",
                "MySQL"
            ],
            "meta": {
                "generator": "^WordPress ?([\\d.]+)?\\;version:\\1"
            },
            "website": "https://wordpress.org"
            },
        'b': {
            'html': 'bbb',
            'cats': [1, 2],
        },
        "PHP": {
            "website": "http://php.net"
        },
        "MySQL": {
            "website": "http://mysql.com"
        },
    }

    analyzer = Wappalyzer(categories=categories, technologies=technologies)
    result = analyzer.analyze_with_versions_and_categories(webpage)

    assert ("WordPress", {"categories": ["CMS", "Blog"], "versions": ["5.4.2"]}) in result.items()

def test_analyze_with_versions_and_categories_pattern_lists():
    
    webpage = WebPage('http://wordpress-example.com', '<html><head><meta name="generator" content="WordPress 5.4.2"></head></html>', {})
    
    categories = {
        "1": {
            "name": "CMS",
            "priority": 1
        },
        "11": {
            "name": "Blog",
            "priority": 1
        }
    }

    technologies = {
        "WordPress": {
            "cats": [
                1,
                11
            ],
            "html": [],
            "icon": "WordPress.svg",
            "implies": [
                "PHP",
                "MySQL"
            ],
            "meta": {
                "generator": ["Whatever123", "Whatever456", "^WordPress ?([\\d.]+)?\\;version:\\1", "Whatever"]
            },
            "website": "https://wordpress.org"
            },
        'b': {
            'html': 'bbb',
            'cats': [1, 2],
        },
        "PHP": {
            "website": "http://php.net"
        },
        "MySQL": {
            "website": "http://mysql.com"
        },
    }

    analyzer = Wappalyzer(categories=categories, technologies=technologies)
    result = analyzer.analyze_with_versions_and_categories(webpage)

    assert ("WordPress", {"categories": ["CMS", "Blog"], "versions": ["5.4.2"]}) in result.items()


def cli(*args):
    """Wrap python-Wappalyzer CLI exec"""

    with StringIO() as stream:
        with redirect_stdout(stream):
            main(get_parser().parse_args(args))
        result = json.loads(stream.getvalue())
    return result

@pytest.mark.skipif(os.getenv('GITHUB_ACTIONS'))
def test_cli():
    r = cli('http://exemple.com', '--update', '--user-agent', 'Mozilla/5.0', '--timeout', '30')
    assert len(r) > 2
    assert "Bootstrap" in r


