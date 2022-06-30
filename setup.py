from setuptools import setup, find_packages
import pathlib

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
    install_requires    =   [   'beautifulsoup4', 
                                'lxml',
                                'requests',
                                'aiohttp',
                                'cached_property', ],
    extras_require      =   {
                             # Pin pydoctor version until https://github.com/twisted/pydoctor/issues/513 is fixed
                             'docs': ["pydoctor==21.2.2", "docutils"], 
                             'dev': ["tox", "mypy>=0.902", "httpretty", "pytest", "pytest-asyncio", 
                                     "types-requests", "types-pkg_resources", "aioresponses"]
                            },
    python_requires     =   '>=3.6',
)