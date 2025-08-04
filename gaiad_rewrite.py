#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gaiad_rewrite.py
Fresh, single-run GEDCOM fixer for a MyHeritage export.

What it does (one run, no options):
  1) Loads ./Gaiad.ged
  2) Builds a fresh SQLite DB (gaiad_work.db) from scratch
  3) Validates & repairs:
       - Fix bidirectional links (INDI.FAMC <-> FAM.CHIL; INDI.FAMS <-> FAM.HUSB/WIFE)
       - Remove pointers to missing targets
       - Remove empty families
       - Strip OBJE/FILE media refs (kills .G00/.G01 prompts etc.)
       - Clean literal "Placeholder surname"
  4) Auto-merges only unambiguous duplicates:
       - identical normalized name AND same birth year
       - if both have death year, it must match
       - group must be exactly two people
       - updates all family links on both sides
  5) Exports a clean GEDCOM back to ./Gaiad.ged (UTF-8), after writing ./Gaiad.ged.bak

No third-party packages. Requires Python 3.9+.
"""

import os, re, sqlite3, shutil, unicodedata
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Set

IN_PATH  = "Gaiad.ged"
OUT_PATH = "Gaiad.ged"        # overwrite (back up first)
BAK_PATH = "Gaiad.ged.bak"
DB_PATH  = "gaiad_work.db"

# ---------------- utils ----------------

def norm_text(s: Optional[str]) -> str:
    if not s: return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    s = re.sub(r"[^\w\s-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_year(date_str: Optional[str]) -> Optional[int]:
    if not date_str: return None
    m = re.search(r"(\d{4})", date_str)
    if not m: return None
    y = int(m.group(1))
    return y if 1000 <= y <= 2100 else None

def log(msg: str):
    print(msg, flush=True)

# ---------------- DB ----------------

def db_init():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript("""
    PRAGMA journal_mode=WAL;
    DROP TABLE IF EXISTS indi;
    DROP TABLE IF EXISTS fam;
    CREATE TABLE indi (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      xref TEXT UNIQUE,
      name TEXT,
      given TEXT,
      surname TEXT,
      sex TEXT,
      birth_date TEXT, birth_year INTEGER, birth_place TEXT,
      death_date TEXT, death_year INTEGER, death_place TEXT,
      norm_name TEXT,
      geni_id TEXT
    );
    CREATE TABLE indi_famc(indi_xref TEXT, fam_xref TEXT);
    CREATE TABLE indi_fams(indi_xref TEXT, fam_xref TEXT);

    CREATE TABLE fam (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      xref TEXT UNIQUE,
      husb TEXT, wife TEXT
    );
    CREATE TABLE fam_chil(fam_xref TEXT, indi_xref TEXT);

    /* media objects ignored/stripped */
    """)
    con.commit()
    return con

# ---------------- GEDCOM parse ----------------

def parse_gedcom(path: str):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\r\n") for ln in f]

    # split into level-0 records
    records: List[List[str]] = []
    cur: List[str] = []
    for ln in lines:
        if ln.startswith("0 "):
            if cur: records.append(cur)
            cur = [ln]
        else:
            cur.append(ln)
    if cur: records.append(cur)

    indi_recs: Dict[str, Dict[str, Any]] = {}
    fam_recs:  Dict[str, Dict[str, Any]] = {}

    def get_tag(s: str) -> Tuple[int, Optional[str], Optional[str], str]:
        # returns (level, xref, tag, arg)
        m = re.match(r"^(\d+)\s+(@[^@]+@)?\s*([A-Z0-9_]+)?\s*(.*)$", s)
        if not m: return 0, None, None, ""
        lvl = int(m.group(1))
        xrf = m.group(2)
        tag = m.group(3)
        arg = (m.group(4) or "").strip()
        return lvl, xrf, tag, arg

    # Collect OBJE @...@ ids to drop them cleanly
    top_level_objes: Set[str] = set()

    for rec in records:
        lvl0, xrf0, tag0, arg0 = get_tag(rec[0])
        if tag0 == "INDI":
            xref = xrf0
            data = {"xref": xref, "FAMC": [], "FAMS": []}
            givn = surn = raw_name = sex = None
            bdate = bplac = ddate = dplac = None
            path = []
            skip_obj_block = False  # ignore embedded OBJE blocks entirely
            for ln in rec[1:]:
                lvl, xrf, tag, arg = get_tag(ln)
                while path and path[-1][0] >= lvl:
                    path.pop()
                path.append((lvl, tag or ""))

                if tag == "OBJE":
                    # Any inline media under an INDI: drop it and its subtree
                    skip_obj_block = True
                    continue
                if skip_obj_block:
                    # leave OBJE subtree
                    if lvl == 1 and tag != "CONC" and tag != "CONT":
                        skip_obj_block = False
                    else:
                        continue

                if tag == "NAME": raw_name = arg
                elif tag == "GIVN": givn = arg
                elif tag == "SURN": surn = arg
                elif tag == "SEX": sex = arg
                elif tag == "FAMC": data["FAMC"].append(arg)
                elif tag == "FAMS": data["FAMS"].append(arg)
                elif "/".join(t for _, t in path) == "BIRT/DATE": bdate = arg
                elif "/".join(t for _, t in path) == "BIRT/PLAC": bplac = arg
                elif "/".join(t for _, t in path) == "DEAT/DATE": ddate = arg
                elif "/".join(t for _, t in path) == "DEAT/PLAC": dplac = arg

            # Build display name: prefer GIVN/SURN
            if (givn or surn):
                name = f"{(givn or '').strip()} {(surn or '').strip()}".strip()
            else:
                name = (raw_name or "").replace("/", "").strip()

            # Clean literal "Placeholder surname"
            if (surn or "").strip().lower() == "placeholder surname":
                surn = None
                # if name is just that, collapse to given only
                name = (givn or "").strip()

            indi_recs[xref] = {
                "xref": xref,
                "name": name or None,
                "given": givn,
                "surname": surn,
                "sex": sex,
                "birth_date": bdate, "birth_year": extract_year(bdate), "birth_place": bplac,
                "death_date": ddate, "death_year": extract_year(ddate), "death_place": dplac,
                "norm_name": norm_text(name),
                "FAMC": data["FAMC"], "FAMS": data["FAMS"],
            }

        elif tag0 == "FAM":
            xref = xrf0
            husb = wife = None
            chil: List[str] = []
            skip_obj_block = False
            path = []
            for ln in rec[1:]:
                lvl, xrf, tag, arg = get_tag(ln)
                while path and path[-1][0] >= lvl:
                    path.pop()
                path.append((lvl, tag or ""))

                if tag == "OBJE":
                    skip_obj_block = True
                    continue
                if skip_obj_block:
                    if lvl == 1 and tag not in ("CONC", "CONT"):
                        skip_obj_block = False
                    else:
                        continue

                if tag in ("HUSB", "WIFE"):
                    if tag == "HUSB": husb = arg
                    else: wife = arg
                elif tag == "CHIL":
                    chil.append(arg)

            fam_recs[xref] = {"xref": xref, "HUSB": husb, "WIFE": wife, "CHIL": chil}

        elif tag0 == "OBJE" and xrf0:
            # Remember top-level media objects (we won’t emit them)
            top_level_objes.add(xrf0)

    return indi_recs, fam_recs

# ---------------- load into DB ----------------

def load_into_db(con, indi: Dict[str, Dict[str, Any]], fam: Dict[str, Dict[str, Any]]):
    cur = con.cursor()
    for x, p in indi.items():
        cur.execute("""
          INSERT INTO indi(xref,name,given,surname,sex,
                           birth_date,birth_year,birth_place,
                           death_date,death_year,death_place,
                           norm_name,geni_id)
          VALUES (?,?,?,?,?,?,?,?,?,?,?,?,NULL)
        """, (p["xref"], p["name"], p["given"], p["surname"], p["sex"],
              p["birth_date"], p["birth_year"], p["birth_place"],
              p["death_date"], p["death_year"], p["death_place"],
              p["norm_name"]))
        for fx in p["FAMC"]:
            cur.execute("INSERT INTO indi_famc(indi_xref,fam_xref) VALUES (?,?)", (x, fx))
        for fx in p["FAMS"]:
            cur.execute("INSERT INTO indi_fams(indi_xref,fam_xref) VALUES (?,?)", (x, fx))
    for x, f in fam.items():
        cur.execute("INSERT INTO fam(xref,husb,wife) VALUES (?,?,?)",
                    (x, f["HUSB"], f["WIFE"]))
        for cx in f["CHIL"]:
            cur.execute("INSERT INTO fam_chil(fam_xref,indi_xref) VALUES (?,?)", (x, cx))
    con.commit()

# ---------------- repairs & sanitizing ----------------

def repair_links(con):
    cur = con.cursor()
    # 1) Drop pointers to missing targets (INDI -> FAM)
    fams = {r[0] for r in cur.execute("SELECT xref FROM fam")}
    for ix, fx in list(cur.execute("SELECT indi_xref,fam_xref FROM indi_famc")):
        if fx not in fams:
            cur.execute("DELETE FROM indi_famc WHERE indi_xref=? AND fam_xref=?", (ix, fx))
    for ix, fx in list(cur.execute("SELECT indi_xref,fam_xref FROM indi_fams")):
        if fx not in fams:
            cur.execute("DELETE FROM indi_fams WHERE indi_xref=? AND fam_xref=?", (ix, fx))

    # 2) Drop FAM pointers to missing people
    people = {r[0] for r in cur.execute("SELECT xref FROM indi")}
    for fx, hx in list(cur.execute("SELECT xref,husb FROM fam")):
        if hx and hx not in people:
            cur.execute("UPDATE fam SET husb=NULL WHERE xref=?", (fx,))
    for fx, wx in list(cur.execute("SELECT xref,wife FROM fam")):
        if wx and wx not in people:
            cur.execute("UPDATE fam SET wife=NULL WHERE xref=?", (fx,))
    for fx, ix in list(cur.execute("SELECT fam_xref,indi_xref FROM fam_chil")):
        if ix not in people:
            cur.execute("DELETE FROM fam_chil WHERE fam_xref=? AND indi_xref=?", (fx, ix))

    con.commit()

    # 3) Enforce bidirectional child links
    for ix, fx in list(cur.execute("SELECT indi_xref,fam_xref FROM indi_famc")):
        has = cur.execute("SELECT 1 FROM fam_chil WHERE fam_xref=? AND indi_xref=?", (fx, ix)).fetchone()
        if not has:
            cur.execute("INSERT INTO fam_chil(fam_xref,indi_xref) VALUES (?,?)", (fx, ix))

    for fx, ix in list(cur.execute("SELECT fam_xref,indi_xref FROM fam_chil")):
        has = cur.execute("SELECT 1 FROM indi_famc WHERE indi_xref=? AND fam_xref=?", (ix, fx)).fetchone()
        if not has:
            cur.execute("INSERT INTO indi_famc(indi_xref,fam_xref) VALUES (?,?)", (ix, fx))

    # 4) Enforce bidirectional spouse links
    for fx, hx, wx in list(cur.execute("SELECT xref,husb,wife FROM fam")):
        if hx:
            has = cur.execute("SELECT 1 FROM indi_fams WHERE indi_xref=? AND fam_xref=?", (hx, fx)).fetchone()
            if not has:
                cur.execute("INSERT INTO indi_fams(indi_xref,fam_xref) VALUES (?,?)", (hx, fx))
        if wx:
            has = cur.execute("SELECT 1 FROM indi_fams WHERE indi_xref=? AND fam_xref=?", (wx, fx)).fetchone()
            if not has:
                cur.execute("INSERT INTO indi_fams(indi_xref,fam_xref) VALUES (?,?)", (wx, fx))

    con.commit()

    # 5) Remove empty families (no spouses and no children)
    cur.execute("""
      DELETE FROM fam
      WHERE (husb IS NULL OR husb='') AND (wife IS NULL OR wife='')
        AND xref NOT IN (SELECT DISTINCT fam_xref FROM fam_chil)
    """)
    con.commit()

def strict_automerge(con) -> int:
    """Merge only groups of exactly two with same norm_name + birth_year and death-year agree if both present."""
    cur = con.cursor()

    groups: Dict[Tuple[str, Optional[int]], List[str]] = defaultdict(list)
    for norm_name, by, x in cur.execute("SELECT norm_name,birth_year,xref FROM indi"):
        if norm_name:
            groups[(norm_name, by)].append(x)

    merged = 0
    for key, members in groups.items():
        if len(members) != 2:
            continue
        a, b = members[0], members[1]
        da = cur.execute("SELECT death_year FROM indi WHERE xref=?", (a,)).fetchone()[0]
        db = cur.execute("SELECT death_year FROM indi WHERE xref=?", (b,)).fetchone()[0]
        if (da is not None) and (db is not None) and (da != db):
            continue

        # choose keep by participation degree
        def degree(ix: str) -> int:
            d = 0
            d += cur.execute("SELECT COUNT(*) FROM indi_famc WHERE indi_xref=?", (ix,)).fetchone()[0]
            d += cur.execute("SELECT COUNT(*) FROM indi_fams WHERE indi_xref=?", (ix,)).fetchone()[0]
            d += cur.execute("SELECT COUNT(*) FROM fam WHERE husb=? OR wife=?", (ix, ix)).fetchone()[0]
            d += cur.execute("SELECT COUNT(*) FROM fam_chil WHERE indi_xref=?", (ix,)).fetchone()[0]
            return d
        keep, drop = (a, b) if degree(a) >= degree(b) else (b, a)

        # update families (husb/wife/child) to point to keep
        cur.execute("UPDATE fam SET husb=? WHERE husb=?", (keep, drop))
        cur.execute("UPDATE fam SET wife=? WHERE wife=?", (keep, drop))
        cur.execute("UPDATE fam_chil SET indi_xref=? WHERE indi_xref=?", (keep, drop))

        # union FAMC/FAMS
        famc_keep = {r[0] for r in cur.execute("SELECT fam_xref FROM indi_famc WHERE indi_xref=?", (keep,))}
        famc_drop = {r[0] for r in cur.execute("SELECT fam_xref FROM indi_famc WHERE indi_xref=?", (drop,))}
        fams_keep = {r[0] for r in cur.execute("SELECT fam_xref FROM indi_fams WHERE indi_xref=?", (keep,))}
        fams_drop = {r[0] for r in cur.execute("SELECT fam_xref FROM indi_fams WHERE indi_xref=?", (drop,))}
        for fx in (famc_drop - famc_keep):
            cur.execute("INSERT INTO indi_famc(indi_xref,fam_xref) VALUES (?,?)", (keep, fx))
        for fx in (fams_drop - fams_keep):
            cur.execute("INSERT INTO indi_fams(indi_xref,fam_xref) VALUES (?,?)", (keep, fx))

        # coalesce scalar fields (prefer keep if non-empty)
        def coalesce(col):
            va = cur.execute(f"SELECT {col} FROM indi WHERE xref=?", (keep,)).fetchone()[0]
            vb = cur.execute(f"SELECT {col} FROM indi WHERE xref=?", (drop,)).fetchone()[0]
            return va if va not in (None, "", 0) else vb

        updated = {
            "name": coalesce("name"),
            "given": coalesce("given"),
            "surname": coalesce("surname"),
            "sex": coalesce("sex"),
            "birth_date": coalesce("birth_date"),
            "birth_year": coalesce("birth_year"),
            "birth_place": coalesce("birth_place"),
            "death_date": coalesce("death_date"),
            "death_year": coalesce("death_year"),
            "death_place": coalesce("death_place"),
            "norm_name": coalesce("norm_name"),
            "geni_id": coalesce("geni_id"),
        }
        cur.execute("""
          UPDATE indi SET
            name=:name, given=:given, surname=:surname, sex=:sex,
            birth_date=:birth_date, birth_year=:birth_year, birth_place=:birth_place,
            death_date=:death_date, death_year=:death_year, death_place=:death_place,
            norm_name=:norm_name, geni_id=:geni_id
          WHERE xref=:xref
        """, {**updated, "xref": keep})

        # drop the duplicate person
        cur.execute("DELETE FROM indi WHERE xref=?", (drop,))
        cur.execute("DELETE FROM indi_famc WHERE indi_xref=?", (drop,))
        cur.execute("DELETE FROM indi_fams WHERE indi_xref=?", (drop,))

        merged += 1

    # remove empty families that may result
    cur.execute("""
      DELETE FROM fam
      WHERE (husb IS NULL OR husb='') AND (wife IS NULL OR wife='')
        AND xref NOT IN (SELECT DISTINCT fam_xref FROM fam_chil)
    """)
    con.commit()
    return merged

# ---------------- export ----------------

def export_gedcom(con, out_path: str):
    cur = con.cursor()
    # Renumber to sequential @I…@ / @F…@
    person_map: Dict[str, str] = {}
    family_map: Dict[str, str] = {}
    i_no = 1
    for (xref,) in cur.execute("SELECT xref FROM indi ORDER BY xref"):
        person_map[xref] = f"@I{i_no}@"; i_no += 1
    f_no = 1
    for (xref,) in cur.execute("SELECT xref FROM fam ORDER BY xref"):
        family_map[xref] = f"@F{f_no}@"; f_no += 1

    out: List[str] = []
    out.append("0 HEAD")
    out.append("1 SOUR GAIAD_REWRITE")
    out.append("1 GEDC")
    out.append("2 VERS 5.5.1")
    out.append("2 FORM LINEAGE-LINKED")
    out.append("1 CHAR UTF-8")

    # INDI
    for row in cur.execute("""
        SELECT xref,name,given,surname,sex,
               birth_date,birth_place,death_date,death_place
        FROM indi ORDER BY xref
    """):
        xref,name,givn,surn,sex,bd,bp,dd,dp = row
        ix = person_map[xref]
        out.append(f"0 {ix} INDI")
        disp_givn = (givn or "").strip()
        disp_surn = (surn or "").strip()
        if not (disp_givn or disp_surn):
            # derive from name if possible
            parts = (name or "").split(" ")
            if parts:
                disp_givn = parts[0]
                if len(parts) > 1: disp_surn = " ".join(parts[1:])
        out.append(f"1 NAME {disp_givn} /{disp_surn}/")
        if disp_givn: out.append(f"2 GIVN {disp_givn}")
        if disp_surn: out.append(f"2 SURN {disp_surn}")
        if sex: out.append(f"1 SEX {sex}")
        if bd or bp:
            out.append("1 BIRT")
            if bd: out.append(f"2 DATE {bd}")
            if bp: out.append(f"2 PLAC {bp}")
        if dd or dp:
            out.append("1 DEAT")
            if dd: out.append(f"2 DATE {dd}")
            if dp: out.append(f"2 PLAC {dp}")

        # FAMC/FAMS links
        for (fx,) in cur.execute("SELECT fam_xref FROM indi_famc WHERE indi_xref=? ORDER BY fam_xref", (xref,)):
            if fx in family_map:
                out.append(f"1 FAMC {family_map[fx]}")
        for (fx,) in cur.execute("SELECT fam_xref FROM indi_fams WHERE indi_xref=? ORDER BY fam_xref", (xref,)):
            if fx in family_map:
                out.append(f"1 FAMS {family_map[fx]}")

    # FAM
    for row in cur.execute("SELECT xref,husb,wife FROM fam ORDER BY xref"):
        fx,hx,wx = row
        new_fx = family_map[fx]
        out.append(f"0 {new_fx} FAM")
        if hx and hx in person_map: out.append(f"1 HUSB {person_map[hx]}")
        if wx and wx in person_map: out.append(f"1 WIFE {person_map[wx]}")
        for (cx,) in cur.execute("SELECT indi_xref FROM fam_chil WHERE fam_xref=? ORDER BY indi_xref", (fx,)):
            if cx in person_map:
                out.append(f"1 CHIL {person_map[cx]}")

    out.append("0 TRLR")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")

# ---------------- run ----------------

def main():
    if not os.path.exists(IN_PATH):
        raise SystemExit(f"Can't find {IN_PATH} in the current folder.")

    # backup first
    if os.path.exists(OUT_PATH):
        shutil.copy2(OUT_PATH, BAK_PATH)
        log(f"Backup written: {BAK_PATH}")

    log("Parsing GEDCOM ...")
    indi, fam = parse_gedcom(IN_PATH)
    log(f"Loaded {len(indi):,} INDI, {len(fam):,} FAM")

    con = db_init()
    load_into_db(con, indi, fam)

    log("Repairing links & removing broken pointers ...")
    repair_links(con)

    # quick stats before merge
    cur = con.cursor()
    people_before = cur.execute("SELECT COUNT(*) FROM indi").fetchone()[0]
    fams_before   = cur.execute("SELECT COUNT(*) FROM fam").fetchone()[0]

    log("Auto-merging strict duplicate pairs ...")
    merged = strict_automerge(con)

    # final link repair & empty family cleanup after merges
    repair_links(con)

    people_after = cur.execute("SELECT COUNT(*) FROM indi").fetchone()[0]
    fams_after   = cur.execute("SELECT COUNT(*) FROM fam").fetchone()[0]

    log(f"Merged {merged:,} pairs. People: {people_before:,} → {people_after:,}; Families: {fams_before:,} → {fams_after:,}")

    log("Exporting cleaned GEDCOM ...")
    export_gedcom(con, OUT_PATH)
    log(f"Done: wrote {OUT_PATH}")

if __name__ == "__main__":
    main()
