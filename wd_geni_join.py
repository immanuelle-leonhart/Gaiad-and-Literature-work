
import argparse
import csv
import re
import sys
import time
from typing import Dict, Iterable, List, Tuple
import requests
import pandas as pd

QID_RE = re.compile(r"(?:^|/)(Q[1-9]\d*)\b")

def extract_qid(s: str) -> str:
    if not isinstance(s, str):
        return ""
    m = QID_RE.search(s.strip())
    return m.group(1) if m else ""

def chunked(iterable: List[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]

def build_sparql(qids: List[str]) -> str:
    values = " ".join(f"wd:{q}" for q in qids)
    return f"""
SELECT ?item ?geni WHERE {{
  VALUES ?item {{ {values} }}
  ?item wdt:P2600 ?geni .
}}
"""


def fetch_batch(qids: List[str], endpoint: str, session: requests.Session, retries: int = 3, timeout: int = 60) -> Dict[str, str]:
    if not qids:
        return {}
    query = build_sparql(qids)
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "wd-geni-join/1.0 (contact: your-email@example.com)"
    }
    params = {"query": query}
    for attempt in range(1, retries+1):
        try:
            resp = session.get(endpoint, headers=headers, params=params, timeout=timeout)
            if resp.status_code == 429:
                # too many requests, back off
                wait = min(60, 2 ** attempt)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            out: Dict[str, str] = {}
            for b in data.get("results", {}).get("bindings", []):
                item_url = b["item"]["value"]          # e.g. https://www.wikidata.org/entity/Q42
                geni = b["geni"]["value"]              # literal string ID (not a URL)
                qid = item_url.rsplit("/", 1)[-1]
                out[qid] = geni
            return out
        except Exception as e:
            if attempt == retries:
                raise
            time.sleep(2 ** attempt)
    return {}

def main():
    ap = argparse.ArgumentParser(description="Append Wikidata Geni.com profile IDs (P2600) to a CSV.")
    ap.add_argument("input", help="Input CSV path")
    ap.add_argument("output", help="Output CSV path")
    ap.add_argument("--wikidata-col", type=int, default=1, help="Zero-based index of column containing Wikidata item (QID or URL). Default: 1")
    ap.add_argument("--chunksize", type=int, default=400, help="Batch size for SPARQL VALUES. Default: 400")
    ap.add_argument("--sleep", type=float, default=0.2, help="Seconds to sleep between batches. Default: 0.2")
    ap.add_argument("--endpoint", default="https://query.wikidata.org/sparql", help="SPARQL endpoint URL")
    args = ap.parse_args()

    # Read CSV with pandas to preserve rows and columns; no header assumption.
    try:
        df = pd.read_csv(args.input, header=None, dtype=str, keep_default_na=False)
    except Exception:
        # Fallback to python csv if pandas has issues
        with open(args.input, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        df = pd.DataFrame(rows)

    if args.wikidata_col < 0 or args.wikidata_col >= df.shape[1]:
        print(f"Error: --wikidata-col {args.wikidata_col} is out of range for this CSV with {df.shape[1]} columns.", file=sys.stderr)
        sys.exit(1)

    # Extract QIDs
    qids_series = df.iloc[:, args.wikidata_col].map(extract_qid)
    qids = [q for q in qids_series.tolist() if q]
    unique_qids = sorted(set(qids))

    # Query in batches
    session = requests.Session()
    mapping: Dict[str, str] = {}

    for batch in chunked(unique_qids, args.chunksize):
        res = fetch_batch(batch, args.endpoint, session)
        mapping.update(res)
        time.sleep(args.sleep)

    # Build output column aligned with original rows
    geni_col: List[str] = []
    for val in df.iloc[:, args.wikidata_col].tolist():
        qid = extract_qid(val)
        geni_col.append(mapping.get(qid, ""))

    # Append new column
    df_out = df.copy()
    df_out["geni_id"] = geni_col

    # Write
    df_out.to_csv(args.output, index=False, header=False)

if __name__ == "__main__":
    main()
