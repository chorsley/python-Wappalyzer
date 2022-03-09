from setuptools import setup, find_packages
import pathlib
import sys

requirements = [
        'beautifulsoup4',
        'lxml',
        'requests',
        'aiohttp',
        'httpretty',
        'aioresponses',
        'cached_property',
    ]

# Simulate that 'beautifulsoup4' and 'lxml' are default extra dependencies
# that can be disabled by [no-lxml] extra. (https://github.com/pypa/setuptools/issues/1139)
if any('no-lxml' in arg for arg in sys.argv[1:]):
    requirements.remove('beautifulsoup4')
    requirements.remove('lxml')

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
    install_requires    =   requirements,
    extras_require      =   {'no-lxml': ['dom-query'],
                             # Pin pydoctor version until https://github.com/twisted/pydoctor/issues/513 if fixed
                             'docs': ["pydoctor==21.2.2", "docutils"], 
                             'dev': ["tox", "mypy>=0.902", "pytest", "pytest-asyncio", 
                                     "types-requests", "types-pkg_resources" ]},
    python_requires     =   '>=3.6',
)
