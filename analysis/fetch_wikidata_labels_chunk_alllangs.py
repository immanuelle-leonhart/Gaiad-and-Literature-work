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
UA = "WikidataSPARQLLabelDump/2.0 (contact: your-email@example.com)"

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
    # de-dup preserving order
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
    return " ".join(f"wd:{q}" for q in qids)

def fetch_all_labels_for_chunk(session, qids):
    # Returns list of rows: (qid, lang, label)
    values = build_values_block(qids)
    sparql = f"""
SELECT ?item (LANG(?l) AS ?lang) (STR(?l) AS ?label) WHERE {{
  VALUES ?item {{ {values} }}
  ?item rdfs:label ?l .
}}
"""
    data = wdqs_query(session, sparql)
    out = []
    for b in data.get("results", {}).get("bindings", []):
        uri = b["item"]["value"]
        qid = uri.rsplit("/", 1)[-1]
        lang = b["lang"]["value"]
        label = b["label"]["value"]
        out.append((qid, lang, label))
    return out

def fetch_all_descs_for_chunk(session, qids):
    # Returns list of rows: (qid, lang, desc)
    values = build_values_block(qids)
    sparql = f"""
SELECT ?item (LANG(?d) AS ?lang) (STR(?d) AS ?desc) WHERE {{
  VALUES ?item {{ {values} }}
  ?item schema:description ?d .
}}
"""
    data = wdqs_query(session, sparql)
    out = []
    for b in data.get("results", {}).get("bindings", []):
        uri = b["item"]["value"]
        qid = uri.rsplit("/", 1)[-1]
        lang = b["lang"]["value"]
        desc = b["desc"]["value"]
        out.append((qid, lang, desc))
    return out

def main():
    ap = argparse.ArgumentParser(description="Fetch all labels & descriptions (all languages) via SPARQL per chunk (no per-language loop).")
    ap.add_argument("input_csv", help="Input CSV with QIDs in 2nd column (1st ignored).")
    ap.add_argument("output_csv", help="Output CSV path.")
    ap.add_argument("--chunk", type=int, default=400, help="QIDs per VALUES block (default 400).")
    ap.add_argument("--sleep", type=float, default=0.2, help="Sleep seconds between WDQS requests (default 0.2).")
    args = ap.parse_args()

    qids = read_qids_from_csv(args.input_csv)
    if not qids:
        print("No QIDs detected in column 2.", file=sys.stderr)
        sys.exit(1)
    print(f"Total QIDs: {len(qids)}")

    session = make_session()

    # Accumulators: qid -> lang -> value
    labels = defaultdict(dict)
    descs = defaultdict(dict)
    langset = set()

    # Process in chunks: two queries per chunk (labels + descriptions)
    chunks = list(chunked(qids, args.chunk))
    for idx, chunk in enumerate(chunks, start=1):
        print(f"[{idx}/{len(chunks)}] Fetching labels for {len(chunk)} QIDs...")
        try:
            rows = fetch_all_labels_for_chunk(session, chunk)
            for qid, lang, label in rows:
                labels[qid][lang] = label
                langset.add(lang)
        except Exception as e:
            print(f"Warning: labels query failed for chunk {idx}: {e}", file=sys.stderr)

        time.sleep(args.sleep)

        print(f"[{idx}/{len(chunks)}] Fetching descriptions for {len(chunk)} QIDs...")
        try:
            rows = fetch_all_descs_for_chunk(session, chunk)
            for qid, lang, desc in rows:
                descs[qid][lang] = desc
                langset.add(lang)
        except Exception as e:
            print(f"Warning: descriptions query failed for chunk {idx}: {e}", file=sys.stderr)

        time.sleep(args.sleep)

    # Order languages: en first, mul second, then alphabetical
    ordered_langs = []
    if "en" in langset:
        ordered_langs.append("en")
    if "mul" in langset:
        ordered_langs.append("mul")
    for lang in sorted(langset):
        if lang not in ordered_langs:
            ordered_langs.append(lang)

    # Build header
    header = ["wikidata_id"]
    for lang in ordered_langs:
        header.append(f"label_{lang}")
        header.append(f"desc_{lang}")

    # Write CSV
    os.makedirs(os.path.dirname(os.path.abspath(args.output_csv)), exist_ok=True)
    with open(args.output_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for qid in qids:
            row = [qid]
            ldict = labels.get(qid, {})
            ddict = descs.get(qid, {})
            for lang in ordered_langs:
                row.append(ldict.get(lang, ""))
                row.append(ddict.get(lang, ""))
            w.writerow(row)

    print(f"Done. Wrote: {args.output_csv}")
    print(f"Languages found: {len(ordered_langs)} (2 columns per language).")

if __name__ == "__main__":
    main()
