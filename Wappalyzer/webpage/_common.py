"""
Containers for a Web page and it's components.
Wraps only the information strictly necessary to run the Wappalyzer engine.
"""

import abc
from typing import Iterable, List, Mapping, Any
try:
    from typing import Protocol
except ImportError:
    Protocol = object # type: ignore

import aiohttp
import requests
from requests.structures import CaseInsensitiveDict

def _raise_not_dict(obj:Any, name:str) -> None:
    try:
        list(obj.keys())
    except AttributeError: 
        raise ValueError(f"{name} must be a dictionary-like object")

class ITag(Protocol):
    """
    A HTML tag, decoupled from any particular HTTP library's API.
    """
    name: str
    attributes: Mapping[str, str]
    inner_html: str

class BaseTag(ITag, abc.ABC):
    """
    Subclasses must implement inner_html().
    """
    def __init__(self, name:str, attributes:Mapping[str, str]) -> None:
        _raise_not_dict(attributes, "attributes")
        self.name = name
        self.attributes = attributes
    @property
    def inner_html(self) -> str: # type: ignore
        """Returns the inner HTML of an element as a UTF-8 encoded bytestring"""
        raise NotImplementedError()

class IWebPage(Protocol):
    """
    Interfacte declaring the required methods/attributes of a WebPage object.

    Simple representation of a web page, decoupled from any particular HTTP library's API.
    """
    url: str
    html: str
    headers: Mapping[str, str]
    scripts: List[str]
    meta: Mapping[str, str]
    def select(self, selector:str) -> Iterable[ITag]: 
        raise NotImplementedError()

class BaseWebPage(IWebPage):
    """
    Implements factory methods for a WebPage.

    Subclasses must implement _parse_html() and select(string).
    """
    def __init__(self, url:str, html:str, headers:Mapping[str, str]):
        """
        Initialize a new WebPage object manually.  

        >>> from Wappalyzer import WebPage
        >>> w = WebPage('exemple.com',  html='<strong>Hello World</strong>', headers={'Server': 'Apache', })

        :param url: The web page URL.
        :param html: The web page content (HTML)
        :param headers: The HTTP response headers
        """
        _raise_not_dict(headers, "headers")
        self.url = url
        self.html = html
        self.headers = CaseInsensitiveDict(headers)
        self.scripts: List[str] = []
        self.meta: Mapping[str, str] = {}
        self._parse_html()

    def _parse_html(self):
        raise NotImplementedError()
    
    @classmethod
    def new_from_url(cls, url: str, **kwargs:Any) -> IWebPage:
        """
        Constructs a new WebPage object for the URL,
        using the `requests` module to fetch the HTML.

        >>> from Wappalyzer import WebPage
        >>> page = WebPage.new_from_url('exemple.com', timeout=5)

        :param url: URL 
        :param headers: (optional) Dictionary of HTTP Headers to send.
        :param cookies: (optional) Dict or CookieJar object to send.
        :param timeout: (optional) How many seconds to wait for the server to send data before giving up. 
        :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
        :param verify: (optional) Boolean, it controls whether we verify the SSL certificate validity. 
        :param \*\*kwargs: Any other arguments are passed to `requests.get` method as well. 
        """
        response = requests.get(url, **kwargs)
        return cls.new_from_response(response)

    @classmethod
    def new_from_response(cls, response:requests.Response) -> IWebPage:
        """
        Constructs a new WebPage object for the response,
        using the `BeautifulSoup` module to parse the HTML.

        :param response: `requests.Response` object
        """
        return cls(response.url, html=response.text, headers=response.headers)


    @classmethod
    async def new_from_url_async(cls, url: str, verify: bool = True,
                                 aiohttp_client_session: aiohttp.ClientSession = None, **kwargs:Any) -> IWebPage:
        """
        Same as new_from_url only Async.

        Constructs a new WebPage object for the URL,
        using the `aiohttp` module to fetch the HTML.

        >>> from Wappalyzer import WebPage
        >>> from aiohttp import ClientSession
        >>> async with ClientSession() as session:
        ...     page = await WebPage.new_from_url_async(aiohttp_client_session=session)
        
        :param url: URL
        :param aiohttp_client_session: `aiohttp.ClientSession` instance to use, optional.
        :param verify: (optional) Boolean, it controls whether we verify the SSL certificate validity. 
        :param headers: Dict. HTTP Headers to send with the request (optional).
        :param cookies: Dict. HTTP Cookies to send with the request (optional).
        :param timeout: Int. override the session's timeout (optional)
        :param proxy: Proxy URL, `str` or `yarl.URL` (optional).
        :param \*\*kwargs: Any other arguments are passed to `aiohttp.ClientSession.get` method as well. 

        """

        if not aiohttp_client_session:
            connector = aiohttp.TCPConnector(ssl=verify)
            aiohttp_client_session = aiohttp.ClientSession(connector=connector)

        async with aiohttp_client_session.get(url, **kwargs) as response:
            return await cls.new_from_response_async(response)

    @classmethod
    async def new_from_response_async(cls, response:aiohttp.ClientResponse) -> IWebPage:
        """
        Constructs a new WebPage object for the response,
        using the `BeautifulSoup` module to parse the HTML.

        >>> from aiohttp import ClientSession
        >>> wappalyzer = Wappalyzer.latest()
        >>> async with ClientSession() as session:
        ...     page = await session.get("http://example.com")
        ...
        >>> webpage = await WebPage.new_from_response_async(page)

        :param response: `aiohttp.ClientResponse` object
        """
        html = await response.text()
        return cls(str(response.url), html=html, headers=response.headers)