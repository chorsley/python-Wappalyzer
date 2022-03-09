from setuptools import setup, find_packages
import pathlib
import sys

# Hack to implement a default extra require [lxml] for lxml and bs4 packages that can be replaced with [minidom]
# https://github.com/pypa/setuptools/issues/1139
is_installing = any('install'==a for a in sys.argv)
is_minidom_extra_enabled = any('minidom' in a for a in sys.argv)

setup(
    name                =   "python-Wappalyzer",
    version             =   "0.4.0",
    description         =   "Python implementation of the Wappalyzer web application "
                            "detection utility",
    long_description    =   (pathlib.Path(__file__).parent / "README.rst").read_text(),
    long_description_content_type   =   "text/markdown",
    author              =   "Chris Horsley (chorsley) and other contributors (See git history)",
    url                 =   "https://github.com/chorsley/python-Wappalyzer",
    classifiers         =   [
                                'Development Status :: 3 - Alpha',
                                'Intended Audience :: Developers',
                                'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
                                'Programming Language :: Python :: 3',
                                'Topic :: Internet :: WWW/HTTP',
                            ],
    packages            =   find_packages(exclude='tests'),
    package_data        =   {'Wappalyzer': ['data/technologies.json']},
    install_requires    =   [   'requests',
                                'aiohttp',
                                'aioresponses',
                                'cached_property',
                            ] + [] if not (is_installing or is_minidom_extra_enabled) else ['beautifulsoup4', 'lxml'],
    extras_require      =   {
                             'lxml': ['beautifulsoup4', 'lxml'],
                             'minidom': ['dom_query'],
                             # Pin pydoctor version until https://github.com/twisted/pydoctor/issues/513 is fixed
                             'docs': ["pydoctor==21.2.2", "docutils"], 
                             'dev': ["tox", "mypy>=0.902", "httpretty", "pytest", "pytest-asyncio", 
                                     "types-requests", "types-pkg_resources" ]
                            },
    python_requires     =   '>=3.6',
)