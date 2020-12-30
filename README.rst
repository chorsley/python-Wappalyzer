python-Wappalyzer
-----------------

.. image:: https://travis-ci.org/chorsley/python-Wappalyzer.svg?branch=master
  :target: https://travis-ci.org/chorsley/python-Wappalyzer

.. image:: https://badge.fury.io/py/python-Wappalyzer.svg
  :target: https://pypi.org/project/python-Wappalyzer/

.. image:: https://coveralls.io/repos/github/chorsley/python-Wappalyzer/badge.svg?branch=master
  :target: https://coveralls.io/github/chorsley/python-Wappalyzer?branch=master



Python implementation of the `Wappalyzer <https://github.com/AliasIO/wappalyzer>`_ web application detection utility.  


Install
-------

::

    $ pip install python-Wappalyzer

Require Python3.6 or later. 

Usage
-----

The API exposes two objects: ``Wappalyzer.Wappalyzer`` and ``Wappalyzer.WebPage``. 

>>> from Wappalyzer import Wappalyzer, WebPage

First create a WebPage. The following code creates a webpage with the ``request`` module. 

>>> webpage = WebPage.new_from_url('http://example.com')

Then analyze it with Wappalyzer. 

>>> wappalyzer = Wappalyzer.latest()
>>> wappalyzer.analyze(webpage)
{'Docker', 'Azure CDN', 'Amazon Web Services', 'Amazon ECS'}

To download and use the latest technologies file from AliasIO/wappalyzer repository, 
create the Wappalyzer driver with the ``update=True`` parameter. 

>>> wappalyzer = Wappalyzer.latest(update=True)

The Wappalyzer object exposes more methods that returns metatada for the detected technologies. 

>>> wappalyzer.analyze_with_categories(webpage)
{'Amazon ECS': {'categories': ['IaaS']},
 'Amazon Web Services': {'categories': ['PaaS']},
 'Azure CDN': {'categories': ['CDN']},
 'Docker': {'categories': ['Containers']}}

>>> webpage = WebPage.new_from_url('http://wordpress-example.com')
>>> wappalyzer.analyze_with_versions_and_categories(webpage)
{'Font Awesome': {'categories': ['Font scripts'], 'versions': ['5.4.2']},
 'Google Font API': {'categories': ['Font scripts'], 'versions': []},
 'MySQL': {'categories': ['Databases'], 'versions': []},
 'Nginx': {'categories': ['Web servers', 'Reverse proxies'], 'versions': []},
 'PHP': {'categories': ['Programming languages'], 'versions': ['5.6.40']},
 'WordPress': {'categories': ['CMS', 'Blogs'], 'versions': ['5.4.2']},
 'Yoast SEO': {'categories': ['SEO'], 'versions': ['14.6.1']}}

Read the `API Reference <https://chorsley.github.io/python-Wappalyzer/Wappalyzer.html>`_ for more documentation.

CLI
---

Additionnaly, there is now a CLI interface. It prints the analyzer results (with metatada) as JSON.

Call it with::

    python -m Wappalyzer

positional arguments:
  url                   URL to analyze

optional arguments:
  -h, --help            show this help message and exit
  --update              Use the latest technologies file downloaded from the internet
  --user-agent USERAGENT
                        Request user agent
  --timeout TIMEOUT     Request timeout
  --no-verify           Skip SSL cert verify


Note:
    Last version to support Python2 was `0.2.2`.  
