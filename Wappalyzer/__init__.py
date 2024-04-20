"""
Welcome to ``python-Wappalyzer`` API documentation!

:see: `Wappalyzer` and `WebPage`.
"""
from typing import TextIO
import logging
import sys

# Setup stdout logger
def _setup_logger(
    name: str,
    verbose: bool = False,
    quiet: bool = False,
    outstream: TextIO = sys.stdout
    ) -> logging.Logger:

    format_string = "%(levelname)s - %(message)s"

    if verbose:
        verb_level = logging.DEBUG
    elif quiet:
        verb_level = logging.ERROR
    else:
        verb_level = logging.INFO

    log = logging.getLogger(name)

    log.setLevel(verb_level)
    std = logging.StreamHandler(outstream)
    std.setLevel(verb_level)
    std.setFormatter(logging.Formatter(format_string))
    log.handlers = []
    log.addHandler(std)

    return log

_setup_logger('python-Wappalyzer')

from .Wappalyzer import Wappalyzer, analyze
from .webpage import WebPage
__all__ = ["Wappalyzer", 
           "WebPage", 
           "analyze"]
