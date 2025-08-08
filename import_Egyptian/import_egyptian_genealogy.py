#!/usr/bin/env python3
"""
import_egyptian_genealogy.py
----------------------------
Crawl Wikidata starting at Pharaoh Khufu (Q161904), following:

  Father   P22
  Mother   P25
  Sibling  P3373
  Spouse   P26
  Child    P40

Each unique person encountered is stored in MongoDB:
    database = egyptian_genealogy
    collection = persons
"""

from __future__ import annotations
import requests, time, sys
from typing import Dict, List, Set
from pymongo import MongoClient, ASCENDING

# ─── CONFIG ───────────────────────────────────────────────────────────────────
START_QID           = "Q161904"         # Pharaoh Khufu
REL_PROPS           = ["P22", "P25", "P3373", "P26", "P40"]
ENTITY_API          = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
LABEL_API           = "https://www.wikidata.org/w/api.php"
HEADERS             = {"User-Agent": "EgyptianGenealogyImporter/1.0"}
REQUEST_TIMEOUT     = 60
LABEL_CHUNK         = 50
RESOLVE_PROPS       = ["P31", "P279"] + REL_PROPS   # include relations for labels
MONGO_URI           = "mongodb://127.0.0.1:27017"
DB_NAME             = "egyptian_genealogy"
COLL_NAME           = "persons"

# ─── WIKIDATA HELPERS ─────────────────────────────────────────────────────────
def fetch_entity(qid: str) -> Dict:
    r = requests.get(ENTITY_API.format(qid), headers=HEADERS, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()["entities"][qid]

def fetch_labels(qids: List[str], lang="en") -> Dict[str, str]:
    out: Dict[str, str] = {}
    for i in range(0, len(qids), LABEL_CHUNK):
        chunk = qids[i:i+LABEL_CHUNK]
        r = requests.get(LABEL_API, params={
            "action": "wbgetentities",
            "ids": "|".join(chunk),
            "props": "labels",
            "languages": lang,
            "format": "json"
        }, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        data = r.json().get("entities", {})
        for q in data:
            lbl = data[q].get("labels", {}).get(lang, {}).get("value")
            if lbl:
                out[q] = lbl
    return out

# ─── DOCUMENT BUILDER ─────────────────────────────────────────────────────────
def build_doc(qid: str, ent: Dict) -> Dict:
    claims = ent.get("claims", {})
    def qids(prop):
        return [s["mainsnak"]["datavalue"]["value"]["id"]
                for s in claims.get(prop, [])
                if s["mainsnak"].get("datavalue")]

    ids_to_resolve = {q for p in RESOLVE_PROPS for q in qids(p)}
    label_map      = fetch_labels(list(ids_to_resolve))

    claims_resolved = {
        p: [{"id": q, "label": label_map.get(q, "")} for q in qids(p)]
        for p in RESOLVE_PROPS
    }

    return {
        "wikidata_id":  qid,
        "wikidata_raw": ent,
        "extracted": {
            "labels":       ent.get("labels", {}),
            "descriptions": ent.get("descriptions", {}),
            "claims":       claims,
            "claims_resolved": claims_resolved,
        }
    }

# ─── MONGO SETUP ──────────────────────────────────────────────────────────────
client = MongoClient(MONGO_URI)
coll   = client[DB_NAME][COLL_NAME]
coll.create_index([("wikidata_id", ASCENDING)], unique=True)

# ─── BFS CRAWL ────────────────────────────────────────────────────────────────
queue: List[str] = [START_QID]
seen : Set[str]  = set()

while queue:
    qid = queue.pop(0)
    if qid in seen:
        continue
    seen.add(qid)

    try:
        print(f"[{len(seen):>4}] {qid}")
        ent = fetch_entity(qid)
        doc = build_doc(qid, ent)
        coll.replace_one({"wikidata_id": qid}, doc, upsert=True)
    except Exception as e:
        print("   ⚠", qid, e)
        continue

    # enqueue relatives
    for prop in REL_PROPS:
        for snk in ent.get("claims", {}).get(prop, []):
            tgt = snk["mainsnak"].get("datavalue", {}).get("value", {})
            if isinstance(tgt, dict) and tgt.get("id"):
                queue.append(tgt["id"])

    time.sleep(0.2)   # politeness pause

print("✅  Finished. Persons stored:", coll.count_documents({}))
