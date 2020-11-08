from setuptools import setup, find_packages
import sys
if sys.version_info[0] < 3: 
    raise RuntimeError("You must use Python 3, sorry")
import pathlib
setup(
    name="python-Wappalyzer",
    version="0.3.1",
    description="Python implementation of the Wappalyzer web application "
                "detection utility",
    long_description=( pathlib.Path(__file__).parent / "README.md" ).read_text(),
    long_description_content_type   =   "text/markdown",
    author="Clay McClure, Marcello Salvati (@byt3bl33d3r)",
    author_email="clay@daemons.net",
    url="https://github.com/chorsley/python-Wappalyzer",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ],
    packages=find_packages(),
    package_data={'Wappalyzer': ['data/technologies.json']},
    install_requires=[
        'beautifulsoup4',
        'lxml',
        'requests',
        'aiohttp',
        'httpretty',
        'aioresponses'
    ]
)
