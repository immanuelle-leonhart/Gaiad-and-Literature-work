#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gaiad_combiner.py
Gaiad_combined – GEDCOM→MongoDB importer & comparer

Features:
- import:    Parse GEDCOM and load persons/families into MongoDB (tagged by dataset label).
- suggest:   Compute cross-dataset match suggestions (A<->B) with simple heuristics.
- review:    Interactive review of suggestions (confirm/reject).
- uniques:   List people present only in one dataset (i.e., no confirmed match).
- prune:     Interactively delete uniques from a dataset (with confirmation).
- merge:     Merge any two person docs (combine fields; keep one; soft-delete the other).

Collections (in DB):
- people: one document per person record imported (fields include dataset, xref, names, events).
- families: family stubs (optional for future use).
- matches: cross-dataset match suggestions and decisions (status=suggested|confirmed|rejected).

Default DB name: "Gaiad_combined"
"""

import argparse
import re
import sys
import unicodedata
from datetime import datetime
from collections import defaultdict
from pymongo import MongoClient
from bson import ObjectId

# ----------------------------
# Utilities
# ----------------------------

def norm_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    s = re.sub(r"[/,.;:'\"()\[\]{}|]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_year(date_str: str) -> int | None:
    if not date_str:
        return None
    # Accept formats like "1 JAN 1900", "ABT 1900", "1900", "BET 1899 AND 1901"
    m = re.search(r"(\d{4})", date_str)
    if m:
        y = int(m.group(1))
        if 1000 <= y <= 2100:
            return y
    return None

def ask_yes_no(prompt: str, default_no: bool = True) -> bool:
    suffix = "[y/N] " if default_no else "[Y/n] "
    ans = input(prompt + " " + suffix).strip().lower()
    if not ans:
        return not default_no
    return ans in ("y", "yes")

# ----------------------------
# Minimal GEDCOM parser (INDI & FAM essentials)
# ----------------------------

def parse_gedcom(path: str) -> tuple[dict, dict]:
    """
    Returns (individuals, families)
    individuals: {xref: {fields...}}
    families:    {xref: {fields...}}
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\n\r") for ln in f]

    rec_type = None
    rec_xref = None
    indi = {}
    fams = {}
    stack = []  # (level, tag_path)

    # Temporary holders during INDI/FAM parsing
    cur = None

    def push(level, tag):
        nonlocal stack
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent = "/".join([t for _, t in stack])
        full = (parent + "/" if parent else "") + tag
        stack.append((level, tag))
        return full

    # Helpers to set nested fields
    def set_field(container: dict, path: str, value: str):
        # path like: "BIRT/DATE"
        parts = path.split("/")
        d = container
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = value

    # First pass: collect basic fields from INDI & FAM
    for raw in lines:
        if not raw.strip():
            continue
        m = re.match(r"^(\d+)\s+(.*)$", raw)
        if not m:
            continue
        level = int(m.group(1))
        rest = m.group(2)

        # Record headers: "0 @I1@ INDI" or "0 @F1@ FAM" or "0 TRLR"
        if level == 0:
            stack.clear()
            rec_type = None
            rec_xref = None
            cur = None

            m2 = re.match(r"^(@[^@]+@)\s+(\w+)$", rest)
            if m2:
                rec_xref, tag = m2.group(1), m2.group(2)
                if tag == "INDI":
                    rec_type = "INDI"
                    cur = indi.setdefault(rec_xref, {"_type": "INDI", "_xref": rec_xref})
                elif tag == "FAM":
                    rec_type = "FAM"
                    cur = fams.setdefault(rec_xref, {"_type": "FAM", "_xref": rec_xref})
                else:
                    rec_type = tag  # ignore others
                push(0, tag)
            else:
                # e.g., "0 TRLR" or "0 HEAD"
                tag = rest.split()[0]
                push(0, tag)
            continue

        # For non-zero levels
        parts = rest.split(None, 1)
        tag = parts[0]
        arg = parts[1] if len(parts) > 1 else ""
        full = push(level, tag)

        if rec_type == "INDI" and cur is not None:
            if tag in ("NAME", "SEX"):
                set_field(cur, tag, arg)
            elif tag in ("GIVN", "SURN"):
                set_field(cur, tag, arg)
            elif full.endswith("BIRT/DATE"):
                set_field(cur, "BIRT/DATE", arg)
            elif full.endswith("BIRT/PLAC"):
                set_field(cur, "BIRT/PLAC", arg)
            elif full.endswith("DEAT/DATE"):
                set_field(cur, "DEAT/DATE", arg)
            elif full.endswith("DEAT/PLAC"):
                set_field(cur, "DEAT/PLAC", arg)
            elif tag == "FAMC":
                # child in family
                cur.setdefault("FAMC", []).append(arg)
            elif tag == "FAMS":
                # spouse in family
                cur.setdefault("FAMS", []).append(arg)

        elif rec_type == "FAM" and cur is not None:
            if tag in ("HUSB", "WIFE"):
                set_field(cur, tag, arg)
            elif tag == "CHIL":
                cur.setdefault("CHIL", []).append(arg)
            elif full.endswith("MARR/DATE"):
                set_field(cur, "MARR/DATE", arg)
            elif full.endswith("MARR/PLAC"):
                set_field(cur, "MARR/PLAC", arg)

    # Second pass: compute useful derived fields for people (parent/spouse names)
    # Build helper maps
    def full_name(person):
        nm = person.get("NAME")
        if nm:
            # GEDCOM NAME often "Given /Surname/"
            g = person.get("GIVN") or ""
            s = person.get("SURN") or ""
            if g or s:
                return (g + " " + s).strip()
            # fallback: remove slashes
            return nm.replace("/", "").strip()
        g = person.get("GIVN") or ""
        s = person.get("SURN") or ""
        return (g + " " + s).strip() or None

    name_map = {xref: full_name(p) for xref, p in indi.items()}

    for xref, p in indi.items():
        # Parents via FAMC
        father_name = mother_name = None
        for fam_x in p.get("FAMC", []):
            fam = fams.get(fam_x)
            if not fam:
                continue
            if fam.get("HUSB"):
                father_name = name_map.get(fam.get("HUSB")) or father_name
            if fam.get("WIFE"):
                mother_name = name_map.get(fam.get("WIFE")) or mother_name
        if father_name:
            p["FATHER_NAME"] = father_name
        if mother_name:
            p["MOTHER_NAME"] = mother_name

        # Spouses via FAMS
        spouse_names = set()
        for fam_x in p.get("FAMS", []):
            fam = fams.get(fam_x)
            if not fam:
                continue
            # If this person is HUSB, spouse=WIFE; vice versa
            if fam.get("HUSB") == xref and fam.get("WIFE"):
                nm = name_map.get(fam["WIFE"])
                if nm:
                    spouse_names.add(nm)
            elif fam.get("WIFE") == xref and fam.get("HUSB"):
                nm = name_map.get(fam["HUSB"])
                if nm:
                    spouse_names.add(nm)
        if spouse_names:
            p["SPOUSE_NAMES"] = sorted(spouse_names)

    return indi, fams

# ----------------------------
# Mongo helpers
# ----------------------------

def get_db(mongo_uri: str, db_name: str):
    client = MongoClient(mongo_uri)
    return client[db_name]

def ensure_indexes(db):
    db.people.create_index([("dataset", 1)])
    db.people.create_index([("norm.name", 1)])
    db.people.create_index([("birth.year", 1)])
    db.people.create_index([("death.year", 1)])
    db.matches.create_index([("a_id", 1), ("b_id", 1)], unique=True)

# ----------------------------
# Import
# ----------------------------

def import_gedcom(db, gedcom_path: str, dataset: str):
    indi, fams = parse_gedcom(gedcom_path)
    persons = []
    for xref, p in indi.items():
        name = (p.get("GIVN", "") + " " + p.get("SURN", "")).strip()
        if not name:
            # fallback
            nm = p.get("NAME")
            if nm:
                name = nm.replace("/", "").strip()
        birth_date = p.get("BIRT", {}).get("DATE")
        death_date = p.get("DEAT", {}).get("DATE")
        doc = {
            "dataset": dataset,
            "xref": xref,
            "name": name or None,
            "given": p.get("GIVN"),
            "surname": p.get("SURN"),
            "sex": p.get("SEX"),
            "birth": {
                "date": birth_date,
                "year": extract_year(birth_date),
                "place": p.get("BIRT", {}).get("PLAC"),
            },
            "death": {
                "date": death_date,
                "year": extract_year(death_date),
                "place": p.get("DEAT", {}).get("PLAC"),
            },
            "parents": {
                "father_name": p.get("FATHER_NAME"),
                "mother_name": p.get("MOTHER_NAME"),
            },
            "spouses": p.get("SPOUSE_NAMES", []),
            "norm": {
                "name": norm_text(name or ""),
                "father": norm_text(p.get("FATHER_NAME", "")),
                "mother": norm_text(p.get("MOTHER_NAME", "")),
                "spouses": [norm_text(s) for s in p.get("SPOUSE_NAMES", [])],
            },
            "meta": {
                "imported_at": datetime.utcnow(),
                "source_path": gedcom_path,
            },
        }
        persons.append(doc)

    if persons:
        db.people.insert_many(persons)
    print(f"Imported {len(persons)} persons from {gedcom_path} as dataset '{dataset}'")
    # families are parsed but not stored by default
    return len(persons)

# ----------------------------
# Matching heuristics
# ----------------------------

def candidate_pairs(db, dataset_a: str, dataset_b: str, limit_per_key: int = 50):
    """
    Yield potential A<->B pairs with simple keys:
    - (name, birth_year)
    - (name, parent name)
    - (name, spouse name)
    - (name only) [weak]
    """
    # Build inverted indexes in-memory for B to speed simple suggestions
    b_by_name = defaultdict(list)
    b_by_name_birth = defaultdict(list)
    b_by_name_parent = defaultdict(list)   # mother/father
    b_by_name_spouse = defaultdict(list)

    def key_name(p):
        return p.get("norm", {}).get("name") or ""

    def key_birth(p):
        return p.get("birth", {}).get("year")

    for pb in db.people.find({"dataset": dataset_b}, {"_id": 1, "norm": 1, "birth.year": 1, "parents": 1, "spouses": 1}):
        n = key_name(pb)
        y = key_birth(pb)
        if n:
            b_by_name[n].append(pb)
            if y:
                b_by_name_birth[(n, y)].append(pb)
            # parents
            mf = pb.get("norm", {}).get("father", "")
            mm = pb.get("norm", {}).get("mother", "")
            if mf:
                b_by_name_parent[(n, mf)].append(pb)
            if mm:
                b_by_name_parent[(n, mm)].append(pb)
            # spouses
            for sp in pb.get("norm", {}).get("spouses", []):
                b_by_name_spouse[(n, sp)].append(pb)

    # Walk A and produce suggestions
    for pa in db.people.find({"dataset": dataset_a}, {"_id": 1, "name": 1, "norm": 1, "birth.year": 1, "parents": 1, "spouses": 1}):
        a_id = pa["_id"]
        n = key_name(pa)
        if not n:
            continue
        y = key_birth(pa)
        a_keys = []

        if y:
            a_keys.append(("name_birth", (n, y)))
        mf = pa.get("norm", {}).get("father", "")
        mm = pa.get("norm", {}).get("mother", "")
        if mf:
            a_keys.append(("name_parent", (n, mf)))
        if mm:
            a_keys.append(("name_parent", (n, mm)))
        for sp in pa.get("norm", {}).get("spouses", []):
            a_keys.append(("name_spouse", (n, sp)))
        # weakest last
        a_keys.append(("name_only", n))

        seen_b = set()
        for kind, k in a_keys:
            if kind == "name_birth":
                cands = b_by_name_birth.get(k, [])[:limit_per_key]
                score = 1.0
            elif kind == "name_parent":
                cands = b_by_name_parent.get(k, [])[:limit_per_key]
                score = 0.9
            elif kind == "name_spouse":
                cands = b_by_name_spouse.get(k, [])[:limit_per_key]
                score = 0.85
            else:
                cands = b_by_name.get(k, [])[:limit_per_key]
                score = 0.6
            for pb in cands:
                b_id = pb["_id"]
                if b_id in seen_b:
                    continue
                seen_b.add(b_id)
                yield a_id, b_id, score

def suggest_matches(db, dataset_a: str, dataset_b: str, overwrite: bool):
    created = 0
    for a_id, b_id, score in candidate_pairs(db, dataset_a, dataset_b):
        try:
            db.matches.update_one(
                {"a_id": a_id, "b_id": b_id},
                {"$setOnInsert": {
                    "a_id": a_id,
                    "b_id": b_id,
                    "score": score,
                    "status": "suggested",
                    "created_at": datetime.utcnow(),
                }},
                upsert=True,
            )
            created += 1
        except Exception:
            # ignore duplicates
            pass
    print(f"Suggested up to {created} A↔B pairs (status='suggested').")

# ----------------------------
# Interactive review
# ----------------------------

def get_person_brief(db, _id: ObjectId) -> str:
    p = db.people.find_one({"_id": _id})
    if not p:
        return f"{_id}"
    bits = [
        f"{_id}",
        f"[{p.get('dataset')}] {p.get('name') or '(no name)'}",
    ]
    by = p.get("birth", {}).get("year")
    dy = p.get("death", {}).get("year")
    dates = []
    if by: dates.append(f"b.{by}")
    if dy: dates.append(f"d.{dy}")
    if dates:
        bits.append("(" + ", ".join(dates) + ")")
    return " ".join(bits)

def review_matches(db):
    cur = db.matches.find({"status": "suggested"}).sort("score", -1)
    for m in cur:
        a_id = m["a_id"]; b_id = m["b_id"]
        print("\nCandidate match:")
        print("A:", get_person_brief(db, a_id))
        print("B:", get_person_brief(db, b_id))
        print(f"Score: {m.get('score')}")
        ans = input("[c]onfirm / [r]eject / [s]kip / [q]uit: ").strip().lower()
        if ans == "c":
            db.matches.update_one({"_id": m["_id"]}, {"$set": {"status": "confirmed", "decided_at": datetime.utcnow()}})
            print("✔ confirmed")
        elif ans == "r":
            db.matches.update_one({"_id": m["_id"]}, {"$set": {"status": "rejected", "decided_at": datetime.utcnow()}})
            print("✘ rejected")
        elif ans == "q":
            break
        else:
            print("…skipped")

# ----------------------------
# Uniques (present only in one dataset, with no confirmed match)
# ----------------------------

def list_uniques(db, dataset: str, limit: int):
    matched_ids = set()
    for m in db.matches.find({"status": "confirmed"}, {"a_id": 1, "b_id": 1}):
        matched_ids.add(m["a_id"])
        matched_ids.add(m["b_id"])
    q = {"dataset": dataset, "_id": {"$nin": list(matched_ids)}}
    cur = db.people.find(q).limit(limit)
    count = db.people.count_documents(q)
    print(f"{count} uniques in dataset '{dataset}' (showing up to {limit}):")
    for p in cur:
        print(" -", get_person_brief(db, p["_id"]))

def prune_uniques(db, dataset: str):
    matched_ids = set()
    for m in db.matches.find({"status": "confirmed"}, {"a_id": 1, "b_id": 1}):
        matched_ids.add(m["a_id"])
        matched_ids.add(m["b_id"])
    q = {"dataset": dataset, "_id": {"$nin": list(matched_ids)}}
    total = db.people.count_documents(q)
    print(f"{total} uniques in dataset '{dataset}'.")
    if total == 0:
        return
    if not ask_yes_no("Proceed to review and optionally delete uniques?", default_no=False):
        return

    cur = db.people.find(q)
    deleted = 0
    for p in cur:
        print("\nUnique candidate:", get_person_brief(db, p["_id"]))
        if ask_yes_no("Delete this person?", default_no=True):
            db.people.delete_one({"_id": p["_id"]})
            deleted += 1
            print("…deleted")
        else:
            print("…kept")
    print(f"Done. Deleted {deleted} records.")

# ----------------------------
# Merge (any two people)
# ----------------------------

def merge_people(db, keep_id: str, drop_id: str):
    k_id = ObjectId(keep_id)
    d_id = ObjectId(drop_id)
    keep = db.people.find_one({"_id": k_id})
    drop = db.people.find_one({"_id": d_id})
    if not keep or not drop:
        print("One or both IDs not found.")
        return
    print("Keep:", get_person_brief(db, k_id))
    print("Drop:", get_person_brief(db, d_id))
    if not ask_yes_no("Merge DROP into KEEP (KEEP wins on conflicts)?", default_no=False):
        return

    # Combine conservatively: keep existing values; fill missing from drop; union lists
    def coalesce(a, b):
        return a if a not in (None, "", [], {}) else b

    def merge_events(a, b):
        out = dict(a or {})
        for k, v in (b or {}).items():
            if k not in out or out[k] in (None, "", []):
                out[k] = v
        return out

    updates = {}
    for field in ("name", "given", "surname", "sex"):
        updates[field] = coalesce(keep.get(field), drop.get(field))
    updates["birth"] = merge_events(keep.get("birth"), drop.get("birth"))
    updates["death"] = merge_events(keep.get("death"), drop.get("death"))

    # parents
    kp = keep.get("parents") or {}
    dp = drop.get("parents") or {}
    updates["parents"] = {
        "father_name": coalesce(kp.get("father_name"), dp.get("father_name")),
        "mother_name": coalesce(kp.get("mother_name"), dp.get("mother_name")),
    }

    # spouses as union
    sp_union = sorted(set((keep.get("spouses") or [])) | set((drop.get("spouses") or [])))
    updates["spouses"] = sp_union

    # recompute normalization
    updates["norm"] = {
        "name": norm_text(updates.get("name") or ""),
        "father": norm_text(updates.get("parents", {}).get("father_name") or ""),
        "mother": norm_text(updates.get("parents", {}).get("mother_name") or ""),
        "spouses": [norm_text(s) for s in sp_union],
    }

    # mark merged
    updates.setdefault("meta", keep.get("meta", {}))
    updates["meta"]["merged_at"] = datetime.utcnow()
    updates["meta"]["merged_from"] = str(d_id)

    db.people.update_one({"_id": k_id}, {"$set": updates})
    # soft-delete dropped record (keep a tombstone)
    db.people.update_one({"_id": d_id}, {"$set": {"meta.deleted": True, "meta.deleted_at": datetime.utcnow(), "meta.merged_into": str(k_id)}})
    # update matches referencing d_id to point to k_id where sensible (simple version: mark invalid)
    db.matches.update_many(
        {"$or": [{"a_id": d_id}, {"b_id": d_id}]},
        {"$set": {"status": "invalid", "decided_at": datetime.utcnow(), "note": f"record {d_id} merged into {k_id}"}}
    )
    print("Merged successfully.")

# ----------------------------
# Main
# ----------------------------

def main():
    ap = argparse.ArgumentParser(description="Gaiad_combined – GEDCOM to MongoDB and comparer")
    ap.add_argument("--mongo", default="mongodb://localhost:27017", help="MongoDB URI")
    ap.add_argument("--db", default="Gaiad_combined", help="MongoDB database name")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp_imp = sub.add_parser("import", help="Import a GEDCOM file")
    sp_imp.add_argument("--dataset", required=True, help="Dataset label (e.g., A, B)")
    sp_imp.add_argument("--gedcom", required=True, help="Path to GEDCOM file")

    sp_sug = sub.add_parser("suggest", help="Suggest cross-dataset matches")
    sp_sug.add_argument("--a", required=True, help="Dataset A label")
    sp_sug.add_argument("--b", required=True, help="Dataset B label")
    sp_sug.add_argument("--overwrite", action="store_true", help="(kept for future use)")

    sp_rev = sub.add_parser("review", help="Review suggested matches interactively")

    sp_uni = sub.add_parser("uniques", help="List uniques in a dataset (no confirmed match)")
    sp_uni.add_argument("--dataset", required=True)
    sp_uni.add_argument("--limit", type=int, default=50)

    sp_pru = sub.add_parser("prune", help="Interactively delete uniques in a dataset")
    sp_pru.add_argument("--dataset", required=True)

    sp_mrg = sub.add_parser("merge", help="Merge two people (drop→keep)")
    sp_mrg.add_argument("--keep", required=True, help="ObjectId to keep")
    sp_mrg.add_argument("--drop", required=True, help="ObjectId to drop")

    args = ap.parse_args()
    db = get_db(args.mongo, args.db)
    ensure_indexes(db)

    if args.cmd == "import":
        import_gedcom(db, args.gedcom, args.dataset)

    elif args.cmd == "suggest":
        suggest_matches(db, args.a, args.b, args.overwrite)

    elif args.cmd == "review":
        review_matches(db)

    elif args.cmd == "uniques":
        list_uniques(db, args.dataset, args.limit)

    elif args.cmd == "prune":
        prune_uniques(db, args.dataset)

    elif args.cmd == "merge":
        merge_people(db, args.keep, args.drop)

if __name__ == "__main__":
    main()
