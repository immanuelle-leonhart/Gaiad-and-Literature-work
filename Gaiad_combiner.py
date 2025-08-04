#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gaiad_combiner.py – Hard-coded GEDCOM→Mongo with AUTO-MERGE of obvious duplicates.

Hard-coded:
- Mongo URI:        mongodb://localhost:27017
- DB name:          Gaiad_combined
- Dataset A file:   Gaiad.ged
- Dataset B file:   Gaiad_trimmed.ged

What happens when you run it:
1) Wipes previous A/B imports and previous matches.
2) Imports both GEDCOMs into collection `people`.
3) AUTO-MERGES high-confidence duplicates (same normalized name, same birth year,
   and equal death year if both present; unique key).
   - Each merged pair is recorded in `matches` with status='confirmed'.
4) Builds looser suggestions for the leftovers (optional review menu follows).

Dependency:
    pip install pymongo
"""

from __future__ import annotations
import re
import sys
import unicodedata
from datetime import datetime
from collections import defaultdict
from typing import Tuple, Dict, Any, List, Optional
from pymongo import MongoClient
from bson import ObjectId

# ===== HARD-CODED SETTINGS =====
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "Gaiad_combined"
GEDCOM_A = "Gaiad.ged"
GEDCOM_B = "Gaiad_trimmed.ged"

# ===== UTILITIES =====

def norm_text(s: Optional[str]) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    s = re.sub(r"[/,.;:'\"()\[\]{}|]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_year(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
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

# ===== MINIMAL GEDCOM PARSER (INDI/FAM essentials) =====

def parse_gedcom(path: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\n\r") for ln in f]

    rec_type = None
    indi: Dict[str, Dict[str, Any]] = {}
    fams: Dict[str, Dict[str, Any]] = {}
    stack: List[Tuple[int, str]] = []
    cur: Optional[Dict[str, Any]] = None

    def push(level: int, tag: str) -> str:
        nonlocal stack
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent = "/".join([t for _, t in stack])
        full = (parent + "/" if parent else "") + tag
        stack.append((level, tag))
        return full

    def set_field(container: Dict[str, Any], path: str, value: str):
        parts = path.split("/")
        d = container
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = value

    for raw in lines:
        if not raw.strip():
            continue
        m = re.match(r"^(\d+)\s+(.*)$", raw)
        if not m:
            continue
        level = int(m.group(1))
        rest = m.group(2)

        if level == 0:
            stack.clear()
            rec_type = None
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
                    rec_type = tag
                push(0, tag)
            else:
                tag = rest.split()[0]
                push(0, tag)
            continue

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
                cur.setdefault("FAMC", []).append(arg)
            elif tag == "FAMS":
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

    def full_name(p: Dict[str, Any]) -> Optional[str]:
        nm = p.get("NAME")
        if nm:
            g = p.get("GIVN") or ""
            s = p.get("SURN") or ""
            if g or s:
                return (g + " " + s).strip()
            return nm.replace("/", "").strip()
        g = p.get("GIVN") or ""
        s = p.get("SURN") or ""
        out = (g + " " + s).strip()
        return out if out else None

    name_map = {xref: full_name(p) for xref, p in indi.items()}

    for xref, p in indi.items():
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

        spouse_names = set()
        for fam_x in p.get("FAMS", []):
            fam = fams.get(fam_x)
            if not fam:
                continue
            if fam.get("HUSB") == xref and fam.get("WIFE"):
                nm = name_map.get(fam["WIFE"])
                if nm: spouse_names.add(nm)
            elif fam.get("WIFE") == xref and fam.get("HUSB"):
                nm = name_map.get(fam["HUSB"])
                if nm: spouse_names.add(nm)
        if spouse_names:
            p["SPOUSE_NAMES"] = sorted(spouse_names)

    return indi, fams

# ===== MONGO =====

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def ensure_indexes(db):
    db.people.create_index([("dataset", 1)])
    db.people.create_index([("norm.name", 1)])
    db.people.create_index([("birth.year", 1)])
    db.people.create_index([("death.year", 1)])
    db.matches.create_index([("a_id", 1), ("b_id", 1)], unique=True)

# ===== IMPORT =====

def import_gedcom(db, gedcom_path: str, dataset: str) -> int:
    indi, _fams = parse_gedcom(gedcom_path)
    persons = []
    for xref, p in indi.items():
        name = (p.get("GIVN", "") + " " + p.get("SURN", "")).strip()
        if not name:
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
    print(f"Imported {len(persons):,} persons from {gedcom_path} as dataset '{dataset}'")
    return len(persons)

# ===== MERGE HELPERS =====

def get_person_brief(db, _id: ObjectId) -> str:
    p = db.people.find_one({"_id": _id})
    if not p:
        return f"{_id}"
    bits = [f"{_id}", f"[{p.get('dataset')}] {p.get('name') or '(no name)'}"]
    by = p.get("birth", {}).get("year"); dy = p.get("death", {}).get("year")
    dates = []
    if by: dates.append(f"b.{by}")
    if dy: dates.append(f"d.{dy}")
    if dates: bits.append("(" + ", ".join(dates) + ")")
    return " ".join(bits)

def merge_people_noninteractive(db, keep_id: ObjectId, drop_id: ObjectId):
    keep = db.people.find_one({"_id": keep_id})
    drop = db.people.find_one({"_id": drop_id})
    if not keep or not drop:
        return False

    def coalesce(a, b): return a if a not in (None, "", [], {}) else b
    def merge_map(a, b):
        out = dict(a or {})
        for k, v in (b or {}).items():
            if k not in out or out[k] in (None, "", []):
                out[k] = v
        return out

    updates = {}
    for field in ("name", "given", "surname", "sex"):
        updates[field] = coalesce(keep.get(field), drop.get(field))
    updates["birth"] = merge_map(keep.get("birth"), drop.get("birth"))
    updates["death"] = merge_map(keep.get("death"), drop.get("death"))

    kp = keep.get("parents") or {}; dp = drop.get("parents") or {}
    updates["parents"] = {
        "father_name": coalesce(kp.get("father_name"), dp.get("father_name")),
        "mother_name": coalesce(kp.get("mother_name"), dp.get("mother_name")),
    }
    sp_union = sorted(set((keep.get("spouses") or [])) | set((drop.get("spouses") or [])))
    updates["spouses"] = sp_union
    updates["norm"] = {
        "name": norm_text(updates.get("name") or ""),
        "father": norm_text(updates.get("parents", {}).get("father_name") or ""),
        "mother": norm_text(updates.get("parents", {}).get("mother_name") or ""),
        "spouses": [norm_text(s) for s in sp_union],
    }
    updates.setdefault("meta", keep.get("meta", {}))
    updates["meta"]["merged_at"] = datetime.utcnow()
    updates["meta"]["merged_from"] = str(drop_id)

    db.people.update_one({"_id": keep_id}, {"$set": updates})
    db.people.update_one({"_id": drop_id}, {"$set": {
        "meta.deleted": True,
        "meta.deleted_at": datetime.utcnow(),
        "meta.merged_into": str(keep_id)
    }})
    return True

def record_confirmed_match(db, a_id: ObjectId, b_id: ObjectId, score: float, note: str = "automerge"):
    db.matches.update_one(
        {"a_id": a_id, "b_id": b_id},
        {"$set": {
            "a_id": a_id,
            "b_id": b_id,
            "score": score,
            "status": "confirmed",
            "decided_at": datetime.utcnow(),
            "note": note
        }},
        upsert=True
    )

# ===== AUTO-MERGE HIGH-CONFIDENCE =====

def automerge_high_confidence(db) -> int:
    """
    Auto-merge when:
      - SAME normalized name AND SAME birth year
      - and death years match if both present
      - and the key (name,birth_year) maps to exactly ONE B record
    Keep = A, Drop = B
    """
    # Build B index by (norm_name, birth_year)
    b_index: Dict[tuple, list] = defaultdict(list)
    b_meta: Dict[ObjectId, dict] = {}
    for pb in db.people.find({"dataset": "B"}, {"_id": 1, "norm.name": 1, "birth.year": 1, "death.year": 1}):
        key = (pb.get("norm", {}).get("name") or "", pb.get("birth", {}).get("year"))
        b_index[key].append(pb)
        b_meta[pb["_id"]] = pb

    merged = 0
    used_b: set[ObjectId] = set()

    for pa in db.people.find({"dataset": "A"}, {"_id": 1, "norm.name": 1, "birth.year": 1, "death.year": 1}):
        n = pa.get("norm", {}).get("name") or ""
        by = pa.get("birth", {}).get("year")
        dy = pa.get("death", {}).get("year")
        if not n or by is None:
            continue
        candidates = b_index.get((n, by), [])
        if len(candidates) != 1:
            continue  # not unique → skip
        pb = candidates[0]
        b_id = pb["_id"]
        if b_id in used_b:
            continue
        # death-year rule: if both have death years, they must match
        b_dy = pb.get("death", {}).get("year")
        if dy is not None and b_dy is not None and dy != b_dy:
            continue

        a_id = pa["_id"]
        if merge_people_noninteractive(db, a_id, b_id):
            record_confirmed_match(db, a_id, b_id, score=1.0, note="automerge(name+birthYear[+deathYear])")
            used_b.add(b_id)
            merged += 1

    print(f"Auto-merged {merged:,} high-confidence pairs.")
    return merged

# ===== SUGGESTIONS FOR LEFTOVERS (optional) =====

def candidate_pairs(db, dataset_a: str, dataset_b: str, limit_per_key: int = 50):
    b_by_name = defaultdict(list)
    b_by_name_birth = defaultdict(list)
    b_by_name_parent = defaultdict(list)
    b_by_name_spouse = defaultdict(list)

    def key_name(p): return p.get("norm", {}).get("name") or ""
    def key_birth(p): return p.get("birth", {}).get("year")

    for pb in db.people.find({"dataset": dataset_b, "meta.deleted": {"$ne": True}},
                             {"_id": 1, "norm": 1, "birth.year": 1, "parents": 1, "spouses": 1}):
        n = key_name(pb); y = key_birth(pb)
        if n:
            b_by_name[n].append(pb)
            if y:
                b_by_name_birth[(n, y)].append(pb)
            mf = pb.get("norm", {}).get("father", "")
            mm = pb.get("norm", {}).get("mother", "")
            if mf: b_by_name_parent[(n, mf)].append(pb)
            if mm: b_by_name_parent[(n, mm)].append(pb)
            for sp in pb.get("norm", {}).get("spouses", []):
                b_by_name_spouse[(n, sp)].append(pb)

    for pa in db.people.find({"dataset": dataset_a, "meta.deleted": {"$ne": True}},
                             {"_id": 1, "norm": 1, "birth.year": 1, "parents": 1, "spouses": 1}):
        a_id = pa["_id"]
        n = key_name(pa)
        if not n:
            continue
        y = key_birth(pa)
        a_keys = []
        if y: a_keys.append(("name_birth", (n, y)))
        mf = pa.get("norm", {}).get("father", "")
        mm = pa.get("norm", {}).get("mother", "")
        if mf: a_keys.append(("name_parent", (n, mf)))
        if mm: a_keys.append(("name_parent", (n, mm)))
        for sp in pa.get("norm", {}).get("spouses", []):
            a_keys.append(("name_spouse", (n, sp)))
        a_keys.append(("name_only", n))

        seen_b = set()
        for kind, k in a_keys:
            if kind == "name_birth":
                cands = b_by_name_birth.get(k, [])[:limit_per_key]; score = 0.95
            elif kind == "name_parent":
                cands = b_by_name_parent.get(k, [])[:limit_per_key]; score = 0.9
            elif kind == "name_spouse":
                cands = b_by_name_spouse.get(k, [])[:limit_per_key]; score = 0.85
            else:
                cands = b_by_name.get(k, [])[:limit_per_key]; score = 0.6
            for pb in cands:
                b_id = pb["_id"]
                if b_id in seen_b:
                    continue
                seen_b.add(b_id)
                yield a_id, b_id, score

def suggest_matches(db, dataset_a: str, dataset_b: str):
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
            pass
    print(f"Suggested up to {created:,} leftover candidates (status='suggested').")

# ===== OPTIONAL REVIEW / UNIQUES / PRUNE / MERGE MENU =====

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
            if merge_people_noninteractive(db, a_id, b_id):
                db.matches.update_one({"_id": m["_id"]},
                                      {"$set": {"status": "confirmed", "decided_at": datetime.utcnow(), "note": "manual_confirm_and_merge"}})
                print("✔ merged+confirmed")
        elif ans == "r":
            db.matches.update_one({"_id": m["_id"]}, {"$set": {"status": "rejected", "decided_at": datetime.utcnow()}})
            print("✘ rejected")
        elif ans == "q":
            break
        else:
            print("…skipped")

def list_uniques(db, dataset: str, limit: int = 50):
    matched_ids = set()
    for m in db.matches.find({"status": "confirmed"}, {"a_id": 1, "b_id": 1}):
        matched_ids.add(m["a_id"]); matched_ids.add(m["b_id"])
    q = {"dataset": dataset, "_id": {"$nin": list(matched_ids)}, "meta.deleted": {"$ne": True}}
    total = db.people.count_documents(q)
    print(f"\n{total:,} uniques in dataset '{dataset}' (showing up to {limit}):")
    for p in db.people.find(q).limit(limit):
        print(" -", get_person_brief(db, p["_id"]))

def prune_uniques(db, dataset: str):
    matched_ids = set()
    for m in db.matches.find({"status": "confirmed"}, {"a_id": 1, "b_id": 1}):
        matched_ids.add(m["a_id"]); matched_ids.add(m["b_id"])
    q = {"dataset": dataset, "_id": {"$nin": list(matched_ids)}, "meta.deleted": {"$ne": True}}
    total = db.people.count_documents(q)
    print(f"\n{total:,} uniques in dataset '{dataset}'.")
    if total == 0:
        return
    if not ask_yes_no("Proceed to review and optionally DELETE these uniques?", default_no=False):
        return

    deleted = 0
    for p in db.people.find(q):
        print("\nUnique candidate:", get_person_brief(db, p["_id"]))
        if ask_yes_no("Delete this person?", default_no=True):
            db.people.delete_one({"_id": p["_id"]})
            deleted += 1
            print("…deleted")
        else:
            print("…kept")
    print(f"Done. Deleted {deleted} records.")

def menu(db):
    while True:
        print("\n=== GIAD Combined – Edge-case Menu ===")
        print("[1] Review leftover suggested matches (optional)")
        print("[2] List uniques in A")
        print("[3] List uniques in B")
        print("[4] Prune uniques in A (with confirmation)")
        print("[5] Prune uniques in B (with confirmation)")
        print("[Q] Quit")
        choice = input("> ").strip().lower()
        if choice == "1": review_matches(db)
        elif choice == "2": list_uniques(db, "A", limit=100)
        elif choice == "3": list_uniques(db, "B", limit=100)
        elif choice == "4": prune_uniques(db, "A")
        elif choice == "5": prune_uniques(db, "B")
        elif choice == "q": break
        else: print("Unknown option.")

# ===== MAIN =====

def main():
    db = get_db()
    ensure_indexes(db)

    # Fresh run
    db.people.delete_many({"dataset": {"$in": ["A", "B"]}})
    db.matches.delete_many({})
    print("Cleared previous A/B imports and matches.")

    # Import
    import_gedcom(db, GEDCOM_A, "A")
    import_gedcom(db, GEDCOM_B, "B")

    # AUTO-MERGE obvious duplicates
    automerge_high_confidence(db)

    # For leftovers, create suggestions (weaker rules) – optional to review
    suggest_matches(db, "A", "B")

    # Optional edge-case menu (or just quit)
    menu(db)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
