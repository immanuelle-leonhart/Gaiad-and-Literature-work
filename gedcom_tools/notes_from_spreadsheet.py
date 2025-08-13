#!/usr/bin/env python3
import sys, csv
csv.field_size_limit(sys.maxsize)   # allow very large note fields

import json
import time
import argparse
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_URL = "https://evolutionism.miraheze.org/w/api.php"

# ---------- Session & Auth (same shape as your current script) ----------
def create_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Notes-from-Spreadsheet/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy)"
    })
    retry = Retry(total=5, backoff_factor=2, status_forcelist=[429,500,502,503,504])
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

def login_to_wiki(session, username, password):
    # fetch login token
    r = session.get(API_URL, params={"action":"query","meta":"tokens","type":"login","format":"json"}, timeout=30)
    r.raise_for_status()
    login_token = r.json()["query"]["tokens"]["logintoken"]
    # do login
    data = {"action":"login","lgname":username,"lgpassword":password,"lgtoken":login_token,"format":"json"}
    r = session.post(API_URL, data=data, timeout=30)
    return r.json().get("login",{}).get("result") == "Success"

def get_csrf_token(session):
    r = session.get(API_URL, params={"action":"query","meta":"tokens","format":"json"})
    r.raise_for_status()
    return r.json()["query"]["tokens"]["csrftoken"]

# ---------- Mapping loader (your correspondence file) ----------
def load_master_mappings(mapping_path: Path):
    """
    Reads lines like:
      @I12345@<TAB>Q9876
    and returns {'@I12345@': 'Q9876', ...}
    """
    mappings = {}
    if not mapping_path.exists():
        return mappings
    with mapping_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("@I") and "\t" in line:
                parts = line.strip().split("\t")
                if len(parts) == 2:
                    mappings[parts[0]] = parts[1]
    return mappings  # :contentReference[oaicite:4]{index=4}

# ---------- Wikibase helpers (pared from your existing script) ----------
def remove_old_notes_property(session, qid, csrf_token):
    # Drop all P15 claims (legacy "notes_page") before adding P46
    r = session.get(API_URL, params={"action":"wbgetentities","ids":qid,"format":"json"})
    r.raise_for_status()
    ent = r.json().get("entities",{}).get(qid)
    if not ent:
        return False
    claims = ent.get("claims", {})
    if "P15" in claims:  # old notes property
        for claim in claims["P15"]:
            claim_id = claim["id"]
            session.post(API_URL, data={
                "action":"wbremoveclaims",
                "claim":claim_id,
                "token":csrf_token,
                "format":"json",
                "summary":"Removing old P15 notes property",
                "bot":1
            })
            time.sleep(0.2)
    return True  # :contentReference[oaicite:5]{index=5}

def add_notes_page_property(session, qid, notes_url, csrf_token):
    # Add P46 (notes page URL). If it already exists, API may error; we just pass that up.
    r = session.post(API_URL, data={
        "action":"wbcreateclaim",
        "entity":qid,
        "property":"P46",
        "snaktype":"value",
        "value":json.dumps(notes_url),
        "format":"json",
        "token":csrf_token,
        "summary":"Adding notes page URL (P46)",
        "bot":1
    })
    return r.json()  # :contentReference[oaicite:6]{index=6}

def create_or_update_notes_page(session, qid, notes_content, csrf_token):
    page_title = f"Notes:{qid}"
    wiki_content = f"""== Notes for [[Item:{qid}|{qid}]] ==

{notes_content}

[[Category:GEDCOM Notes Pages]]"""
    r = session.post(API_URL, data={
        "action":"edit",
        "title":page_title,
        "text":wiki_content,
        "token":csrf_token,
        "format":"json",
        "summary":f"Creating/updating notes page for {qid}",
        "bot":1
    })
    j = r.json()
    return ("edit" in j) and (j["edit"].get("result") == "Success")  # :contentReference[oaicite:7]{index=7}

# ---------- CSV reader ----------
def iter_spreadsheet_rows(csv_path: Path):
    """
    Expects columns: gedcom_id, qid, full_note (others are ignored)
    Only yields rows where we actually have some note text.
    """
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            full_note = (row.get("full_note") or "").strip()
            gedcom_id = (row.get("gedcom_id") or "").strip()
            qid = (row.get("qid") or "").strip()
            if not full_note:
                continue
            yield {"gedcom_id": gedcom_id, "qid": qid, "full_note": full_note}

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(description="Create/Update Notes:* pages only for rows in spreadsheet.")
    ap.add_argument("--csv", default="substantial_notes_analysis.csv", help="Input CSV with notes (default: substantial_notes_analysis.csv)")
    ap.add_argument("--mapping", default="gedcom_to_qid_mapping.txt", help="GEDCOM↔QID correspondences file")
    ap.add_argument("--username", required=True, help="Wiki username")
    ap.add_argument("--password", required=True, help="Wiki password")
    ap.add_argument("--sleep", type=float, default=1.0, help="Sleep between items (seconds)")
    ap.add_argument("--dry-run", action="store_true", help="Parse and resolve targets, but do not write to the wiki")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    map_path = Path(args.mapping)

    # Load correspondences
    mappings = load_master_mappings(map_path)

    # Build the worklist just from the spreadsheet
    rows = list(iter_spreadsheet_rows(csv_path))
    print(f"Loaded {len(rows)} spreadsheet rows with notes.")

    # Resolve QIDs
    work = []
    for r in rows:
        qid = r["qid"]
        if not qid:
            # try by gedcom_id
            gid = r["gedcom_id"]
            if gid and gid in mappings:
                qid = mappings[gid]
        if not qid:
            print(f"  SKIP: could not resolve QID for gedcom_id={r['gedcom_id']!r}")
            continue
        work.append((qid, r["full_note"]))

    print(f"Resolved {len(work)} rows to QIDs using CSV and mapping file.")

    if args.dry_run:
        print("Dry-run complete. No edits made.")
        return

    # Log in & get CSRF
    session = create_session()
    if not login_to_wiki(session, args.username, args.password):
        print("Login failed. Exiting.")
        return
    token = get_csrf_token(session)

    success = errors = 0
    for idx, (qid, note) in enumerate(work, 1):
        try:
            print(f"[{idx}/{len(work)}] QID={qid} – removing old P15, adding P46, writing Notes:{qid}")
            remove_old_notes_property(session, qid, token)
            time.sleep(0.2)

            # Add P46 — ignore if API says it's duplicate
            url = f"https://evolutionism.miraheze.org/wiki/Notes:{qid}"
            res = add_notes_page_property(session, qid, url, token)
            if "error" in res:
                print(f"    P46 add returned error (continuing): {res['error']}")
            time.sleep(0.2)

            # Create/Update notes page
            if create_or_update_notes_page(session, qid, note, token):
                print("    OK")
                success += 1
            else:
                print("    FAILED to write page")
                errors += 1

            time.sleep(args.sleep)

        except Exception as e:
            print(f"    ERROR: {e}")
            errors += 1

    print(f"\nDone. Success: {success}, Errors: {errors}")

if __name__ == "__main__":
    main()
