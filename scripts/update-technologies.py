import argparse
import datetime
import pprint
from pathlib import Path

from Wappalyzer.fingerprint import get_latest_tech_data

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('technologies_py_moddule', action='store', type=Path, nargs=1)
    return parser

TECHNOLOGIES_PY_MOD_DOC = """
This module contains the raw fingerprints data. It has been automatically generated on the %s.
"""

if __name__ == "__main__":
    args = get_parser().parse_args()
    with args.technologies_py_moddule[0].open(mode='w', encoding='utf-8') as f:
        text = f"TECHNOLOGIES_DATA = {pprint.pformat(get_latest_tech_data(), indent=4, width=120)}"
        text = f'"""{TECHNOLOGIES_PY_MOD_DOC%datetime.datetime.now().isoformat()}"""\n\n{text}'
        f.write(text)
