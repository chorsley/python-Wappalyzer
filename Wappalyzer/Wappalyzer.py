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
    def new_from_url(cls, url: str, verify: bool = True, timeout: Union[int, float] = 2.5):
        """
        Constructs a new WebPage object for the URL,
        using the `requests` module to fetch the HTML.

        Parameters
        ----------

        url : str
        verify: bool
        """
        response = requests.get(url, verify=verify, timeout=timeout)
        return cls.new_from_response(response)

    @classmethod
    async def new_from_url_async(cls, url: str, verify: bool =True, timeout: Union[int, float] = 2.5, aiohttp_client_session: aiohttp.ClientSession = None):
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

        #TODO
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
        for key in ['url', 'html', 'script', 'implies']:
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
        for key in ['url', 'html', 'script']:
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
        regex, _, rest = pattern.partition('\\;')
        try:
            return re.compile(regex, re.I)
        except re.error as e:
            warnings.warn(
                "Caught '{error}' compiling regex: {regex}"
                .format(error=e, regex=regex)
            )
            # regex that never matches:
            # http://stackoverflow.com/a/1845097/413622
            return re.compile(r'(?!x)x')

    def _has_technology(self, technology, webpage):
        """
        Determine whether the web page matches the technology signature.
        """
        # Search the easiest things first and save the full-text search of the
        # HTML for last

        for regex in technology['url']:
            if regex.search(webpage.url):
                return True

        for name, regex in list(technology['headers'].items()):
            if name in webpage.headers:
                content = webpage.headers[name]
                if regex.search(content):
                    return True

        for regex in technology['script']:
            for script in webpage.scripts:
                if regex.search(script):
                    return True

        for name, regex in list(technology['meta'].items()):
            if name in webpage.meta:
                content = webpage.meta[name]
                if regex.search(content):
                    return True

        for regex in technology['html']:
            if regex.search(webpage.html):
                return True

    def _get_implied_technologies(self, detected_technologies):
        """
        Get the set of technologies implied by `detected_technologies`.
        """
        def __get_implied_technologies(technologies):
            _implied_technologies = set()
            for tech in technologies:
                try:
                    _implied_technologies.update(set(self.technologies[tech]['implies']))
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
