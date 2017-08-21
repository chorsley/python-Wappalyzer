python-Wappalyzer
=================

[![Build Status](https://travis-ci.org/chorsley/python-Wappalyzer.svg?branch=master)](https://travis-ci.org/chorsley/python-Wappalyzer)
[![PyPI version](https://badge.fury.io/py/python-Wappalyzer.svg)](https://badge.fury.io/py/python-Wappalyzer)
[![Coverage Status](https://coveralls.io/repos/github/chorsley/python-Wappalyzer/badge.svg?branch=master)](https://coveralls.io/github/chorsley/python-Wappalyzer?branch=master)


Python driver for [Wappalyzer][], a web application
detection utility.

    $ pip install python-Wappalyzer

    >>> from Wappalyzer import Wappalyzer, WebPage
    >>> wappalyzer = Wappalyzer.latest()
    >>> webpage = WebPage.new_from_url('http://example.com')
    >>> wappalyzer.analyze(webpage)
    set([u'EdgeCast'])

[Wappalyzer]: http://wappalyzer.com/
