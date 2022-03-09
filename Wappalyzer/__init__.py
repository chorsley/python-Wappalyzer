"""
Welcome to ``python-Wappalyzer`` API documentation!

:see: `Wappalyzer`
"""

from .Wappalyzer import Wappalyzer, analyze
from .webpage import WebPage
__all__ = ["Wappalyzer", 
           "WebPage", 
           "analyze"]
