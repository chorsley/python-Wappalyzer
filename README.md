python-Wappalyzer
=================

[![Build Status](https://travis-ci.org/chorsley/python-Wappalyzer.svg?branch=master)](https://travis-ci.org/chorsley/python-Wappalyzer)
[![PyPI version](https://badge.fury.io/py/python-Wappalyzer.svg)](https://badge.fury.io/py/python-Wappalyzer)
[![Coverage Status](https://coveralls.io/repos/github/chorsley/python-Wappalyzer/badge.svg?branch=master)](https://coveralls.io/github/chorsley/python-Wappalyzer?branch=master)

Python implementation of the [Wappalyzer](https://github.com/AliasIO/wappalyzer) web application detection utility.  


### Install

```
$ python3 -m pip install python-Wappalyzer
```

### Usage

```python
from Wappalyzer import Wappalyzer, WebPage
wappalyzer = Wappalyzer.latest()
webpage = WebPage.new_from_url('http://example.com')
wappalyzer.analyze(webpage)
```

> `
{'Docker', 'Azure CDN', 'Amazon Web Services', 'Amazon ECS'}
`

```python
wappalyzer.analyze_with_categories(webpage)
```

> `
{'Amazon ECS': {'categories': ['IaaS']},
 'Amazon Web Services': {'categories': ['PaaS']},
 'Azure CDN': {'categories': ['CDN']},
 'Docker': {'categories': ['Containers']}}
`

```python
webpage = WebPage.new_from_url('http://wordpress-example.com')
wappalyzer.analyze_with_versions_and_categories(webpage)
```


> `
{'Font Awesome': {'categories': ['Font scripts'], 'versions': ['5.4.2']},
 'Google Font API': {'categories': ['Font scripts'], 'versions': []},
 'MySQL': {'categories': ['Databases'], 'versions': []},
 'Nginx': {'categories': ['Web servers', 'Reverse proxies'], 'versions': []},
 'PHP': {'categories': ['Programming languages'], 'versions': ['5.6.40']},
 'WordPress': {'categories': ['CMS', 'Blogs'], 'versions': ['5.4.2']},
 'Yoast SEO': {'categories': ['SEO'], 'versions': ['14.6.1']}}
`

***

Last version to support Python2 was `0.2.2`.  