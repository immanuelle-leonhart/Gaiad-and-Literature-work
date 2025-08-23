#!/usr/bin/env python3
import argparse
import csv
import os
import re
import sys
import time
from collections import defaultdict, OrderedDict

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("This script requires the 'requests' package. Install with: pip install requests", file=sys.stderr)
    raise

WDQS = "https://query.wikidata.org/sparql"
UA = "WikidataSPARQLLabelDump/1.0 (contact: your-email@example.com)"

def make_session():
    s = requests.Session()
    retries = Retry(
        total=6,
        backoff_factor=0.7,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    s.headers.update({"User-Agent": UA})
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

def read_qids_from_csv(path):
    qids = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 2:
                continue
            q = (row[1] or "").strip()
            if re.match(r"^Q\d+$", q):
                qids.append(q)
    # de-dup, preserve order
    seen = set()
    out = []
    for q in qids:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out

def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

def wdqs_query(session, sparql, timeout=120):
    headers = {"Accept": "application/sparql-results+json"}
    data = {"query": sparql}
    resp = session.post(WDQS, data=data, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.json()

def build_values_block(qids):
    # VALUES ?item { wd:Q42 wd:Q1 ... }
    parts = " ".join(f"wd:{q}" for q in qids)
    return f"VALUES ?item {{ {parts} }}\n"

def discover_languages(session, qids, chunk_size=500, sleep=0.2):
    langs = set()

    # Labels
    for i, chunk in enumerate(chunked(qids, chunk_size), start=1):
        values = build_values_block(chunk)
        sparql = f"""
SELECT DISTINCT (LANG(?l) AS ?lang) WHERE {{
  {values}
  ?item rdfs:label ?l .
}}
"""
        data = wdqs_query(session, sparql)
        for b in data.get("results", {}).get("bindings", []):
            lang = b.get("lang", {}).get("value")
            if lang:
                langs.add(lang)
        time.sleep(sleep)

    # Descriptions
    for i, chunk in enumerate(chunked(qids, chunk_size), start=1):
        values = build_values_block(chunk)
        sparql = f"""
SELECT DISTINCT (LANG(?d) AS ?lang) WHERE {{
  {values}
  ?item schema:description ?d .
}}
"""
        data = wdqs_query(session, sparql)
        for b in data.get("results", {}).get("bindings", []):
            lang = b.get("lang", {}).get("value")
            if lang:
                langs.add(lang)
        time.sleep(sleep)

    return sorted(langs)

def fetch_lang_labels(session, qids, lang, chunk_size=500, sleep=0.2):
    # Returns dict qid -> label string (for given lang)
    out = {}
    for i, chunk in enumerate(chunked(qids, chunk_size), start=1):
        values = build_values_block(chunk)
        # Using rdfs:label with explicit LANG filter; STR() to avoid lang tags in JSON
        sparql = f"""
SELECT ?item (STR(?l) AS ?label) WHERE {{
  {values}
  ?item rdfs:label ?l .
  FILTER(LANG(?l) = "{lang}")
}}
"""
        data = wdqs_query(session, sparql)
        for b in data.get("results", {}).get("bindings", []):
            item_uri = b["item"]["value"]
            qid = item_uri.rsplit("/", 1)[-1]
            out[qid] = b["label"]["value"]
        time.sleep(sleep)
    return out

def fetch_lang_descriptions(session, qids, lang, chunk_size=500, sleep=0.2):
    out = {}
    for i, chunk in enumerate(chunked(qids, chunk_size), start=1):
        values = build_values_block(chunk)
        sparql = f"""
SELECT ?item (STR(?d) AS ?desc) WHERE {{
  {values}
  ?item schema:description ?d .
  FILTER(LANG(?d) = "{lang}")
}}
"""
        data = wdqs_query(session, sparql)
        for b in data.get("results", {}).get("bindings", []):
            item_uri = b["item"]["value"]
            qid = item_uri.rsplit("/", 1)[-1]
            out[qid] = b["desc"]["value"]
        time.sleep(sleep)
    return out

def write_wide_csv(qids, langs_ordered, labels_by_lang, descs_by_lang, output_csv):
    # Header
    header = ["wikidata_id"]
    for lang in langs_ordered:
        header.append(f"label_{lang}")
        header.append(f"desc_{lang}")

    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for qid in qids:
            row = [qid]
            for lang in langs_ordered:
                row.append(labels_by_lang.get(lang, {}).get(qid, ""))
                row.append(descs_by_lang.get(lang, {}).get(qid, ""))
            w.writerow(row)

def main():
    ap = argparse.ArgumentParser(description="Fetch all labels & descriptions (all languages incl. mul) for QIDs via SPARQL, write wide CSV.")
    ap.add_argument("input_csv", help="Input CSV with QIDs in 2nd column (1st column ignored).")
    ap.add_argument("output_csv", help="Output CSV path.")
    ap.add_argument("--chunk", type=int, default=500, help="QIDs per SPARQL VALUES block (default 500).")
    ap.add_argument("--sleep", type=float, default=0.2, help="Sleep seconds between WDQS requests (default 0.2).")
    args = ap.parse_args()

    qids = read_qids_from_csv(args.input_csv)
    if not qids:
        print("No QIDs detected in column 2.", file=sys.stderr)
        sys.exit(1)
    print(f"Total QIDs: {len(qids)}")

    session = make_session()

    print("Discovering languages across labels/descriptions...")
    langs = discover_languages(session, qids, chunk_size=args.chunk, sleep=args.sleep)
    # Order languages: en first (if any), then mul, then alphabetical others.
    ordered = []
    if "en" in langs:
        ordered.append("en")
    if "mul" in langs:
        ordered.append("mul")
    for lang in langs:
        if lang not in ("en", "mul"):
            ordered.append(lang)
    print(f"Discovered languages: {len(ordered)}")

    labels_by_lang = {}
    descs_by_lang = {}

    for lang in ordered:
        print(f"[{lang}] fetching labels...")
        labels_by_lang[lang] = fetch_lang_labels(session, qids, lang, chunk_size=args.chunk, sleep=args.sleep)
        print(f"[{lang}] labels: {len(labels_by_lang[lang])}")

        print(f"[{lang}] fetching descriptions...")
        descs_by_lang[lang] = fetch_lang_descriptions(session, qids, lang, chunk_size=args.chunk, sleep=args.sleep)
        print(f"[{lang}] descriptions: {len(descs_by_lang[lang])}")

    print("Writing output CSV...")
    write_wide_csv(qids, ordered, labels_by_lang, descs_by_lang, args.output_csv)
    print(f"Done. Wrote: {args.output_csv}")

if __name__ == "__main__":
    main()
