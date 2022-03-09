"""
`Wappalyzer.WebPage` uses BeautifulSoup4 by default and fallback to standard library if it's not available.

The following objects are importable form this module: `WebPage`, `IWebPage`, `ITag`.

:Note: You can directly use/subclass one of the ``WebPage`` classes provided 
    in modules `_bs4` and `_stdlib` if you'de like more control. 
    Alternatively, your can write your own ``WebPage`` from scratch by suclassing the `IWebPage` interface.
"""
from ._common import IWebPage, ITag
try:
    from ._bs4 import WebPage
except Exception:
    try:
        from ._stdlib import WebPage # type: ignore
    except Exception as e:
        raise ImportError(
        """Cannot use Wappalyzer, missing required parser libraries.
        You can either install 'lxml' and 'beatifulsoup4' OR install 'dom_query'. 
        The later option makes Wappalyzer use the standard library HTML parser.""") from e