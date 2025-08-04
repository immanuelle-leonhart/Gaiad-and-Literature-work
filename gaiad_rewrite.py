#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gaiad_rewrite.py
Fresh, single-run GEDCOM fixer for a MyHeritage export.

Flow (one run, no options):
  1) Loads ./Gaiad.ged
  2) Builds a fresh SQLite DB (gaiad_work.db)
  3) Repairs and sanitizes:
       - Fix bidirectional links (INDI.FAMC <-> FAM.CHIL; INDI.FAMS <-> FAM.HUSB/WIFE)
       - Remove pointers to missing targets
       - Remove empty families
       - Strip OBJE/FILE media refs under INDI/FAM
       - Clean literal "Placeholder surname"
  4) (Optional) Auto-merge only unambiguous duplicates — OFF by default
  5) Exports clean GEDCOM back to ./Gaiad.ged (or Gaiad_clean.ged if locked)
"""

import os, re, sqlite3, shutil, unicodedata
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple, Set

# ---------- CONFIG ----------
IN_PATH  = "Gaiad.ged"
OUT_PATH = "Gaiad.ged"
BAK_PATH = "Gaiad.ged.bak"
DB_PATH  = "gaiad_work.db"

AUTO_MERGE_STRICT = False  # OFF per your request

# ---------- utils ----------
def norm_text(s: Optional[str]) -> str:
    if not s: return ""
    s = unicodedata.normalize("NFKC", s).lower()
    s = re.sub(r"[^\w\s-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def extract_year(date_str: Optional[str]) -> Optional[int]:
    if not date_str: return None
    m = re.search(r"(\d{4})", date_str)
    if not m: return None
    y = int(m.group(1))
    return y if 1000 <= y <= 2100 else None

def log(msg: str): print(msg, flush=True)

# ---------- DB ----------
def db_init():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript("""
    PRAGMA journal_mode=WAL;
    DROP TABLE IF EXISTS indi;
    DROP TABLE IF EXISTS fam;
    DROP TABLE IF EXISTS indi_famc;
    DROP TABLE IF EXISTS indi_fams;
    DROP TABLE IF EXISTS fam_chil;

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
    """)
    con.commit()
    return con

# ---------- GEDCOM parse (strip OBJE; clean placeholders) ----------
def parse_gedcom(path: str):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\r\n") for ln in f]

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
        m = re.match(r"^(\d+)\s+(@[^@]+@)?\s*([A-Z0-9_]+)?\s*(.*)$", s)
        if not m: return 0, None, None, ""
        return int(m.group(1)), m.group(2), m.group(3), (m.group(4) or "").strip()

    for rec in records:
        lvl0, xrf0, tag0, arg0 = get_tag(rec[0])

        if tag0 == "INDI":
            xref = xrf0
            data = {"xref": xref, "FAMC": [], "FAMS": []}
            givn = surn = raw_name = sex = None
            bdate = bplac = ddate = dplac = None
            path = []
            skipping_obje = False
            for ln in rec[1:]:
                lvl, xrf, tag, arg = get_tag(ln)
                # strip OBJE subtree under INDI
                if tag == "OBJE":
                    skipping_obje = True; continue
                if skipping_obje:
                    if lvl == 1 and tag not in ("CONC", "CONT"):
                        skipping_obje = False
                    else:
                        continue
                while path and path[-1][0] >= lvl: path.pop()
                path.append((lvl, tag or ""))

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

            if (givn or surn):
                name = f"{(givn or '').strip()} {(surn or '').strip()}".strip()
            else:
                name = (raw_name or "").replace("/", "").strip()

            if (surn or "").strip().lower() == "placeholder surname":
                surn = None
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
            skipping_obje = False
            path = []
            for ln in rec[1:]:
                lvl, xrf, tag, arg = get_tag(ln)
                if tag == "OBJE":
                    skipping_obje = True; continue
                if skipping_obje:
                    if lvl == 1 and tag not in ("CONC", "CONT"):
                        skipping_obje = False
                    else:
                        continue
                while path and path[-1][0] >= lvl: path.pop()
                path.append((lvl, tag or ""))

                if tag == "HUSB": husb = arg
                elif tag == "WIFE": wife = arg
                elif tag == "CHIL": chil.append(arg)

            fam_recs[xref] = {"xref": xref, "HUSB": husb, "WIFE": wife, "CHIL": chil}

        # top-level OBJE: ignored

    return indi_recs, fam_recs

# ---------- load into DB ----------
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
        cur.execute("INSERT INTO fam(xref,husb,wife) VALUES (?,?,?)", (x, f["HUSB"], f["WIFE"]))
        for cx in f["CHIL"]:
            cur.execute("INSERT INTO fam_chil(fam_xref,indi_xref) VALUES (?,?)", (x, cx))
    con.commit()

# ---------- repairs & sanitizing ----------
def repair_links(con):
    cur = con.cursor()
    fams = {r[0] for r in cur.execute("SELECT xref FROM fam")}
    # prune bad INDI->FAM refs
    for ix, fx in list(cur.execute("SELECT indi_xref,fam_xref FROM indi_famc")):
        if fx not in fams: cur.execute("DELETE FROM indi_famc WHERE indi_xref=? AND fam_xref=?", (ix, fx))
    for ix, fx in list(cur.execute("SELECT indi_xref,fam_xref FROM indi_fams")):
        if fx not in fams: cur.execute("DELETE FROM indi_fams WHERE indi_xref=? AND fam_xref=?", (ix, fx))

    people = {r[0] for r in cur.execute("SELECT xref FROM indi")}
    # prune bad FAM->INDI refs
    for fx, hx in list(cur.execute("SELECT xref,husb FROM fam")):
        if hx and hx not in people: cur.execute("UPDATE fam SET husb=NULL WHERE xref=?", (fx,))
    for fx, wx in list(cur.execute("SELECT xref,wife FROM fam")):
        if wx and wx not in people: cur.execute("UPDATE fam SET wife=NULL WHERE xref=?", (fx,))
    for fx, ix in list(cur.execute("SELECT fam_xref,indi_xref FROM fam_chil")):
        if ix not in people: cur.execute("DELETE FROM fam_chil WHERE fam_xref=? AND indi_xref=?", (fx, ix))
    con.commit()

    # enforce child bidirectionality
    for ix, fx in list(cur.execute("SELECT indi_xref,fam_xref FROM indi_famc")):
        if not cur.execute("SELECT 1 FROM fam_chil WHERE fam_xref=? AND indi_xref=?", (fx, ix)).fetchone():
            cur.execute("INSERT INTO fam_chil(fam_xref,indi_xref) VALUES (?,?)", (fx, ix))
    for fx, ix in list(cur.execute("SELECT fam_xref,indi_xref FROM fam_chil")):
        if not cur.execute("SELECT 1 FROM indi_famc WHERE indi_xref=? AND fam_xref=?", (ix, fx)).fetchone():
            cur.execute("INSERT INTO indi_famc(indi_xref,fam_xref) VALUES (?,?)", (ix, fx))

    # enforce spouse bidirectionality
    for fx, hx, wx in list(cur.execute("SELECT xref,husb,wife FROM fam")):
        if hx and not cur.execute("SELECT 1 FROM indi_fams WHERE indi_xref=? AND fam_xref=?", (hx, fx)).fetchone():
            cur.execute("INSERT INTO indi_fams(indi_xref,fam_xref) VALUES (?,?)", (hx, fx))
        if wx and not cur.execute("SELECT 1 FROM indi_fams WHERE indi_xref=? AND fam_xref=?", (wx, fx)).fetchone():
            cur.execute("INSERT INTO indi_fams(indi_xref,fam_xref) VALUES (?,?)", (wx, fx))
    con.commit()

    # drop empty families (no spouses, no children)
    cur.execute("""
      DELETE FROM fam
      WHERE (husb IS NULL OR husb='') AND (wife IS NULL OR wife='')
        AND xref NOT IN (SELECT DISTINCT fam_xref FROM fam_chil)
    """)
    con.commit()

# ---------- optional strict auto-merge ----------
def strict_automerge(con) -> int:
    cur = con.cursor()
    groups: Dict[Tuple[str, Optional[int]], List[str]] = defaultdict(list)
    for norm_name, by, x in cur.execute("SELECT norm_name,birth_year,xref FROM indi"):
        if norm_name: groups[(norm_name, by)].append(x)
    merged = 0
    for key, members in groups.items():
        if len(members) != 2: continue
        a, b = members
        da = cur.execute("SELECT death_year FROM indi WHERE xref=?", (a,)).fetchone()[0]
        db = cur.execute("SELECT death_year FROM indi WHERE xref=?", (b,)).fetchone()[0]
        if (da is not None) and (db is not None) and (da != db): continue

        def degree(ix: str) -> int:
            d = 0
            d += cur.execute("SELECT COUNT(*) FROM indi_famc WHERE indi_xref=?", (ix,)).fetchone()[0]
            d += cur.execute("SELECT COUNT(*) FROM indi_fams WHERE indi_xref=?", (ix,)).fetchone()[0]
            d += cur.execute("SELECT COUNT(*) FROM fam WHERE husb=? OR wife=?", (ix, ix)).fetchone()[0]
            d += cur.execute("SELECT COUNT(*) FROM fam_chil WHERE indi_xref=?", (ix,)).fetchone()[0]
            return d
        keep, drop = (a, b) if degree(a) >= degree(b) else (b, a)

        cur.execute("UPDATE fam SET husb=? WHERE husb=?", (keep, drop))
        cur.execute("UPDATE fam SET wife=? WHERE wife=?", (keep, drop))
        cur.execute("UPDATE fam_chil SET indi_xref=? WHERE indi_xref=?", (keep, drop))

        famc_keep = {r[0] for r in cur.execute("SELECT fam_xref FROM indi_famc WHERE indi_xref=?", (keep,))}
        famc_drop = {r[0] for r in cur.execute("SELECT fam_xref FROM indi_famc WHERE indi_xref=?", (drop,))}
        fams_keep = {r[0] for r in cur.execute("SELECT fam_xref FROM indi_fams WHERE indi_xref=?", (keep,))}
        fams_drop = {r[0] for r in cur.execute("SELECT fam_xref FROM indi_fams WHERE indi_xref=?", (drop,))}
        for fx in (famc_drop - famc_keep): cur.execute("INSERT INTO indi_famc(indi_xref,fam_xref) VALUES (?,?)", (keep, fx))
        for fx in (fams_drop - fams_keep): cur.execute("INSERT INTO indi_fams(indi_xref,fam_xref) VALUES (?,?)", (keep, fx))

        def coalesce(col):
            va = cur.execute(f"SELECT {col} FROM indi WHERE xref=?", (keep,)).fetchone()[0]
            vb = cur.execute(f"SELECT {col} FROM indi WHERE xref=?", (drop,)).fetchone()[0]
            return va if va not in (None, "", 0) else vb

        updated = {
            "name": coalesce("name"), "given": coalesce("given"), "surname": coalesce("surname"), "sex": coalesce("sex"),
            "birth_date": coalesce("birth_date"), "birth_year": coalesce("birth_year"), "birth_place": coalesce("birth_place"),
            "death_date": coalesce("death_date"), "death_year": coalesce("death_year"), "death_place": coalesce("death_place"),
            "norm_name": coalesce("norm_name"), "geni_id": coalesce("geni_id"),
        }
        cur.execute("""
          UPDATE indi SET
            name=:name, given=:given, surname=:surname, sex=:sex,
            birth_date=:birth_date, birth_year=:birth_year, birth_place=:birth_place,
            death_date=:death_date, death_year=:death_year, death_place=:death_place,
            norm_name=:norm_name, geni_id=:geni_id
          WHERE xref=:xref
        """, {**updated, "xref": keep})

        cur.execute("DELETE FROM indi WHERE xref=?", (drop,))
        cur.execute("DELETE FROM indi_famc WHERE indi_xref=?", (drop,))
        cur.execute("DELETE FROM indi_fams WHERE indi_xref=?", (drop,))
        merged += 1

    cur.execute("""
      DELETE FROM fam
      WHERE (husb IS NULL OR husb='') AND (wife IS NULL OR wife='')
        AND xref NOT IN (SELECT DISTINCT fam_xref FROM fam_chil)
    """)
    con.commit()
    return merged

# ---------- export (prefetch; no nested cursor reuse) ----------
def export_gedcom(con, out_path: str):
    cur = con.cursor()

    # Prefetch entities
    people = list(cur.execute("""
        SELECT xref,name,given,surname,sex,birth_date,birth_place,death_date,death_place
        FROM indi ORDER BY xref
    """))
    families = list(cur.execute("SELECT xref,husb,wife FROM fam ORDER BY xref"))

    famc_map: Dict[str, List[str]] = defaultdict(list)
    for ix, fx in cur.execute("SELECT indi_xref,fam_xref FROM indi_famc ORDER BY indi_xref,fam_xref"):
        famc_map[ix].append(fx)
    fams_map: Dict[str, List[str]] = defaultdict(list)
    for ix, fx in cur.execute("SELECT indi_xref,fam_xref FROM indi_fams ORDER BY indi_xref,fam_xref"):
        fams_map[ix].append(fx)
    chil_map: Dict[str, List[str]] = defaultdict(list)
    for fx, ix in cur.execute("SELECT fam_xref,indi_xref FROM fam_chil ORDER BY fam_xref,indi_xref"):
        chil_map[fx].append(ix)

    # Renumber maps
    person_map: Dict[str, str] = {}
    family_map: Dict[str, str] = {}
    for i, (xref, *_rest) in enumerate(people, start=1):
        person_map[xref] = f"@I{i}@"
    for i, (xref, *_rest) in enumerate(families, start=1):
        family_map[xref] = f"@F{i}@"

    out: List[str] = []
    out.append("0 HEAD")
    out.append("1 SOUR GAIAD_REWRITE")
    out.append("1 GEDC")
    out.append("2 VERS 5.5.1")
    out.append("2 FORM LINEAGE-LINKED")
    out.append("1 CHAR UTF-8")

    # INDI
    for xref,name,givn,surn,sex,bd,bp,dd,dp in people:
        ix = person_map[xref]
        out.append(f"0 {ix} INDI")
        disp_givn = (givn or "").strip()
        disp_surn = (surn or "").strip()
        if not (disp_givn or disp_surn):
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
        for fx in famc_map.get(xref, []):
            if fx in family_map: out.append(f"1 FAMC {family_map[fx]}")
        for fx in fams_map.get(xref, []):
            if fx in family_map: out.append(f"1 FAMS {family_map[fx]}")

    # FAM
    for xref,hx,wx in families:
        fx = family_map[xref]
        out.append(f"0 {fx} FAM")
        if hx and hx in person_map: out.append(f"1 HUSB {person_map[hx]}")
        if wx and wx in person_map: out.append(f"1 WIFE {person_map[wx]}")
        for cx in chil_map.get(xref, []):
            if cx in person_map: out.append(f"1 CHIL {person_map[cx]}")

    out.append("0 TRLR")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")

# ---------- run ----------
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

    cur = con.cursor()
    people_before = cur.execute("SELECT COUNT(*) FROM indi").fetchone()[0]
    fams_before   = cur.execute("SELECT COUNT(*) FROM fam").fetchone()[0]

    merged = 0
    if AUTO_MERGE_STRICT:
        log("Auto-merging strict duplicate pairs ...")
        merged = strict_automerge(con)
        repair_links(con)
    else:
        log("Skipping duplicate auto-merge (AUTO_MERGE_STRICT=False)")

    people_after = cur.execute("SELECT COUNT(*) FROM indi").fetchone()[0]
    fams_after   = cur.execute("SELECT COUNT(*) FROM fam").fetchone()[0]
    log(f"Merged {merged:,} pairs. People: {people_before:,} → {people_after:,}; Families: {fams_before:,} → {fams_after:,}")

    log("Exporting cleaned GEDCOM ...")
    try:
        export_gedcom(con, OUT_PATH)
        log(f"Done: wrote {OUT_PATH}")
    except PermissionError:
        alt = "Gaiad_clean.ged"
        log(f"Target '{OUT_PATH}' is locked. Writing to '{alt}' instead.")
        export_gedcom(con, alt)
        log(f"Done: wrote {alt}")

if __name__ == "__main__":
    main()
