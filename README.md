python-Wappalyzer
=================

Python driver for [Wappalyzer][], a web application
detection utility.

    $ pip install python-Wappalyzer

    >>> from Wappalyzer import Wappalyzer, WebPage
    >>> wappalyzer = Wappalyzer.latest()
    >>> webpage = WebPage.new_from_url('http://example.com')
    >>> wappalyzer.analyze(webpage)
    set([u'EdgeCast'])

[Wappalyzer]: http://wappalyzer.com/
