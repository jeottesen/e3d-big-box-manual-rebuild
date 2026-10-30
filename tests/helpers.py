"""Shared by the tests: paths, and loading the committed data. Standard library only; no venv and no raw/ data are needed."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

def load(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f: return json.load(f)
