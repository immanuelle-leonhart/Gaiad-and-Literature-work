#!/usr/bin/env python3
# wd_bulk_props.py
import sys
import csv
import time
import math
import requests
from collections import defaultdict

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "WDQS-bulk-genealogy-props/1.0 (contact: your-email@example.com)"

# The properties you asked for, in the order provided
PROPS = [
    "P7931","P6821","P8857","P7969","P9129","P3217","P6996","P2889","P4193","P535",
    "P4108","P7352","P8094","P9644","P6192","P2503","P4116","P3051","P9195","P4620",
    "P9280","P5452","P7434","P9495","P5871","P8462","P1185","P13492","P7929","P8143",
    "P8356","P8172","P4963","P6303","P5259","P5324","P4819","P5316","P5536","P4820",
    "P4638","P4159","P7607","P2949","P1819"
]

BATCH_SIZE = 250         # Adjust if needed (150–400 is usually stable)
RETRY_LIMIT = 5
RETRY_BACKOFF = 5.0      # seconds (exponential)

def build_sparql(qids, props):
    # Build VALUES list
    values = " ".join(f"(wd:{qid})" for qid in qids)

    # OPTIONAL + value-vars for each property
    opt_blocks = []
    sel_aggs   = []
    for p in props:
        v = f"?v{p[1:]}"             # e.g. ?v7931
        out = f"?{p}"                 # e.g. ?P7931 (final column/variable)
        opt_blocks.append(f"  OPTIONAL {{ ?item wdt:{p} {v} . }}")
        # GROUP_CONCAT handles multi-values, empty if none
        sel_aggs.append(f"(GROUP_CONCAT(DISTINCT {v};separator='|') AS {out})")

    query = f"""
SELECT ?item {' '.join(sel_aggs)} WHERE {{
  VALUES (?item) {{ {values} }}
{chr(10).join(opt_blocks)}
}}
GROUP BY ?item
"""
    return query

def run_wdqs(query):
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": USER_AGENT,
    }
    data = {"query": query}
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            resp = requests.post(ENDPOINT, data=data, headers=headers, timeout=120)
            if resp.status_code == 200:
                return resp.json()
            # 429 or 5xx: backoff
            if resp.status_code in (429, 500, 502, 503, 504):
                sleep_s = RETRY_BACKOFF * (2 ** (attempt - 1))
                time.sleep(sleep_s)
                continue
            # Other non-200: raise
            resp.raise_for_status()
        except requests.RequestException:
            sleep_s = RETRY_BACKOFF * (2 ** (attempt - 1))
            time.sleep(sleep_s)
    raise RuntimeError("WDQS request failed after retries.")

def read_qids_from_csv(path):
    qids = []
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            if len(row) < 2:
                continue
            qid = row[1].strip()
            if qid and qid[0].upper() == "Q" and qid[1:].isdigit():
                qids.append(qid)
    return qids

def write_enriched_csv(in_path, out_path, results_map):
    # Read input rows so we can preserve order and past through column 1
    with open(in_path, "r", newline="", encoding="utf-8-sig") as fin, \
         open(out_path, "w", newline="", encoding="utf-8") as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)

        # Build header: original columns + props
        # If input has a header, we won't try to detect; we pass through as-is and append prop columns.
        # If there's no header, this still works (first row becomes "header-like").
        first_row = next(reader)
        header = list(first_row) + PROPS
        writer.writerow(header)

        # write first row's data + property values
        def row_out(row):
            # row[1] should be QID; if missing, produce empty prop cols
            qid = row[1].strip() if len(row) > 1 else ""
            propvals = []
            if qid in results_map:
                for p in PROPS:
                    propvals.append(results_map[qid].get(p, ""))
            else:
                propvals = [""] * len(PROPS)
            return list(row) + propvals

        writer.writerow(row_out(first_row))
        for row in reader:
            writer.writerow(row_out(row))

def main():
    if len(sys.argv) != 3:
        print("Usage: python wd_bulk_props.py <input.csv> <output.csv>")
        sys.exit(1)

    in_csv = sys.argv[1]
    out_csv = sys.argv[2]

    qids = read_qids_from_csv(in_csv)
    if not qids:
        print("No valid QIDs found in column 2 of input CSV.")
        sys.exit(1)

    # Prepare results map: QID -> { Pxxxx: "val|val2" }
    results = defaultdict(dict)

    # Batch through WDQS
    total = len(qids)
    for i in range(0, total, BATCH_SIZE):
        batch = qids[i:i+BATCH_SIZE]
        query = build_sparql(batch, PROPS)
        data = run_wdqs(query)

        bindings = data.get("results", {}).get("bindings", [])
        for b in bindings:
            item_uri = b["item"]["value"]                  # e.g. https://www.wikidata.org/entity/Q42
            qid = item_uri.rsplit("/", 1)[-1]              # Q42
            for p in PROPS:
                if p in b:
                    results[qid][p] = b[p]["value"]
                else:
                    # Ensure key exists? Optional — we leave missing ones out, writer fills ""
                    pass

        # Gentle pause to be polite to WDQS
        time.sleep(0.25)

        done = i + len(batch)
        print(f"Processed {done}/{total}")

    write_enriched_csv(in_csv, out_csv, results)
    print(f"Done. Wrote: {out_csv}")

if __name__ == "__main__":
    main()
