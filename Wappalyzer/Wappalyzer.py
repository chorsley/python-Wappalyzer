import json
import re
import warnings
import os
import logging
import pkgutil
import pkg_resources

import requests

from BeautifulSoup import BeautifulSoup

logger = logging.getLogger(name=__name__)


class WappalyzerError(Exception):
    """
    Raised for fatal Wappalyzer errors.
    """
    pass


class WebPage(object):
    """
    Simple representation of a web page, decoupled
    from any particular HTTP library's API.
    """

    def __init__(self, url, html, headers):
        """
        Initialize a new WebPage object.

        Parameters
        ----------

        url : str
            The web page URL.
        html : str
            The web page content (HTML)
        headers : dict
            The HTTP response headers
        """
        self.url = url
        self.html = html
        self.headers = headers
        
        try:
            self.headers.keys()
        except AttributeError:
            raise ValueError("Headers must be a dictionary-like object")

        self._parse_html()

    def _parse_html(self):
        """
        Parse the HTML with BeautifulSoup to find <script> and <meta> tags.
        """
        self.parsed_html = soup = BeautifulSoup(self.html)
        self.scripts = [script['src'] for script in
                        soup.findAll('script', src=True)]
        self.meta = {
            meta['name'].lower():
                meta['content'] for meta in soup.findAll(
                    'meta', attrs=dict(name=True, content=True))
        }


    @classmethod
    def new_from_url(cls, url, verify=True):
        """
        Constructs a new WebPage object for the URL,
        using the `requests` module to fetch the HTML.

        Parameters
        ----------

        url : str
        verify: bool
        """

        url = url.split('#', 1)[0]
        response = requests.get(url, verify=verify, timeout=2.5)
        return cls.new_from_response(response)

    @classmethod
    def new_from_response(cls, response):
        """
        Constructs a new WebPage object for the response,
        using the `BeautifulSoup` module to parse the HTML.

        Parameters
        ----------

        response : requests.Response object
        """
        return cls(response.url, html=response.text, headers=response.headers)


class Wappalyzer(object):
    """
    Python Wappalyzer driver.
    """
    def __init__(self, categories, apps):
        """
        Initialize a new Wappalyzer instance.

        Parameters
        ----------

        categories : dict
            Map of category ids to names, as in apps.json.
        apps : dict
            Map of app names to app dicts, as in apps.json.
        """
        self.categories = categories
        self.apps = apps

        for name, app in self.apps.items():
            self._prepare_app(app)

    @classmethod
    def latest(cls, apps_file=None):
        """
        Construct a Wappalyzer instance using a apps db path passed in via
        apps_file, or alternatively the default in data/apps.json
        """
        if apps_file:
            with open(apps_file, 'r') as fd:
                obj = json.load(fd)
        else:
            obj = json.loads(pkg_resources.resource_string(__name__, "data/apps.json"))

        return cls(categories=obj['categories'], apps=obj['apps'])

    def _prepare_app(self, app):
        """
        Normalize app data, preparing it for the detection phase.
        """
        # Ensure these keys' values are lists
        for key in ['url', 'html', 'script', 'implies']:
            try:
                value = app[key]
            except KeyError:
                app[key] = []
            else:
                if not isinstance(value, list):
                    app[key] = [value]

        # Ensure these keys exist
        for key in ['headers', 'meta']:
            try:
                value = app[key]
            except KeyError:
                app[key] = {}            

        # Ensure the 'meta' key is a dict
        obj = app['meta']
        if not isinstance(obj, dict):
            app['meta'] = { 'generator': obj }

        # Ensure keys are lowercase
        for key in ['headers', 'meta']:
            obj = app[key]
            app[key] = { k.lower(): v for k,v in obj.items() }

        # Prepare regular expression patterns
        for key in ['url', 'html', 'script']:
            app[key] = [self._prepare_pattern(pattern) for pattern in app[key]]

        for key in ['headers', 'meta']:
            obj = app[key]
            for name, pattern in obj.items():
                obj[name] = self._prepare_pattern(obj[name])

    def _prepare_pattern(self, pattern):
        """
        Strip out key:value pairs from the pattern and compile the regular
        expression.
        """
        attrs = {}
        pattern = pattern.split('\\;')
        for idx, expression in enumerate(pattern):
            if idx == 0:
                attrs['string'] = expression
                try:
                    attrs['regex'] = re.compile(expression, re.I)
                except re.error as e:
                    warnings.warn(
                        "Caught '{error}' compiling regex: {regex}"
                        .format(error=e, regex=regex)
                    )
                    # regex that never matches:
                    # http://stackoverflow.com/a/1845097/413622
                    attrs['regex'] = re.compile(r'(?!x)x')
            else:
                attr = expression.split(':')
                if len(attr) > 1:
                    key = attr.pop(0)
                    attrs[str(key)] = ':'.join(attr)
        return attrs

    def _has_app(self, app_name, app, webpage):
        """
        Determine whether the web page matches the app signature.
        """
        hasApp = False
        # Search the easiest things first and save the full-text search of the HTML for last
        for pattern in app['url']:
            if pattern['regex'].search(webpage.url):
                self._set_detected_app(app_name, app, 'url', pattern, webpage.url)
                #return True
                hasApp = True

        for name, pattern in app['headers'].items():
            if name in webpage.headers:
                content = webpage.headers[name]
                if pattern['regex'].search(content):
                    self._set_detected_app(app_name, app, 'headers', pattern, content, name)
                    #return True
                    hasApp = True
                    
        for pattern in app['script']:
            for script in webpage.scripts:
                if pattern['regex'].search(script):
                    self._set_detected_app(app_name, app, 'script', pattern, script)
                    #return True
                    hasApp = True

        for name, pattern in app['meta'].items():
            if name in webpage.meta:
                content = webpage.meta[name]
                if pattern['regex'].search(content):
                    self._set_detected_app(app_name, app, 'meta', pattern, content, name)
                    #return True
                    hasApp = True

        for pattern in app['html']:
            if pattern['regex'].search(webpage.html):
                self._set_detected_app(app_name, app, 'html', pattern, webpage.html)
                #return True
                hasApp = True
        
        # Set total confidence
        if hasApp:
            total = 0
            for id in app['confidence']:
                total += app['confidence'][id]
            app['confidenceTotal'] = total

        return hasApp
    
    def _set_detected_app(self, app_name, app, type, pattern, value, key = ''):
        """
        Store detected app
        """
        app['detected'] = True
        
        # Set confidence level
        if key != '':
            key += ' '
        if 'confidence' not in app:
            app['confidence'] = {}
        if 'confidence' not in pattern:
            pattern['confidence'] = 100
        else:
            # Convert to int for easy adding later
            pattern['confidence'] = int(pattern['confidence'])
        app['confidence'][type + ' ' + key + pattern['string']] = pattern['confidence']
        
        # Detect version number
        if 'version' in pattern:
            allmatches = re.findall(pattern['regex'], value)
            for i, matches in enumerate(allmatches):
                version = pattern['version']
                # Check for a string to avoid enumerating the string
                if isinstance(matches, basestring):
                    matches = [(matches)]
                for idx, match in enumerate(matches):
                    # Parse ternary operator
                    ternary = re.search(re.compile('\\\\' + str(idx+1) + '\\?([^:]+):(.*)$', re.I), version)
                    if ternary and len(ternary.groups()) == 2 and ternary.group(1) is not None and ternary.group(2) is not None:
                        version = version.replace(ternary.group(0), ternary.group(1) if match != '' else ternary.group(2))
                    
                    # Replace back references
                    version = version.replace('\\' + str(idx+1), match);
                if version != '':
                    if 'versions' not in app:
                        app['versions'] = [version]
                    elif version not in app['versions']:
                        app['versions'].append(version)
            #self._set_app_version(app)
        return app_name

    def _set_app_version(self, app):
        """
		Resolve version number (find the longest version number that contains
        all shorter detected version numbers)
		"""
        if 'versions' not in app:
            return
        
        app['versions'] = sorted(app['versions'], cmp=_sort_app_versions)
        
    def _get_implied_apps(self, detected_apps):
        """
        Get the set of apps implied by `detected_apps`.
        """
        def __get_implied_apps(apps):
            _implied_apps = set()
            for app in apps:
                try:
                    _implied_apps.update(set(self.apps[app]['implies']))
                except KeyError:
                    pass
            return _implied_apps

        implied_apps = __get_implied_apps(detected_apps)
        all_implied_apps = set()

        # Descend recursively until we've found all implied apps
        while not all_implied_apps.issuperset(implied_apps):
            all_implied_apps.update(implied_apps)
            implied_apps = __get_implied_apps(all_implied_apps)

        return all_implied_apps

    def get_categories(self, app_name):
        """
        Returns a list of the categories for an app name.
        """
        cat_nums = self.apps.get(app_name, {}).get("cats", [])
        cat_names = [self.categories.get("%s" % cat_num, "")
                     for cat_num in cat_nums]

        return cat_names
        
    def get_versions(self, app_name):
        """
        Returns a list of the disovered versions for an app name.
        """
        return [] if 'versions' not in self.apps[app_name] else self.apps[app_name]['versions']

    def get_confidence(self, app_name):
        """
        Returns the total confidence for an app name.
        """
        return [] if 'confidenceTotal' not in self.apps[app_name] else self.apps[app_name]['confidenceTotal']

    def analyze(self, webpage):
        """
        Return a list of applications that can be detected on the web page.
        """
        detected_apps = set()
        detected_apps_with_versions = set()

        # Check for app
        for app_name, app in self.apps.items():
            if self._has_app(app_name, app, webpage):
                detected_apps.add(app_name)

        # Add implied apps
        detected_apps |= self._get_implied_apps(detected_apps)

        return detected_apps

    def analyze_with_categories(self, webpage):
        detected_apps = self.analyze(webpage)
        categorised_apps = {}

        for app_name in detected_apps:
            cat_names = self.get_categories(app_name)
            categorised_apps[app_name] = {"categories": cat_names}

        return categorised_apps


        
def _sort_app_versions(a, b):
    return len(a) - len(b)
