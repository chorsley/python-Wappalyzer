from unittest import TestCase

from httpretty import HTTPretty, httprettified

from Wappalyzer import WebPage, Wappalyzer


class WebPageTestCase(TestCase):
    @httprettified
    def test_new_from_url(self):
        HTTPretty.register_uri(HTTPretty.GET, 'http://example.com/', body='snerble')

        webpage = WebPage.new_from_url('http://example.com/')

        self.assertEquals(webpage.html, 'snerble')


class WappalyzerTestCase(TestCase):
    def test_analyze(self):
        analyzer = Wappalyzer()
        webpage = WebPage('http://example.com', '<html></html>', {})

        detected_apps = analyzer.analyze(webpage)

        self.assertEquals(detected_apps, set())

    def test_get_implied_apps(self):
        analyzer = Wappalyzer()
        analyzer.apps = {
            'a': { 
                'implies': 'b',
            },
            'b': { 
                'implies': 'c',
            },
            'c': { 
                'implies': 'a',
            },
        }

        implied_apps = analyzer._get_implied_apps('a')

        self.assertEquals(implied_apps, set(['a', 'b', 'c']))
