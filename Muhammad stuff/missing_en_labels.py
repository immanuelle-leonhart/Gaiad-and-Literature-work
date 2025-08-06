"""
missing_en_labels_jawiki.py   (with label search)
──────────────────────────────────────────────────
Browse japanese_genealogy.persons and patch Wikidata rows.

New            : search box – “en:Jimmu”, “fr:Jean”, or plain “Amaterasu”.
Label priority : en  >  mul  >  ja.
"""

from __future__ import annotations
import math, time, re, requests, streamlit as st, pandas as pd
from pymongo import MongoClient

# ── Mongo ────────────────────────────────────────────────────────────────────
COLL = (MongoClient("mongodb://127.0.0.1:27017")
        ["japanese_genealogy"]["persons"])

# ── Wikidata helper for per-row refresh ↻ ────────────────────────────────────
API   = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
HEAD  = {"User-Agent": "JP-Genealogy UI/1.2"}
TIMEO = 60

def patch_entity(qid: str):
    r = requests.get(API.format(qid), headers=HEAD, timeout=TIMEO)
    r.raise_for_status()
    ent = r.json()["entities"][qid]
    COLL.update_one(
        {"wikidata_id": qid},
        {"$set": {
            "wikidata_raw":        ent,
            "extracted.labels":    ent.get("labels", {}),
            "extracted.sitelinks": ent.get("sitelinks", {}),
            "extracted.claims":    ent.get("claims", {}),
        }},
        upsert=True,
    )

# ── query helpers ────────────────────────────────────────────────────────────
def build_query(no_en: bool, no_enwiki: bool,
                must_langs: list[str],
                search_lang: str | None,
                search_text: str | None) -> dict:
    clauses: list = []
    if no_en:
        clauses.append({
            "$or": [
                {"extracted.labels.en": {"$exists": False}},
                {"extracted.labels.en.value": ""},
            ]
        })
    if no_enwiki:
        clauses.append({"extracted.sitelinks.enwiki": {"$exists": False}})

    for lang in must_langs:
        clauses.append({
            f"extracted.labels.{lang}.value": {
                "$exists": True,
                "$ne":     ""
            }
        })

    if search_text:
        regex = {"$regex": re.escape(search_text), "$options": "i"}
        clauses.append({f"extracted.labels.{search_lang}.value": regex})

    return {"$and": clauses} if clauses else {}

PROJ = {
    "wikidata_id": 1,
    "extracted.labels": 1,
    "extracted.sitelinks": 1,
    "extracted.claims_resolved.P460": 1,
    "_id": 0,
}

def total_rows(q: dict) -> int:
    return COLL.count_documents(q)

def fetch_page(q: dict, page: int, size: int) -> pd.DataFrame:
    cur = (COLL.find(q, PROJ)
                .skip(page * size)
                .limit(size))
    rows = []
    for d in cur:
        qid  = d["wikidata_id"]
        lbls = d.get("extracted", {}).get("labels", {})

        display = (
            lbls.get("en",  {}).get("value") or
            lbls.get("mul", {}).get("value") or
            lbls.get("ja",  {}).get("value") or
            "(no label)"
        )

        sl   = d.get("extracted", {}).get("sitelinks", {})
        jp_sl = sl.get("jawiki") or {}
        wp_url   = jp_sl.get("url", "")
        wp_title = jp_sl.get("title", "")

        same = (d.get("extracted", {})
                  .get("claims_resolved", {})
                  .get("P460", []))
        same_lab = ", ".join(x.get("label") or x.get("id") for x in same) or "—"

        rows.append({
            "Q-ID":       qid,
            "Display":    display,
            "Wikidata":   f"https://www.wikidata.org/wiki/{qid}",
            "JP_WP_URL":   wp_url,
            "JP_WP_TITLE": wp_title,
            "Same-as":    same_lab,
            "All labels": ", ".join(f"{k}:{v['value']}" for k, v in lbls.items()),
        })
    return pd.DataFrame(rows)

def rerun():
    if hasattr(st, "rerun"): st.rerun()
    else: st.experimental_rerun()

# ── UI ───────────────────────────────────────────────────────────────────────
st.set_page_config("Missing EN labels", layout="wide")
st.title("🈚️  Missing English Labels — Japanese Genealogy DB")

# ── Sidebar filters ─────────────────────────────────────────────────────────
st.sidebar.header("Filters")

only_no_en  = st.sidebar.checkbox("Hide rows *with* an English label", value=True)
only_no_wp  = st.sidebar.checkbox("Hide rows *with* an English-Wikipedia link", value=True)

must_langs = st.sidebar.text_input(
    "Must already have label in…  (comma-list, e.g. fr, zh-hant)",
    value=""
).strip()
must_langs_list = [x.strip() for x in must_langs.split(",") if x.strip()]

search_raw = st.sidebar.text_input(
    "Find label (e.g. en:Jimmu, fr:Jeanne, Amaterasu)", value=""
).strip()

if search_raw:
    if ":" in search_raw:
        search_lang, search_text = [x.strip() for x in search_raw.split(":", 1)]
        if not search_lang: search_lang = "en"
    else:
        search_lang, search_text = "en", search_raw
else:
    search_lang = search_text = None

PAGE_SIZE = st.sidebar.number_input("Rows per page", 10, 500, value=200, step=10)

query = build_query(only_no_en, only_no_wp,
                    must_langs_list,
                    search_lang, search_text)

TOTAL = total_rows(query)
MAX_P = max(0, math.ceil(TOTAL / PAGE_SIZE) - 1)
page  = st.sidebar.number_input("Page #", 0, MAX_P, value=st.session_state.get("page", 0))
st.session_state["page"] = page = int(page)

if st.sidebar.button("⭮ reload page"):
    rerun()

st.write(
    f"### {TOTAL} person(s) match current filters "
    f"— page {page+1}/{MAX_P+1 if TOTAL else 1}"
)

df = fetch_page(query, page, PAGE_SIZE)

# Markdown header
head = [
    "Label (→WD)", "JP-Wikipedia", "Same-as (P460)",
    "All labels", ""                # last col = ↻
]
st.markdown("| " + " | ".join(head) + " |\n| " + " | ".join(["---"]*5) + " |")

for _, r in df.iterrows():
    c = st.columns([3, 3, 3, 6, 1])

    c[0].markdown(f"[{r['Display']}]({r['Wikidata']})")

    c[1].markdown(
        f"[{r['JP_WP_TITLE']}]({r['JP_WP_URL']})"
        if r["JP_WP_URL"] else "—"
    )
    c[2].markdown(r["Same-as"])
    c[3].markdown(r["All labels"])

    if c[4].button("↻", key=r["Q-ID"]):
        try:
            patch_entity(r["Q-ID"])
            time.sleep(0.3)
            rerun()
        except Exception as e:
            st.error(f"{r['Q-ID']}: {e}")

st.caption(
    "*Label column follows priority **English → mul → Japanese**.*  "
    "Use the search box like **`en:Jimmu`**, **`fr:Jeanne`**, or just "
    "**`Benzaiten`** (defaults to EN) to find rows quickly.  "
    "Rows vanish automatically once they gain an EN label or EN-wiki link "
    "depending on your toggles."
)
