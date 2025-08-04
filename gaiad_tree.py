#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gaiad_tree.py — GEDCOM ⇄ Mongo pipeline for one tree

Hard-coded:
- Mongo URI: mongodb://localhost:27017
- DB name:   Gaiad_tree
- GEDCOM in: Gaiad.ged

Commands:
  import                      Parse Gaiad.ged → DB (indi,fam)
  find-dupes                  List likely duplicate groups (by name+birth year)
  automerge-strict            Auto-merge only unambiguous identicals (safe)
  prune-unrelated --keep-largest
                              Keep only the largest connected component
  clean-placeholders          Remove SURN == "Placeholder surname"
  export --out merged.ged     Write a clean, renumbered GEDCOM

Notes
- Bidirectional integrity: merges and pruning update both INDI↔FAM.
- “Strict duplicate” = same normalized NAME + same birth year, and if both
  have death years they must match; and the key maps to a unique pair.
- A future `geni_id` field per person is included (unused here).
"""

from __future__ import annotations
import argparse
import re
import sys
import unicodedata
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, Any, List, Tuple, Optional, Set
from pymongo import MongoClient
from bson import ObjectId

MONGO_URI = "mongodb://localhost:27017"
DB_NAME   = "Gaiad_tree"
GEDCOM_IN = "Gaiad.ged"

# --------------- utils ---------------

def norm_text(s: Optional[str]) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_year(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    m = re.search(r"(\d{4})", date_str)
    if not m:
        return None
    y = int(m.group(1))
    return y if 1000 <= y <= 2100 else None

def get_db():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]

def ensure_indexes(db):
    db.indi.create_index([("xref", 1)], unique=True)
    db.indi.create_index([("norm_name", 1)])
    db.indi.create_index([("birth.year", 1)])
    db.indi.create_index([("death.year", 1)])
    db.fam.create_index([("xref", 1)], unique=True)
    db.matches.create_index([("a", 1), ("b", 1)], unique=True)

def full_name(givn: Optional[str], surn: Optional[str], raw_name: Optional[str]) -> Optional[str]:
    givn = (givn or "").strip()
    surn = (surn or "").strip()
    if givn or surn:
        return f"{givn} {surn}".strip()
    if raw_name:
        return raw_name.replace("/", "").strip()
    return None

# --------------- GEDCOM parse ---------------

def parse_gedcom(path: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]], Dict[str, Any]]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\r\n") for ln in f]

    records: List[List[str]] = []
    cur: List[str] = []
    for ln in lines:
        if ln.startswith("0 "):
            if cur:
                records.append(cur)
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        records.append(cur)

    indi: Dict[str, Dict[str, Any]] = {}
    fam:  Dict[str, Dict[str, Any]] = {}
    head: Dict[str, Any] = {"lines": []}
    trlr: Dict[str, Any] = {"lines": []}

    def get_tag_arg(s: str) -> Tuple[int, str, str]:
        # returns (level, tag, arg)
        m = re.match(r"^(\d+)\s+(@[^@]+@)?\s*([A-Z0-9_]+)?\s*(.*)$", s)
        if not m:
            return 0, "", ""
        lvl = int(m.group(1))
        if m.group(2) and m.group(3):
            # "0 @I1@ INDI"
            return lvl, m.group(3), m.group(2)
        tag = m.group(3) or ""
        arg = m.group(4) or ""
        return lvl, tag, arg

    for rec in records:
        lvl0, tag0, arg0 = get_tag_arg(rec[0])
        if tag0 == "INDI":
            xref = arg0
            data = {"_type": "INDI", "xref": xref, "lines": rec, "FAMC": [], "FAMS": [], "other": []}
            givn = surn = raw_name = sex = None
            birth_date = birth_plac = death_date = death_plac = None
            path = []
            for ln in rec[1:]:
                lvl, tag, arg = get_tag_arg(ln)
                while path and path[-1][0] >= lvl:
                    path.pop()
                path.append((lvl, tag))
                if tag == "NAME": raw_name = arg
                elif tag == "GIVN": givn = arg
                elif tag == "SURN": surn = arg
                elif tag == "SEX": sex = arg
                elif tag == "FAMC": data["FAMC"].append(arg)
                elif tag == "FAMS": data["FAMS"].append(arg)
                elif "/".join(t for _, t in path) == "BIRT/DATE": birth_date = arg
                elif "/".join(t for _, t in path) == "BIRT/PLAC": birth_plac = arg
                elif "/".join(t for _, t in path) == "DEAT/DATE": death_date = arg
                elif "/".join(t for _, t in path) == "DEAT/PLAC": death_plac = arg
            nm = full_name(givn, surn, raw_name)
            data.update({
                "name": nm,
                "given": givn,
                "surname": surn,
                "sex": sex,
                "birth": {"date": birth_date, "year": extract_year(birth_date), "place": birth_plac},
                "death": {"date": death_date, "year": extract_year(death_date), "place": death_plac},
                "norm_name": norm_text(nm),
                "geni_id": None,  # reserved for later
            })
            indi[xref] = data

        elif tag0 == "FAM":
            xref = arg0
            data = {"_type": "FAM", "xref": xref, "lines": rec, "HUSB": None, "WIFE": None, "CHIL": [], "MARR": {}}
            path = []
            for ln in rec[1:]:
                lvl, tag, arg = get_tag_arg(ln)
                while path and path[-1][0] >= lvl:
                    path.pop()
                path.append((lvl, tag))
                if tag in ("HUSB", "WIFE"):
                    data[tag] = arg
                elif tag == "CHIL":
                    data["CHIL"].append(arg)
                elif "/".join(t for _, t in path) == "MARR/DATE":
                    data["MARR"]["date"] = arg
                elif "/".join(t for _, t in path) == "MARR/PLAC":
                    data["MARR"]["place"] = arg
            fam[xref] = data

        elif tag0 == "HEAD":
            head["lines"] = rec
        elif tag0 == "TRLR":
            trlr["lines"] = rec

    return indi, fam, {"HEAD": head, "TRLR": trlr}

# --------------- import ---------------

def cmd_import(db):
    db.indi.delete_many({})
    db.fam.delete_many({})
    db.matches.delete_many({})
    indi, fam, _meta = parse_gedcom(GEDCOM_IN)
    if indi:
        db.indi.insert_many(list(indi.values()))
    if fam:
        db.fam.insert_many(list(fam.values()))
    ensure_indexes(db)
    print(f"Imported: {len(indi):,} INDI, {len(fam):,} FAM from {GEDCOM_IN}")

# --------------- duplicates ---------------

def groups_by_key(db) -> Dict[Tuple[str, Optional[int]], List[Dict[str, Any]]]:
    groups: Dict[Tuple[str, Optional[int]], List[Dict[str, Any]]] = defaultdict(list)
    for p in db.indi.find({}, {"_id": 1, "xref": 1, "name": 1, "norm_name": 1, "birth.year": 1, "death.year": 1}):
        key = (p.get("norm_name") or "", p.get("birth", {}).get("year"))
        if key[0]:  # require a name
            groups[key].append(p)
    return groups

def cmd_find_dupes(db, top_n: int = 30):
    groups = groups_by_key(db)
    candidates = [(k, v) for k, v in groups.items() if len(v) > 1]
    candidates.sort(key=lambda kv: len(kv[1]), reverse=True)
    total_groups = len(candidates)
    total_people = sum(len(v) for _, v in candidates)
    print(f"Duplicate key groups (name+birth_year): {total_groups:,} groups, {total_people:,} people in groups.")
    for (name_key, byear), people in candidates[:top_n]:
        print(f"\n[{len(people)}] name='{name_key}' birth_year={byear}")
        for p in people[:10]:
            dy = p.get("death", {}).get("year")
            print(f"  - {p['_id']} {p.get('xref')} {p.get('name')}  (d.{dy})")
        if len(people) > 10:
            print("  …")

def strict_pairable(people: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Given people with identical (norm_name,birth_year), return disjoint safe pairs:
    - Only pairs of size 2 in the group (unique pair)
    - If both have death.year, they must match
    """
    if len(people) != 2:
        return []
    a, b = people[0], people[1]
    dy_a = a.get("death", {}).get("year")
    dy_b = b.get("death", {}).get("year")
    if dy_a is not None and dy_b is not None and dy_a != dy_b:
        return []
    return [(a, b)]

def cmd_automerge_strict(db):
    groups = groups_by_key(db)
    merged = 0
    for key, people in groups.items():
        pairs = strict_pairable(people)
        for a, b in pairs:
            # prefer keeping the one with more link participation (heuristic)
            deg_a = participation_degree(db, a["_id"])
            deg_b = participation_degree(db, b["_id"])
            keep, drop = (a, b) if deg_a >= deg_b else (b, a)
            merge_people(db, keep["_id"], drop["_id"])
            db.matches.update_one({"a": keep["_id"], "b": drop["_id"]},
                                  {"$set": {"a": keep["_id"], "b": drop["_id"], "status": "confirmed",
                                            "score": 1.0, "note": "automerge_strict", "decided_at": datetime.utcnow()}},
                                  upsert=True)
            merged += 1
    print(f"Auto-merged {merged:,} strict duplicate pairs.")

# --------------- links & merge ---------------

def participation_degree(db, pid: ObjectId) -> int:
    # count of FAMC+FAMS edges via INDI + appearances in FAM roles
    p = db.indi.find_one({"_id": pid}, {"FAMC": 1, "FAMS": 1})
    deg = len(p.get("FAMC", [])) + len(p.get("FAMS", []))
    deg += db.fam.count_documents({"CHIL": {"$elemMatch": {"$eq": p.get("xref")}}})
    deg += db.fam.count_documents({"HUSB": p.get("xref")}) + db.fam.count_documents({"WIFE": p.get("xref")})
    return deg

def merge_people(db, keep_oid: ObjectId, drop_oid: ObjectId):
    keep = db.indi.find_one({"_id": keep_oid})
    drop = db.indi.find_one({"_id": drop_oid})
    if not keep or not drop:
        return

    keep_x = keep["xref"]; drop_x = drop["xref"]

    # 1) Update FAMs that reference drop → keep (HUSB/WIFE/CHIL)
    db.fam.update_many({"HUSB": drop_x}, {"$set": {"HUSB": keep_x}})
    db.fam.update_many({"WIFE": drop_x}, {"$set": {"WIFE": keep_x}})
    for fam in db.fam.find({"CHIL": drop_x}, {"_id": 1, "CHIL": 1}):
        newchil = list(dict.fromkeys([keep_x if c == drop_x else c for c in fam["CHIL"]]))  # dedupe
        db.fam.update_one({"_id": fam["_id"]}, {"$set": {"CHIL": newchil}})

    # 2) Combine INDI fields
    def coalesce(a, b): return a if a not in (None, "", [], {}) else b
    def merge_map(a, b):
        out = dict(a or {})
        for k, v in (b or {}).items():
            if k not in out or out[k] in (None, "", []):
                out[k] = v
        return out

    updated = {}
    for fld in ("name", "given", "surname", "sex", "geni_id"):
        updated[fld] = coalesce(keep.get(fld), drop.get(fld))
    updated["birth"] = merge_map(keep.get("birth"), drop.get("birth"))
    updated["death"] = merge_map(keep.get("death"), drop.get("death"))
    # FAMC/FAMS union by xref
    famc = sorted(set((keep.get("FAMC") or []) + (drop.get("FAMC") or [])))
    fams = sorted(set((keep.get("FAMS") or []) + (drop.get("FAMS") or [])))
    updated["FAMC"] = famc
    updated["FAMS"] = fams
    updated["norm_name"] = norm_text(updated.get("name"))
    updated.setdefault("meta", keep.get("meta", {}))
    updated["meta"]["merged_at"] = datetime.utcnow()
    updated["meta"]["merged_from_xref"] = drop_x

    # 3) Write back keep
    db.indi.update_one({"_id": keep_oid}, {"$set": updated})

    # 4) Remove drop person
    db.indi.delete_one({"_id": drop_oid})

    # 5) Ensure bidirectional consistency after merge
    enforce_bidirectional(db, [keep_x])

def enforce_bidirectional(db, touch_xrefs: Optional[List[str]] = None):
    """
    Make sure:
      - If INDI.FAMC has @Fx@, that FAM.CHIL contains @Ix@.
      - If FAM.CHIL contains @Ix@, that INDI.FAMC contains @Fx@.
      - If INDI.FAMS has @Fx@, that FAM.(HUSB|WIFE) contains @Ix@ appropriately (cannot infer sex reliably, but we keep existing if set).
      - If FAM.(HUSB|WIFE) == @Ix@, then INDI.FAMS includes @Fx@.
    touch_xrefs: if provided, restrict to these INDI xrefs; else all.
    """
    indi_q = {} if not touch_xrefs else {"xref": {"$in": touch_xrefs}}

    # CHIL ↔ FAMC
    for p in db.indi.find(indi_q, {"xref": 1, "FAMC": 1}):
        ix = p["xref"]
        for fx in p.get("FAMC", []):
            fam = db.fam.find_one({"xref": fx}, {"_id": 1, "CHIL": 1})
            if not fam:
                continue
            if ix not in fam.get("CHIL", []):
                db.fam.update_one({"_id": fam["_id"]}, {"$push": {"CHIL": ix}})

    for f in db.fam.find({}, {"xref": 1, "CHIL": 1}):
        fx = f["xref"]
        for ix in f.get("CHIL", []):
            if not db.indi.find_one({"xref": ix, "FAMC": fx}):
                db.indi.update_one({"xref": ix}, {"$addToSet": {"FAMC": fx}})

    # (HUSB|WIFE) ↔ FAMS
    for f in db.fam.find({}, {"xref": 1, "HUSB": 1, "WIFE": 1}):
        fx = f["xref"]
        for role in ("HUSB", "WIFE"):
            ix = f.get(role)
            if ix and not db.indi.find_one({"xref": ix, "FAMS": fx}):
                db.indi.update_one({"xref": ix}, {"$addToSet": {"FAMS": fx}})

    for p in db.indi.find(indi_q, {"xref": 1, "FAMS": 1, "sex": 1}):
        ix = p["xref"]
        for fx in p.get("FAMS", []):
            fam = db.fam.find_one({"xref": fx}, {"_id": 1, "HUSB": 1, "WIFE": 1})
            if not fam:
                continue
            # If neither spouse is set, leave as-is (cannot infer reliably).
            # If already set to someone, leave it (do not overwrite).
            # Only ensure at least one of HUSB/WIFE equals ix when both empty.
            if not fam.get("HUSB") and not fam.get("WIFE"):
                # try assign by sex if provided
                if (p.get("sex") or "").upper() == "M":
                    db.fam.update_one({"_id": fam["_id"]}, {"$set": {"HUSB": ix}})
                elif (p.get("sex") or "").upper() == "F":
                    db.fam.update_one({"_id": fam["_id"]}, {"$set": {"WIFE": ix}})

# --------------- graph & pruning ---------------

def build_graph(db) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """
    Returns:
      adj: person_xref -> set(person_xref) undirected edges via family relations
      fams_by_person: person_xref -> set(fam_xref)
    """
    adj: Dict[str, Set[str]] = defaultdict(set)
    fams_by_person: Dict[str, Set[str]] = defaultdict(set)

    # child-parent edges
    for f in db.fam.find({}, {"xref": 1, "HUSB": 1, "WIFE": 1, "CHIL": 1}):
        fx = f["xref"]
        spouses = [x for x in [f.get("HUSB"), f.get("WIFE")] if x]
        children = f.get("CHIL", [])
        # spouse↔spouse
        if len(spouses) == 2:
            a, b = spouses
            adj[a].add(b); adj[b].add(a)
        # parent↔child
        for c in children:
            for p in spouses:
                adj[p].add(c); adj[c].add(p)
        # siblings via common family (connect children loosely)
        for i in range(len(children)):
            for j in range(i + 1, len(children)):
                a, b = children[i], children[j]
                adj[a].add(b); adj[b].add(a)
        # collect fam links
        for ix in spouses + children:
            fams_by_person[ix].add(fx)

    return adj, fams_by_person

def largest_component(memberships: Dict[str, Set[str]]) -> Set[str]:
    # BFS to find components
    visited: Set[str] = set()
    best: Set[str] = set()
    for start in memberships.keys():
        if start in visited:
            continue
        comp: Set[str] = set()
        q = deque([start]); visited.add(start)
        while q:
            u = q.popleft()
            comp.add(u)
            for v in memberships[u]:
                if v not in visited:
                    visited.add(v); q.append(v)
        if len(comp) > len(best):
            best = comp
    return best

def cmd_prune_unrelated_keep_largest(db):
    adj, fams_by_person = build_graph(db)
    if not adj:
        print("No relationships found; nothing pruned.")
        return
    keep = largest_component(adj)
    all_people = set(x["xref"] for x in db.indi.find({}, {"xref": 1}))
    drop_people = sorted(all_people - keep)
    if not drop_people:
        print("Already a single connected component; nothing to prune.")
        return

    # Delete unrelated people
    db.indi.delete_many({"xref": {"$in": drop_people}})

    # Remove them from families
    for f in db.fam.find({}, {"_id": 1, "HUSB": 1, "WIFE": 1, "CHIL": 1}):
        upd = {}
        if f.get("HUSB") in drop_people: upd["HUSB"] = None
        if f.get("WIFE") in drop_people: upd["WIFE"] = None
        ch = [c for c in (f.get("CHIL") or []) if c not in drop_people]
        if ch != (f.get("CHIL") or []): upd["CHIL"] = ch
        if upd:
            db.fam.update_one({"_id": f["_id"]}, {"$set": upd})

    # Remove empty families (no spouses, no children)
    removed_fams = db.fam.delete_many({
        "$and": [
            {"$or": [{"HUSB": None}, {"HUSB": {"$exists": False}}]},
            {"$or": [{"WIFE": None}, {"WIFE": {"$exists": False}}]},
            {"$or": [{"CHIL": {"$size": 0}}, {"CHIL": {"$exists": False}}]}
        ]
    }).deleted_count

    enforce_bidirectional(db)  # consistency pass
    print(f"Pruned {len(drop_people):,} unrelated people; removed {removed_fams:,} empty families.")

# --------------- cleaners ---------------

def cmd_clean_placeholders(db):
    # Clear surname if literally "Placeholder surname" (case-insensitive)
    q = {"surname": {"$regex": r"^placeholder surname$", "$options": "i"}}
    n = 0
    for p in db.indi.find(q, {"_id": 1, "given": 1, "surname": 1, "name": 1}):
        new_surn = None
        new_name = (p.get("given") or "").strip()
        db.indi.update_one({"_id": p["_id"]},
                           {"$set": {"surname": new_surn, "name": new_name, "norm_name": norm_text(new_name)}})
        n += 1
    print(f"Cleaned {n} placeholder surnames.")

# --------------- export ---------------

def cmd_export(db, out_path: str):
    # Renumber to new sequential @I…@/@F…@ so everything is consistent
    person_map: Dict[str, str] = {}
    family_map: Dict[str, str] = {}

    # Assign new IDs
    i_no = 1
    for p in db.indi.find({}, {"xref": 1}).sort("xref", 1):
        person_map[p["xref"]] = f"@I{i_no}@"; i_no += 1
    f_no = 1
    for f in db.fam.find({}, {"xref": 1}).sort("xref", 1):
        family_map[f["xref"]] = f"@F{f_no}@"; f_no += 1

    out: List[str] = []
    # HEAD (minimal)
    out.append("0 HEAD")
    out.append("1 SOUR GAIAD_TREE")
    out.append("1 GEDC")
    out.append("2 VERS 5.5.1")
    out.append("2 FORM LINEAGE-LINKED")
    out.append("1 CHAR UTF-8")

    # INDI
    for p in db.indi.find({}).sort("xref", 1):
        ix = person_map[p["xref"]]
        out.append(f"0 {ix} INDI")
        nm = p.get("name") or ""
        givn = (p.get("given") or "").strip()
        surn = (p.get("surname") or "")
        # NAME line (GEDCOM wants GIVN /SURN/)
        if givn or surn or nm:
            display_givn = givn if givn else (nm.split(" ")[0] if nm else "")
            display_surn = surn if surn else (" ".join(nm.split(" ")[1:]) if nm and " " in nm else "")
            out.append(f"1 NAME {display_givn} /{display_surn}/")
            if display_givn: out.append(f"2 GIVN {display_givn}")
            if display_surn: out.append(f"2 SURN {display_surn}")
        if p.get("sex"): out.append(f"1 SEX {p['sex']}")
        # birth
        b = p.get("birth") or {}
        if b.get("date") or b.get("place"):
            out.append("1 BIRT")
            if b.get("date"): out.append(f"2 DATE {b['date']}")
            if b.get("place"): out.append(f"2 PLAC {b['place']}")
        # death
        d = p.get("death") or {}
        if d.get("date") or d.get("place"):
            out.append("1 DEAT")
            if d.get("date"): out.append(f"2 DATE {d['date']}")
            if d.get("place"): out.append(f"2 PLAC {d['place']}")
        # family links
        for fx in (p.get("FAMC") or []):
            if fx in family_map: out.append(f"1 FAMC {family_map[fx]}")
        for fx in (p.get("FAMS") or []):
            if fx in family_map: out.append(f"1 FAMS {family_map[fx]}")

    # FAM
    for f in db.fam.find({}).sort("xref", 1):
        fx = family_map[f["xref"]]
        out.append(f"0 {fx} FAM")
        if f.get("HUSB") and f["HUSB"] in person_map: out.append(f"1 HUSB {person_map[f['HUSB']]}")
        if f.get("WIFE") and f["WIFE"] in person_map: out.append(f"1 WIFE {person_map[f['WIFE']]}")
        for cx in (f.get("CHIL") or []):
            if cx in person_map: out.append(f"1 CHIL {person_map[cx]}")
        marr = f.get("MARR") or {}
        if marr.get("date") or marr.get("place"):
            out.append("1 MARR")
            if marr.get("date"): out.append(f"2 DATE {marr['date']}")
            if marr.get("place"): out.append(f"2 PLAC {marr['place']}")

    out.append("0 TRLR")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"Wrote GEDCOM: {out_path}  ({len(person_map):,} INDI, {len(family_map):,} FAM)")

# --------------- CLI ---------------

def main():
    ap = argparse.ArgumentParser(description="GIAD tree tools (hard-coded to Gaiad.ged → Gaiad_tree)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("import", help="Import Gaiad.ged into Mongo (indi,fam)")

    sub.add_parser("find-dupes", help="List duplicate key groups (name+birth_year)")

    sub.add_parser("automerge-strict", help="Auto-merge only unambiguous identicals")

    sp_prune = sub.add_parser("prune-unrelated", help="Remove people not in the kept component")
    sp_prune.add_argument("--keep-largest", action="store_true", help="Keep only the largest component")

    sub.add_parser("clean-placeholders", help="Remove SURN == 'Placeholder surname'")

    sp_exp = sub.add_parser("export", help="Export current DB to GEDCOM")
    sp_exp.add_argument("--out", required=True, help="Output .ged path")

    args = ap.parse_args()
    db = get_db()
    ensure_indexes(db)

    if args.cmd == "import":
        cmd_import(db)

    elif args.cmd == "find-dupes":
        cmd_find_dupes(db)

    elif args.cmd == "automerge-strict":
        cmd_automerge_strict(db)

    elif args.cmd == "prune-unrelated":
        if args.keep_largest:
            cmd_prune_unrelated_keep_largest(db)
        else:
            print("Specify --keep-largest (only mode implemented for now).")

    elif args.cmd == "clean-placeholders":
        cmd_clean_placeholders(db)

    elif args.cmd == "export":
        cmd_export(db, args.out)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(1)
