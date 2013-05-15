from setuptools import setup

setup(
    name = "python-Wappalyzer",
    version = "0.1.0",
    description = "Python implementation of the Wappalyzer web application detection utility",
    author = "Clay McClure",
    author_email = "clay@daemons.net",
    url = "https://github.com/claymation/python-Wappalyzer",
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Internet :: WWW/HTTP',
    ],
    py_modules = ['Wappalyzer'],
    data_files = [('', ['apps.json'])],
    install_requires = [
        'BeautifulSoup==3.2.1',
        'requests',
    ],
    test_suite = 'nose.collector',
    tests_require = [
        'httpretty==0.5.12',
        'nose==1.2.1',
    ]
)
