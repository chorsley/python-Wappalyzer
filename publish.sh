set -e
rm -fr ./dist
python3 setup.py build check sdist bdist_wheel
python3 -m twine upload --verbose dist/*
git tag -a "$(python3 setup.py -V)" -m "python-Wappalyzer version $(python3 setup.py -V)" 
git push --tags
