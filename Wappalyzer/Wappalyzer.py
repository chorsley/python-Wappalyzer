import aiohttp
import asyncio
import json
import logging
import pkg_resources
import re
import requests
import warnings

from bs4 import BeautifulSoup
from typing import Union

logger = logging.getLogger(name=__name__)


class WappalyzerError(Exception):
    """
    Raised for fatal Wappalyzer errors.
    """
    pass


class WebPage:
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
            list(self.headers.keys())
        except AttributeError:
            raise ValueError("Headers must be a dictionary-like object")

        self._parse_html()

    def _parse_html(self):
        """
        Parse the HTML with BeautifulSoup to find <script> and <meta> tags.
        """
        self.parsed_html = soup = BeautifulSoup(self.html, 'lxml')
        self.scripts = [script['src'] for script in
                        soup.findAll('script', src=True)]
        self.meta = {
            meta['name'].lower():
                meta['content'] for meta in soup.findAll(
                    'meta', attrs=dict(name=True, content=True))
        }

    @classmethod
    def new_from_url(cls, url: str, verify: bool = True, timeout: Union[int, float] = 10):
        """
        Constructs a new WebPage object for the URL,
        using the `requests` module to fetch the HTML.

        Parameters
        ----------

        url : str  
        verify: bool  
        timeout: int, float  
        """
        response = requests.get(url, verify=verify, timeout=timeout)
        return cls.new_from_response(response)

    @classmethod
    async def new_from_url_async(cls, url: str, verify: bool = True, timeout: Union[int, float] = 2.5,
                                 aiohttp_client_session: aiohttp.ClientSession = None):
        """
        Same as new_from_url only Async.

        Constructs a new WebPage object for the URL,
        using the `aiohttp` module to fetch the HTML.

        Parameters
        ----------

        url : str
        verify: bool
        """

        if not aiohttp_client_session:
            connector = aiohttp.TCPConnector(ssl=verify)
            aiohttp_client_session = aiohttp.ClientSession(connector=connector)

        async with aiohttp_client_session.get(url, timeout=timeout) as response:
            return await cls.new_from_response_async(response)

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

    @classmethod
    async def new_from_response_async(cls, response):
        """
        Constructs a new WebPage object for the response,
        using the `BeautifulSoup` module to parse the HTML.

        Parameters
        ----------

        response : aiohttp.ClientResponse¶ object
        """
        html = await response.text()
        return cls(str(response.url), html=html, headers=response.headers)


class Wappalyzer:
    """
    Python Wappalyzer driver.
    """

    def __init__(self, categories, technologies):
        """
        Initialize a new Wappalyzer instance.

        Parameters
        ----------

        categories : dict
            Map of category ids to names, as in technologies.json.
        technologies : dict
            Map of technology names to technology dicts, as in technologies.json.
        """
        self.categories = categories
        self.technologies = technologies
        self.confidence_regexp = re.compile(r"(.+)\\;confidence:(\d+)")

        # TODO
        for name, technology in list(self.technologies.items()):
            self._prepare_technology(technology)

    @classmethod
    def latest(cls, technologies_file=None):
        """
        Construct a Wappalyzer instance using a technologies db path passed in via
        technologies_file, or alternatively the default in data/technologies.json
        """
        if technologies_file:
            with open(technologies_file, 'r') as fd:
                obj = json.load(fd)
        else:
            obj = json.loads(pkg_resources.resource_string(__name__, "data/technologies.json"))

        return cls(categories=obj['categories'], technologies=obj['technologies'])

    def _prepare_technology(self, technology):
        """
        Normalize technology data, preparing it for the detection phase.
        """
        # Ensure these keys' values are lists
        for key in ['url', 'html', 'scripts', 'implies']:
            try:
                value = technology[key]
            except KeyError:
                technology[key] = []
            else:
                if not isinstance(value, list):
                    technology[key] = [value]

        # Ensure these keys exist
        for key in ['headers', 'meta']:
            try:
                value = technology[key]
            except KeyError:
                technology[key] = {}

        # Ensure the 'meta' key is a dict
        obj = technology['meta']
        if not isinstance(obj, dict):
            technology['meta'] = {'generator': obj}

        # Ensure keys are lowercase
        for key in ['headers', 'meta']:
            obj = technology[key]
            technology[key] = {k.lower(): v for k, v in list(obj.items())}

        # Prepare regular expression patterns
        for key in ['url', 'html', 'scripts']:
            technology[key] = [self._prepare_pattern(pattern) for pattern in technology[key]]

        for key in ['headers', 'meta']:
            obj = technology[key]
            for name, pattern in list(obj.items()):
                obj[name] = self._prepare_pattern(obj[name])

    def _prepare_pattern(self, pattern):
        """
        Strip out key:value pairs from the pattern and compile the regular
        expression.
        """
        attrs = {}
        pattern = pattern.split('\\;')
        for index, expression in enumerate(pattern):
            if index == 0:
                attrs['string'] = expression
                try:
                    attrs['regex'] = re.compile(expression, re.I)
                except re.error as err:
                    warnings.warn(
                        "Caught '{error}' compiling regex: {regex}".format(
                            error=err, regex=pattern)
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

    def _has_technology(self, technology, webpage):
        """
        Determine whether the web page matches the technology signature.
        """
        app = technology

        has_app = False
        # Search the easiest things first and save the full-text search of the
        # HTML for last

        for pattern in app['url']:
            if pattern['regex'].search(webpage.url):
                self._set_detected_app(app, 'url', pattern, webpage.url)

        for name, pattern in list(app['headers'].items()):
            if name in webpage.headers:
                content = webpage.headers[name]
                if pattern['regex'].search(content):
                    self._set_detected_app(app, 'headers', pattern, content, name)
                    has_app = True

        for pattern in technology['scripts']:
            for script in webpage.scripts:
                if pattern['regex'].search(script):
                    self._set_detected_app(app, 'scripts', pattern, script)
                    has_app = True

        for name, pattern in list(technology['meta'].items()):
            if name in webpage.meta:
                content = webpage.meta[name]
                if pattern['regex'].search(content):
                    self._set_detected_app(app, 'meta', pattern, content, name)
                    has_app = True

        for pattern in app['html']:
            if pattern['regex'].search(webpage.html):
                self._set_detected_app(app, 'html', pattern, webpage.html)
                has_app = True

        # Set total confidence
        if has_app:
            total = 0
            for index in app['confidence']:
                total += app['confidence'][index]
            app['confidenceTotal'] = total

        return has_app

    def _set_detected_app(self, app, app_type, pattern, value, key=''):
        """
        Store detected app.
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
        app['confidence'][app_type + ' ' + key + pattern['string']] = pattern['confidence']

        # Dectect version number
        if 'version' in pattern:
            allmatches = re.findall(pattern['regex'], value)
            for i, matches in enumerate(allmatches):
                version = pattern['version']

                # Check for a string to avoid enumerating the string
                if isinstance(matches, str):
                    matches = [(matches)]
                for index, match in enumerate(matches):
                    # Parse ternary operator
                    ternary = re.search(re.compile('\\\\' + str(index + 1) + '\\?([^:]+):(.*)$', re.I), version)
                    if ternary and len(ternary.groups()) == 2 and ternary.group(1) is not None and ternary.group(2) is not None:
                        version = version.replace(ternary.group(0), ternary.group(1) if match != ''
                                                  else ternary.group(2))

                    # Replace back references
                    version = version.replace('\\' + str(index + 1), match)
                if version != '':
                    if 'versions' not in app:
                        app['versions'] = [version]
                    elif version not in app['versions']:
                        app['versions'].append(version)
            self._set_app_version(app)

    def _set_app_version(self, app):
        """
        Resolve version number (find the longest version number that contains all shorter detected version numbers).
        """
        if 'versions' not in app:
            return

        app['versions'] = sorted(app['versions'], key=self._cmp_to_key(self._sort_app_versions))

    def _get_implied_technologies(self, detected_technologies):
        """
        Get the set of technologies implied by `detected_technologies`.
        """
        def __get_implied_technologies(technologies):
            _implied_technologies = set()
            for tech in technologies:
                try:
                    for implie in self.technologies[tech]['implies']:
                        # If we have no doubts just add technology
                        if 'confidence' not in implie:
                            _implied_technologies.add(implie)

                        # Case when we have "confidence" (some doubts)
                        else:
                            try:
                                # Use more strict regexp (cause we have already checked the entry of "confidence")
                                # Also, better way to compile regexp one time, instead of every time
                                app_name, confidence = self.confidence_regexp.search(implie).groups()
                                if int(confidence) >= 50:
                                    _implied_technologies.add(app_name)
                            except (ValueError, AttributeError):
                                pass
                except KeyError:
                    pass
            return _implied_technologies

        implied_technologies = __get_implied_technologies(detected_technologies)
        all_implied_technologies = set()

        # Descend recursively until we've found all implied technologies
        while not all_implied_technologies.issuperset(implied_technologies):
            all_implied_technologies.update(implied_technologies)
            implied_technologies = __get_implied_technologies(all_implied_technologies)

        return all_implied_technologies

    def get_categories(self, tech_name):
        """
        Returns a list of the categories for an technology name.
        """
        cat_nums = self.technologies.get(tech_name, {}).get("cats", [])
        cat_names = [self.categories.get(str(cat_num), "").get("name", "")
                     for cat_num in cat_nums]

        return cat_names

    def get_versions(self, app_name):
        """
        Retuns a list of the discovered versions for an app name.
        """
        return [] if 'versions' not in self.technologies[app_name] else self.technologies[app_name]['versions']

    def get_confidence(self, app_name):
        """
        Returns the total confidence for an app name.
        """
        return [] if 'confidenceTotal' not in self.technologies[app_name] else self.technologies[app_name]['confidenceTotal']

    def analyze(self, webpage):
        """
        Return a list of technologylications that can be detected on the web page.
        """
        detected_technologies = set()

        for tech_name, technology in list(self.technologies.items()):
            if self._has_technology(technology, webpage):
                detected_technologies.add(tech_name)

        detected_technologies |= self._get_implied_technologies(detected_technologies)

        return detected_technologies

    def analyze_with_versions(self, webpage):
        """
        Return a list of applications and versions that can be detected on the web page.
        """
        detected_apps = self.analyze(webpage)
        versioned_apps = {}

        for app_name in detected_apps:
            versions = self.get_versions(app_name)
            versioned_apps[app_name] = {"versions": versions}

        return versioned_apps

    def analyze_with_categories(self, webpage):
        """
        Return a list of technologies and categories that can be detected on the web page.
        """
        detected_technologies = self.analyze(webpage)
        categorised_technologies = {}

        for tech_name in detected_technologies:
            cat_names = self.get_categories(tech_name)
            categorised_technologies[tech_name] = {"categories": cat_names}

        return categorised_technologies

    def analyze_with_versions_and_categories(self, webpage):
        versioned_apps = self.analyze_with_versions(webpage)
        versioned_and_categorised_apps = versioned_apps

        for app_name in versioned_apps:
            cat_names = self.get_categories(app_name)
            versioned_and_categorised_apps[app_name]["categories"] = cat_names

        return versioned_and_categorised_apps

    def _sort_app_versions(self, version_a, version_b):
        return len(version_a) - len(version_b)

    def _cmp_to_key(self, mycmp):
        """
        Convert a cmp= function into a key= function
        """

        # https://docs.python.org/3/howto/sorting.html
        class CmpToKey:
            def __init__(self, obj, *args):
                self.obj = obj

            def __lt__(self, other):
                return mycmp(self.obj, other.obj) < 0

            def __gt__(self, other):
                return mycmp(self.obj, other.obj) > 0

            def __eq__(self, other):
                return mycmp(self.obj, other.obj) == 0

            def __le__(self, other):
                return mycmp(self.obj, other.obj) <= 0

            def __ge__(self, other):
                return mycmp(self.obj, other.obj) >= 0

            def __ne__(self, other):
                return mycmp(self.obj, other.obj) != 0

        return CmpToKey
