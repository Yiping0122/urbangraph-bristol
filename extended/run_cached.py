"""Shim: run fetch_bristol.py unchanged against cached Overpass-format data."""
import json, runpy, sys, types
cache = json.load(open('overpass_cache.json'))
class Resp:
    def raise_for_status(self): pass
    def json(self): return cache
import requests
requests.post = lambda *a, **k: Resp()
runpy.run_path(sys.argv[1], run_name='__main__')
