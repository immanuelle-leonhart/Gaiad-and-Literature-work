#!/usr/bin/env python3
"""
Enhanced GEDCOM export from Muhammad database with proper REFN logic and notes.

REFN logic: Use Geni ID if present, otherwise use Q-ID
Notes: Include both Wikidata links and Geni IDs
"""
from __future__ import annotations
import argparse, datetime, re
from collections import defaultdict
from itertools   import count
from pymongo     import MongoClient

# ─── CLI ──────────────────────────────────────────────────────────────────────
cli = argparse.ArgumentParser()
cli.add_argument("--mongo", default="mongodb://127.0.0.1:27017")
cli.add_argument("--db",    default="Muhammad")
cli.add_argument("--coll",  default="persons")
cli.add_argument("--limit", type=int, default=15000)
cli.add_argument("--out",   default="muhammad_enhanced.ged")
args = cli.parse_args()

# ─── constants ───────────────────────────────────────────────────────────────
SEX_MAP = {"Q6581097": "M",        # male human
           "Q6581072": "F"}        # female human
MONTHS  = {1:"JAN",2:"FEB",3:"MAR",4:"APR",5:"MAY",6:"JUN",
           7:"JUL",8:"AUG",9:"SEP",10:"OCT",11:"NOV",12:"DEC"}

# ─── helpers ──────────────────────────────────────────────────────────────────
def as_qid(v):
    if isinstance(v,str) and v.startswith("Q"):
        return v
    if isinstance(v,dict):
        i=v.get("id","")
        return i if i.startswith("Q") else None
    return None

def first_dv(clm,pid):
    """Return first *stated* mainsnak value dict/str for property `pid`."""
    for st in clm.get(pid,[]):
        dv = st["mainsnak"].get("datavalue")
        if dv: return dv["value"]
    return None

def iso_to_ged(t) -> str:
    """
    Convert a Wikidata time dict or ISO string → GEDCOM text.
    Handles negative years & '00' placeholders.
    """
    if isinstance(t,dict):        # Wikidata time snak
        t = t.get("time")
    if not t or not isinstance(t,str):
        return ""

    m=re.match(r"([+-]?\d{1,6})-(\d{2})-(\d{2})",t)
    if not m: return ""
    y,mm,dd=map(int,m.groups())
    bc = y < 0
    y  = abs(y)

    if 1 <= mm <= 12:
        if dd > 0:
            return f"{dd} {MONTHS[mm]} {y}{' BC' if bc else ''}"
        return f"{MONTHS[mm]} {y}{' BC' if bc else ''}"
    return f"{y}{' BC' if bc else ''}"

def writ(lvl:int,tag:str,val:str="",xref:str="",fh=None):
    fh.write(f"{lvl} {'%s ' % xref if xref else ''}{tag}{' '+val if val else ''}\n")

def build_note_text(qid: str, geni_id: str = None) -> str:
    """Build note text with Wikidata and optionally Geni information."""
    notes = [f"Wikidata: https://www.wikidata.org/wiki/{qid}"]
    if geni_id:
        notes.append(f"Geni: https://www.geni.com/people/{geni_id}")
    return " | ".join(notes)

# ─── fetch slice from Mongo ───────────────────────────────────────────────────
print(f"Loading first {args.limit} docs from enhanced database...")
coll = MongoClient(args.mongo)[args.db][args.coll]
docs = list(coll.find({},{"_id":0}).limit(args.limit))

people   :dict[str,dict]             = {}
families :dict[tuple[str|None,str|None],set[str]] = defaultdict(set)

for d in docs:
    qid  = d["wikidata_id"]
    clm  = d["extracted"]["claims"]
    lbls = d["extracted"]["labels"]
    geni_id = d["extracted"].get("geni_profile_id")

    # Use English name if available, otherwise fall back to other languages or Q-ID
    name = (lbls.get("en") or lbls.get("mul") or lbls.get("ja") or {}).get("value", qid)
    
    sex = SEX_MAP.get(as_qid(first_dv(clm,"P21")),"U")
    birt = iso_to_ged(first_dv(clm,"P569"))
    deat = iso_to_ged(first_dv(clm,"P570"))

    father = as_qid(first_dv(clm,"P22"))
    mother = as_qid(first_dv(clm,"P25"))
    if father or mother:
        key = (father, mother)         # keep order, don't sort Nones
        families[key].add(qid)

    for st in clm.get("P26",[]):
        sp = as_qid(st["mainsnak"].get("datavalue",{}).get("value"))
        if sp:
            key = tuple(sorted((qid,sp)))  # both real Q-ids ⇒ safe to sort
            families[key]        # ensure key exists

    people[qid] = dict(
        NAME=name, SEX=sex, BIRT=birt, DEAT=deat,
        FAMS=set(), FAMC=None, 
        GENI_ID=geni_id,
        QID=qid
    )

# ─── link people ↔ families ──────────────────────────────────────────────────
fam_x  = {k:f"@F{n}@" for n,k in enumerate(families,1)}
indi_x = {q:f"@I{n}@" for n,q in enumerate(people, 1)}

for (a,b),kids in families.items():
    fx = fam_x[(a,b)]
    if a and a in people: people[a]["FAMS"].add(fx)
    if b and b in people: people[b]["FAMS"].add(fx)
    for c in kids:
        if c in people: people[c]["FAMC"]=fx

# ─── write enhanced GEDCOM ───────────────────────────────────────────────────
print(f"Writing enhanced GEDCOM to {args.out}...")
with open(args.out,"w",encoding="utf-8") as g:
    writ(0,"HEAD",fh=g)
    writ(1,"SOUR","Enhanced Muhammad Database Export v1.0",fh=g)
    writ(1,"DATE",datetime.date.today().strftime("%d %b %Y").upper(),fh=g)
    writ(1,"CHAR","UTF-8",fh=g)

    # Individuals ----------------------------------------------------------
    for qid,d in people.items():
        ix = indi_x[qid]
        writ(0,"INDI",xref=ix,fh=g)
        writ(1,"NAME",d["NAME"],fh=g)
        writ(1,"SEX", d["SEX"], fh=g)
        if d["BIRT"]:
            writ(1,"BIRT",fh=g); writ(2,"DATE",d["BIRT"],fh=g)
        if d["DEAT"]:
            writ(1,"DEAT",fh=g); writ(2,"DATE",d["DEAT"],fh=g)
        
        # Enhanced REFN logic: Geni ID takes precedence over Q-ID
        if d["GENI_ID"]:
            writ(1,"REFN",f"geni:{d['GENI_ID']}",fh=g)
            writ(2,"TYPE","GENI",fh=g)
        else:
            writ(1,"REFN",qid,fh=g)
            writ(2,"TYPE","WIKIDATA",fh=g)
        
        # Enhanced notes with both Wikidata and Geni information
        note_text = build_note_text(qid, d["GENI_ID"])
        writ(1,"NOTE",note_text,fh=g)
        
        if d["FAMC"]: writ(1,"FAMC",d["FAMC"],fh=g)
        for fx in sorted(d["FAMS"]):
            writ(1,"FAMS",fx,fh=g)

    # Families -------------------------------------------------------------
    for (a,b),kids in families.items():
        fx = fam_x[(a,b)]
        writ(0,"FAM",xref=fx,fh=g)
        if a and a in indi_x: writ(1,"HUSB",indi_x[a],fh=g)
        if b and b in indi_x: writ(1,"WIFE",indi_x[b],fh=g)
        for c in sorted(kids):
            if c in indi_x: writ(1,"CHIL",indi_x[c],fh=g)

    writ(0,"TRLR",fh=g)

# Statistics ----------------------------------------------------------------
total_people = len(people)
people_with_geni = sum(1 for p in people.values() if p["GENI_ID"])
people_with_english = sum(1 for qid, p in people.items() if p["NAME"] != qid)

print(f"Enhanced GEDCOM export completed!")
print(f"- Output file: {args.out}")
print(f"- Total individuals: {total_people}")
print(f"- With Geni profiles: {people_with_geni} ({people_with_geni/total_people*100:.1f}%)")
print(f"- With English names: {people_with_english} ({people_with_english/total_people*100:.1f}%)")
print(f"- Total families: {len(families)}")
print(f"- REFN priority: Geni ID > Wikidata Q-ID")
print(f"- Notes include: Wikidata links + Geni profiles (when available)")