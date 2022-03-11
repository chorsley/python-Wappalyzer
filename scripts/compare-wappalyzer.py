import argparse
import shutil
import subprocess
from typing import Dict, List, Set
from urllib.parse import urlparse
import json

from Wappalyzer import Wappalyzer, WebPage
from Wappalyzer.fingerprint import Technology

# Taken and adapted from https://github.com/tristanlatr/MassWappalyzer/blob/master/masswappalyzer.py

class IWappalyzer:
    def analyze(self, host) -> Set[str]:
        ...

class PythonWappalyzer(IWappalyzer):
    def __init__(self) -> None:
        self._wappalyzer = Wappalyzer.latest()
    
    def analyze(self, host:str) -> Set[str]:
        return self._wappalyzer.analyze(WebPage.new_from_url(ensure_scheme(host)))

class JsWappalyzer(IWappalyzer):
    def __init__(self) -> None:
        self.wappalyzerpath = None
        if shutil.which("wappalyzer"):
            self.wappalyzerpath = [ 'wappalyzer' ]
        elif shutil.which("docker"):
            # Test if docker image is installed
            o = subprocess.run( args=[ 'docker', 'image', 'ls' ], stdout=subprocess.PIPE )
            if 'wappalyzer/cli' in o.stdout.decode() :
                self.wappalyzerpath = [ 'docker', 'run', '--rm', 'wappalyzer/cli' ]
        if self.wappalyzerpath is None:
            raise AssertionError("Can't wappalyzer/cli in your system.")

    def analyze(self, host) -> Set[str]:
        return set((t.name for t in self._analyze(host)))
    
    def _analyze(self, host:str) -> List[Technology]:
        cmd = self.wappalyzerpath + [ensure_scheme(host)]
        p = subprocess.run(args=cmd, timeout=600, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if p.returncode == 0:
            result = json.loads(p.stdout)
        techs = []
        for r in result['technologies']:
            t = Technology(r['name'])
            t.confidence[''] = int(r['confidence'])
            t.versions = [r['version']]
            techs.append(t)
        return techs

def ensure_scheme(url:str) -> str:
    # Strip URL string
    url=url.strip()
    # Format URL with scheme indication if not already present
    p_url=list(urlparse(url))
    if p_url[0]=="": 
        url='http://'+url
    return url

def get_parser() -> argparse.ArgumentParser:
    """Get the CLI `argparse.ArgumentParser`"""
    parser = argparse.ArgumentParser(description="Helper to compare python-Wappalyzer and Wappalyzer", prog="python -m test-wappalyzer")
    parser.add_argument('url', help='URL to analyze with both python-Wappalyzer and oroginal Wappalyzer.')
    return parser

if __name__ == '__main__':
    args = get_parser().parse_args()
    results: Dict[str, Set[str]] = {}
    for wappalyzercls in (PythonWappalyzer, JsWappalyzer):
        _set = wappalyzercls().analyze(args.url)
        _name = wappalyzercls.__name__
        results[_name] = _set
        print(f"{_name} results (short): {_set}")
    print(f"python-Wappalyzer results contains {(len(results['PythonWappalyzer'])*100)/len(results['JsWappalyzer'])}% less results than the JS Wappalyzer.")
    assert results['JsWappalyzer'].issuperset(results['PythonWappalyzer']), \
        f"Looks like python-Wappalyzer got some invalid results. These items are not detected in the JS version: {results['PythonWappalyzer'] - results['JsWappalyzer']}"
