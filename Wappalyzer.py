import json
import os
import re
import warnings

from BeautifulSoup import BeautifulSoup


DEFAULT_APPS_PATH = os.path.join(os.path.dirname(__file__), 'apps.json')


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

        self._parse_html()

    def _parse_html(self):
        """
        Parse the HTML with BeautifulSoup to find <script> and <meta> tags.
        """
        self.parsed_html = soup = BeautifulSoup(self.html)
        self.scripts = [ script['src'] for script in soup.findAll('script', src=True) ]
        self.meta = { meta['name'].lower(): meta['content'] for meta in soup.findAll('meta', attrs=dict(name=True)) }

    @classmethod
    def new_from_url(cls, url):
        """
        Constructs a new WebPage object for the URL,
        using the `requests` module to fetch the HTML.

        Parameters
        ----------

        url : str
        """
        # Placing the import here allows the Wappalyzer module
        # to be used without requiring any third-party dependencies.
        import requests
        response = requests.get(url)
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
    def __init__(self, apps_path=DEFAULT_APPS_PATH):
        """
        Initialize a new Wappalyzer instance.

        Parameters
        ----------

        apps_path : str, optional
            Path to a Wappalyzer apps.json file.

            By default, uses the version of the file
            bundled with the library.
        """
        self._load_apps(apps_path)

    def _load_apps(self, apps_path):
        """
        Load the Wappalyzer apps.json file.
        """
        try:
            with open(apps_path) as f:
                obj = json.load(f)
        except IOError as e:
            raise WappalyzerError("Failed to load Wappalyzer signatures file ({path}): {error}".format(
                    path=apps_path,
                    error=e.message,
                ))

        try:
            self.categories = obj['categories']
            self.apps = obj['apps']
        except KeyError as e:
            raise WappalyzerError("Invalid Wappalyzer signatures file: {error}".format(
                    error=e.message,
                ))

        for name, app in self.apps.items():
            self._prepare_app(app)

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
        Strip out key:value pairs from the pattern and compile the regular expression.
        """
        regex, _, rest = pattern.partition('\\;')
        try:
            return re.compile(regex, re.I)
        except re.error as e:
            warnings.warn("Caught '{error}' compiling regex: {regex}".format(error=e, regex=regex))
            return re.compile(r'(?!x)x') # regex that never matches: http://stackoverflow.com/a/1845097/413622

    def _has_app(self, app, webpage):
        """
        Determine whether the web page matches the app signature.
        """
        # Search the easiest things first and save the full-text search of the HTML for last

        for regex in app['url']:
            if regex.search(webpage.url):
                return True

        for name, regex in app['headers'].items():
            if name in webpage.headers:
                content = webpage.headers[name]
                if regex.search(content):
                    return True

        for regex in app['script']:
            for script in webpage.scripts:
                if regex.search(script):
                    return True

        for name, regex in app['meta'].items():
            if name in webpage.meta:
                content = webpage.meta[name]
                if regex.search(content):
                    return True

        for regex in app['html']:
            if regex.search(webpage.html):
                return True

    def _get_implied_apps(self, detected_apps):
        """
        Get the set of apps implied by `detected_apps`.
        """
        def __get_implied_apps(apps):
            _implied_apps = set()
            for app in apps:
                _implied_apps.update(self.apps[app]['implies'])
            return _implied_apps

        implied_apps = __get_implied_apps(detected_apps)
        all_implied_apps = set()

        # Descend recursively until we've found all implied apps
        while not all_implied_apps.issuperset(implied_apps):
            all_implied_apps.update(implied_apps)
            implied_apps = __get_implied_apps(all_implied_apps)

        return all_implied_apps


    def analyze(self, webpage):
        """
        Return a list of applications that can be detected on the web page.
        """
        detected_apps = set()

        for app_name, app in self.apps.items():
            if self._has_app(app, webpage):
                detected_apps.add(app_name)

        detected_apps |= self._get_implied_apps(detected_apps)

        return detected_apps
