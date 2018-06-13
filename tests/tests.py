from unittest import TestCase

from httpretty import HTTPretty, httprettified

from Wappalyzer import WebPage, Wappalyzer


class WebPageTestCase(TestCase):
    @httprettified
    def test_new_from_url(self):
        HTTPretty.register_uri(HTTPretty.GET, 'http://example.com/',
                               body='snerble')

        webpage = WebPage.new_from_url('http://example.com/')

        self.assertEquals(webpage.html, 'snerble')


class WappalyzerTestCase(TestCase):
    def test_latest(self):
        analyzer = Wappalyzer.latest()

        print(analyzer.categories)
        self.assertEquals(analyzer.categories['1'], 'CMS')
        self.assertIn('Apache', analyzer.apps)

    def test_analyze_no_apps(self):
        analyzer = Wappalyzer(categories={}, apps={})
        webpage = WebPage('http://example.com', '<html></html>', {})

        detected_apps = analyzer.analyze(webpage)

        self.assertEquals(detected_apps, set())

    def test_get_implied_apps(self):
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

        self.assertEquals(implied_apps, set(['a', 'b', 'c']))

    def test_get_analyze_with_categories(self):
        webpage = WebPage('http://example.com', '<html>aaa</html>', {})
        analyzer = Wappalyzer(categories={"1": "cat1", "2": "cat2"}, apps={
            'a': {
                'html': 'aaa',
                'cats': [1],
            },
            'b': {
                'html': 'bbb',
                'cats': [1, 2],
            },
        })

        result = analyzer.analyze_with_categories(webpage)

        self.assertEquals(result, {"a": {"categories": ["cat1"]}})
