from setuptools import setup, find_packages

setup(
    name="python-Wappalyzer",
    version="0.2.2",
    description="Python implementation of the Wappalyzer web application "
                "detection utility",
    author="Clay McClure",
    author_email="clay@daemons.net",
    url="https://github.com/chorsley/python-Wappalyzer",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
    ],
    packages=find_packages(),
    package_data={'Wappalyzer': ['data/apps.json']},
    install_requires=[
        'BeautifulSoup4',
        'requests',
    ]
)
