#!/usr/bin/env python3
"""
Bulk-remove item descriptions on a Wikibase (evolutionism.miraheze.org).

Iterates Q1..Q100000. For each existing item, removes *all* language
short descriptions (if any). Skips non-existing items. Adds a clear
edit summary for each change.

Usage examples
--------------
# Dry run (no edits), show what would be removed for the first 200 items
python wipe_descriptions_q1_q100000.py --dry-run --end 200

# Real run with credentials passed via env vars (recommended)
#   set WIKI_USER and WIKI_PASS in your environment first
python wipe_descriptions_q1_q100000.py

# Or pass credentials explicitly (not recommended to keep in shell history)
python wipe_descriptions_q1_q100000.py --user "YourUser" --password "YourPassword"

Notes
-----
* Uses the Action API endpoint: https://evolutionism.miraheze.org/w/api.php
* Item existence is checked via wbgetentities.
* Descriptions are removed with wbsetdescription by setting value to "" (empty string).
* Respects maxlag and does simple rate-limiting/backoff.
"""

import os
import sys
import time
import json
import argparse
import logging
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_ENDPOINT = "https://evolutionism.miraheze.org/w/api.php"
USER_AGENT = (
    "Evolutionism Description Wiper/1.0 (+https://evolutionism.miraheze.org/; "
    "contact: site admin)"
)

# --- HTTP session with retry/backoff -------------------------------------------------

def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    retry = Retry(
        total=6,
        backoff_factor=1.5,  # 0s, 1.5s, 3s, 4.5s, 6s, 7.5s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

# --- Auth helpers --------------------------------------------------------------------

def get_token(session: requests.Session, token_type: str) -> str:
    params = {
        "action": "query",
        "meta": "tokens",
        "type": token_type,
        "format": "json",
    }
    r = session.get(API_ENDPOINT, params=params, timeout=45)
    r.raise_for_status()
    j = r.json()
    key = f"{token_type}token"
    return j["query"]["tokens"][key]


def login(session: requests.Session, username: str, password: str) -> None:
    """Legacy action=login flow (simple and works fine on Miraheze)."""
    login_token = get_token(session, "login")
    data = {
        "action": "login",
        "lgname": username,
        "lgpassword": password,
        "lgtoken": login_token,
        "format": "json",
    }
    r = session.post(API_ENDPOINT, data=data, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("login", {}).get("result") != "Success":
        raise RuntimeError(f"Login failed: {j}")

# --- Wikibase helpers ----------------------------------------------------------------

def fetch_entity(session: requests.Session, qid: str) -> Optional[dict]:
    params = {
        "action": "wbgetentities",
        "ids": qid,
        "format": "json",
    }
    r = session.get(API_ENDPOINT, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()
    ent = j.get("entities", {}).get(qid)
    if not ent or ent.get("missing") is not None:
        return None
    return ent


def remove_descriptions(
    session: requests.Session,
    qid: str,
    languages: List[str],
    csrf: str,
    summary: str,
    throttle: float = 0.2,
) -> Dict[str, bool]:
    """Return dict lang->success."""
    results: Dict[str, bool] = {}
    for lang in languages:
        data = {
            "action": "wbsetdescription",
            "id": qid,
            "language": lang,
            "value": "",  # empty value deletes description
            "format": "json",
            "token": csrf,
            "summary": summary,
            "bot": 1,
            "maxlag": 5,
            "assert": "user",
        }
        try:
            r = session.post(API_ENDPOINT, data=data, timeout=60)
            j = r.json()
            ok = j.get("wbsetdescription", {}).get("result") == "Success"
            results[lang] = bool(ok)
        except Exception:
            results[lang] = False
        time.sleep(throttle)
    return results

# --- Main routine --------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Remove descriptions Q1..Q100000 on Evolutionism Wikibase")
    ap.add_argument("--start", type=int, default=1, help="Starting numeric Q id (default: 1)")
    ap.add_argument("--end", type=int, default=100000, help="Ending numeric Q id inclusive (default: 100000)")
    ap.add_argument("--sleep", type=float, default=0.05, help="Sleep between items in seconds (default: 0.05)")
    ap.add_argument(
        "--summary",
        default="Descriptions were erroneously added; removing.",
        help="Edit summary to use",
    )
    ap.add_argument("--dry-run", action="store_true", help="Do not edit; just report")
    ap.add_argument("--user", default="Immanuelle", help="Username (or set WIKI_USER env var)")
    ap.add_argument("--password", default="1996ToOmega!", help="Password (or set WIKI_PASS env var)")
    ap.add_argument("--resume", type=int, default=None, help="Resume from this numeric Q id (overrides --start)")
    args = ap.parse_args()

    start = args.resume if args.resume is not None else args.start
    end = args.end

    session = make_session()

    if not args.dry_run:
        if not args.user or not args.password:
            print("ERROR: Missing credentials. Use --user/--password or WIKI_USER/WIKI_PASS env vars.")
            sys.exit(2)
        print("Logging in…")
        login(session, args.user, args.password)
        csrf = get_token(session, "csrf")
    else:
        csrf = ""  # unused

    processed = 0
    changed_items = 0

    for n in range(start, end + 1):
        qid = f"Q{n}"
        try:
            ent = fetch_entity(session, qid)
        except Exception as e:
            print(f"{qid}: fetch failed, will skip ({e})")
            time.sleep(0.5)
            continue

        if ent is None:
            # Deleted or never existed
            if n % 1000 == 0:
                print(f"Up to {qid}: still scanning… (skipping non-existing)")
            time.sleep(args.sleep)
            continue

        # Collect available description languages
        descriptions = ent.get("descriptions", {}) or {}
        langs = list(descriptions.keys())

        if not langs:
            if n % 500 == 0:
                print(f"{qid}: no descriptions to remove")
            time.sleep(args.sleep)
            continue

        if args.dry_run:
            print(f"DRY: {qid} would remove descriptions for languages: {', '.join(langs)}")
        else:
            results = remove_descriptions(session, qid, langs, csrf, args.summary)
            ok_langs = [l for l, ok in results.items() if ok]
            bad_langs = [l for l, ok in results.items() if not ok]
            if ok_langs:
                changed_items += 1
                print(f"{qid}: removed {len(ok_langs)} descriptions ({', '.join(ok_langs)})")
            if bad_langs:
                print(f"{qid}: FAILED removing ({', '.join(bad_langs)})")

        processed += 1
        time.sleep(args.sleep)

    print("\nDone.")
    print(f"Scanned items: {end - start + 1}")
    if not args.dry_run:
        print(f"Items with at least one description removed: {changed_items}")


if __name__ == "__main__":
    main()
