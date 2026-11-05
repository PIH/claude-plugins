#!/usr/bin/env python3
"""Tell the user if a newer version of the PIH `ocl` plugin is available.

Compares this plugin's version (from its own .claude-plugin/plugin.json) with the
version on the main branch of PIH/claude-plugins on GitHub. Read-only, needs no
token, and caches the result for a day in ~/.cache/ocl/update-check.json.

Prints one line and always exits 0, so a failed check never blocks real work:
  UPDATE AVAILABLE: installed <x>, latest <y>
  up to date (<x>)
  ahead of the published version (<x> > <y>)      e.g. a local --plugin-dir copy
  update check skipped: <reason>
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

LATEST_URL = ("https://raw.githubusercontent.com/PIH/claude-plugins/main/"
              "plugins/ocl/.claude-plugin/plugin.json")
CACHE_FILE = Path.home() / ".cache" / "ocl" / "update-check.json"
CACHE_SECONDS = 24 * 60 * 60
MANIFEST = Path(__file__).resolve().parents[3] / ".claude-plugin" / "plugin.json"


def parse_version(v):
    if not isinstance(v, str):
        return None
    m = re.fullmatch(r"\s*v?(\d+(?:\.\d+)*)\s*", v)
    return tuple(int(x) for x in m.group(1).split(".")) if m else None


def status(installed, latest):
    a, b = parse_version(installed), parse_version(latest)
    if a is None or b is None:
        return "unknown"
    n = max(len(a), len(b))
    a, b = a + (0,) * (n - len(a)), b + (0,) * (n - len(b))
    return "behind" if a < b else "ahead" if a > b else "current"


def installed_version():
    return json.loads(MANIFEST.read_text())["version"]


def fetch_latest():
    with urllib.request.urlopen(LATEST_URL, timeout=5) as r:
        return json.loads(r.read().decode("utf-8"))["version"]


def _cached(cache):
    try:
        if time.time() - cache.stat().st_mtime < CACHE_SECONDS:
            return json.loads(cache.read_text())["latest"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def run(installed, fetch, cache):
    latest = _cached(cache)
    if latest is None:
        try:
            latest = fetch()
        except Exception as e:  # network, HTTP, bad JSON: never block real work
            print(f"update check skipped: {type(e).__name__}: {e}")
            return 0
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps({"latest": latest}))
        except OSError:
            pass
    s = status(installed, latest)
    if s == "behind":
        print(f"UPDATE AVAILABLE: installed {installed}, latest {latest}")
    elif s == "current":
        print(f"up to date ({installed})")
    elif s == "ahead":
        print(f"ahead of the published version ({installed} > {latest})")
    else:
        print(f"update check skipped: can't compare {installed!r} with {latest!r}")
    return 0


def main():
    try:
        installed = installed_version()
    except (OSError, ValueError, KeyError) as e:
        print(f"update check skipped: can't read plugin.json: {e}")
        return 0
    return run(installed, fetch_latest, CACHE_FILE)


if __name__ == "__main__":
    sys.exit(main())
