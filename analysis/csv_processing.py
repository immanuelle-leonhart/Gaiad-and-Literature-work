import csv
import requests

INPUT_FILE = "geni_ids_no_wikidata.csv"
OUTPUT_FILE = "geni_ids_with_wikidata.csv"

# 1. Query Wikidata for all P2600 values
url = "https://query.wikidata.org/sparql"
query = """
SELECT ?item ?geni WHERE {
  ?item wdt:P2600 ?geni.
}
"""
headers = {"Accept": "application/sparql-results+json"}
resp = requests.get(url, params={"query": query}, headers=headers)
resp.raise_for_status()
results = resp.json()["results"]["bindings"]

# 2. Build mapping: geni_id -> QID
geni_to_qid = {
    r["geni"]["value"]: r["item"]["value"].split("/")[-1]
    for r in results
}

print(f"Loaded {len(geni_to_qid)} GENI→QID mappings from Wikidata")

# 3. Process CSV
with open(INPUT_FILE, newline="", encoding="utf-8") as infile, \
     open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    for row in reader:
        if len(row) < 2:
            continue
        local_qid, geni_id = row[0], row[1]
        wikidata_qid = geni_to_qid.get(geni_id, "")
        writer.writerow([local_qid, geni_id, wikidata_qid])

print(f"Done. Output written to {OUTPUT_FILE}")
