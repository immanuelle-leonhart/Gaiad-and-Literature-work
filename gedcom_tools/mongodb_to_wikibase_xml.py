#!/usr/bin/env python3
"""
MongoDB → Wikibase XML Exporter (fixed)

Complete drop‑in replacement for your exporter. Key fixes:
- Every statement gets a **valid GUID**: QID$UUIDv4
- `mainsnak.datatype` is set for every claim (no more blank widgets)
- Property entities include top‑level `datatype`
- No <timestamp> written in revisions (let MW/Wikibase assign)
- Minor hardening + consistent defaults
"""

from __future__ import annotations
import json
import os
import time
import re
import uuid
import pymongo
import xml.etree.ElementTree as ET

# ---- Config ----
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
COLLECTION_NAME = "entities"

OUTPUT_DIR = os.environ.get("WIKIBASE_EXPORT_DIR", "wikibase_export")
CHUNK_SIZE = 606  # ~240 parts for big sets
XML_NAMESPACE = "http://www.mediawiki.org/xml/export-0.11/"


# ---- Helpers ----
_GUID_RE = re.compile(r"^Q[1-9]\d*\$[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$")


def _is_valid_guid_for(qid: str, guid: str | None) -> bool:
    if not guid:
        return False
    g = guid.strip().upper()
    return bool(_GUID_RE.match(g)) and g.startswith(f"{qid}$")


def _new_guid(qid: str) -> str:
    return f"{qid}${str(uuid.uuid4()).upper()}"


def _datatype_for_claim_type(claim_type: str | None) -> str:
    t = (claim_type or "string").lower()
    mapping = {
        "wikibase-item": "wikibase-item",
        "wikibase-entityid": "wikibase-item",
        "monolingualtext": "monolingualtext",
        "external-id": "external-id",
        "time": "time",
        "quantity": "quantity",
        "url": "url",
        "string": "string",
    }
    return mapping.get(t, "string")


class WikibaseXMLExporter:
    def __init__(self, mongo_uri: str = MONGO_URI, output_dir: str = OUTPUT_DIR):
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client[DATABASE_NAME]
        self.collection = self.db[COLLECTION_NAME]
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.stats = {
            "entities_processed": 0,
            "entities_exported": 0,
            "redirects_seen": 0,
            "files_created": 0,
            "start_time": time.time(),
        }
        print(f"Connected: {DATABASE_NAME}.{COLLECTION_NAME}")
        print(f"Writing to: {os.path.abspath(self.output_dir)}")

    # ----------------- JSON shaping -----------------
    def _copy_ldal(self, entity: dict, out: dict) -> None:
        # labels
        labels = entity.get("labels") or {}
        out_labels = {}
        for lang, val in labels.items():
            if isinstance(val, dict) and {"language", "value"} <= set(val.keys()):
                out_labels[lang] = {"language": val["language"], "value": val["value"]}
            elif isinstance(val, str):
                out_labels[lang] = {"language": lang, "value": val}
        out["labels"] = out_labels
        # descriptions
        descs = entity.get("descriptions") or {}
        out_descs = {}
        for lang, val in descs.items():
            if isinstance(val, dict) and {"language", "value"} <= set(val.keys()):
                out_descs[lang] = {"language": val["language"], "value": val["value"]}
            elif isinstance(val, str):
                out_descs[lang] = {"language": lang, "value": val}
        out["descriptions"] = out_descs
        # aliases
        aliases = entity.get("aliases") or {}
        out_aliases = {}
        for lang, vals in aliases.items():
            norm = []
            if isinstance(vals, list):
                for v in vals:
                    if isinstance(v, dict) and {"language", "value"} <= set(v.keys()):
                        norm.append({"language": v["language"], "value": v["value"]})
                    elif isinstance(v, str):
                        norm.append({"language": lang, "value": v})
            out_aliases[lang] = norm
        out["aliases"] = out_aliases

    def sanitize_wikibase_json(self, wikibase_entity: dict) -> dict:
        # Remove snak hashes (Wikibase recomputes); keep valid GUIDs
        for claims in wikibase_entity.get("claims", {}).values():
            for claim in claims:
                ms = claim.get("mainsnak") or {}
                ms.pop("hash", None)
                for qlist in (claim.get("qualifiers") or {}).values():
                    for snak in qlist:
                        snak.pop("hash", None)
                for ref in claim.get("references") or []:
                    ref.pop("hash", None)
                    for rlist in (ref.get("snaks") or {}).values():
                        for snak in rlist:
                            snak.pop("hash", None)
        return wikibase_entity

    def entity_to_wikibase_json(self, entity: dict) -> dict:
        qid = entity["qid"]
        entity_type = entity.get("entity_type") or ("property" if qid.startswith("P") else "item")

        out: dict = {"type": entity_type, "id": qid, "labels": {}, "descriptions": {}, "aliases": {}, "claims": {}}
        self._copy_ldal(entity, out)

        # Property pages must include datatype
        if entity_type == "property":
            out["datatype"] = entity.get("datatype") or entity.get("property_datatype") or "string"

        used_ids: set[str] = set()
        props = entity.get("properties") or {}
        for prop_id, claims in props.items():
            if not claims:
                continue
            wb_claims = []
            for claim in claims:
                ctype = (claim.get("type") or "string").lower()
                cval = claim.get("value")
                raw_id = claim.get("id") or claim.get("claim_id")

                snak_datatype = _datatype_for_claim_type(ctype)
                wb = {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": prop_id,
                        "datatype": snak_datatype,
                        "datavalue": {"type": "string", "value": None},  # will be set below
                    },
                    "type": "statement",
                    "rank": "normal",
                }

                # value shaping
                if snak_datatype == "wikibase-item":
                    # accept dict {id:Q..} or string "Q.."
                    tq = None
                    if isinstance(cval, dict) and "id" in cval:
                        tq = cval["id"]
                    elif isinstance(cval, str) and cval.startswith("Q"):
                        tq = cval
                    if not tq:
                        continue  # skip malformed
                    val = {"entity-type": "item", "id": tq}
                    if tq[1:].isdigit():
                        val["numeric-id"] = int(tq[1:])
                    wb["mainsnak"]["datavalue"] = {"type": "wikibase-entityid", "value": val}

                elif snak_datatype == "monolingualtext":
                    if isinstance(cval, dict) and {"text", "language"} <= set(cval.keys()):
                        wb["mainsnak"]["datavalue"] = {"type": "monolingualtext", "value": {"text": cval["text"], "language": cval["language"]}}
                    else:
                        continue

                elif snak_datatype in ("external-id", "string", "url"):
                    wb["mainsnak"]["datavalue"] = {"type": "string", "value": "" if cval is None else str(cval)}

                elif snak_datatype == "time":
                    if isinstance(cval, dict):
                        wb["mainsnak"]["datavalue"] = {"type": "time", "value": cval}
                    else:
                        wb["mainsnak"]["datavalue"] = {
                            "type": "time",
                            "value": {
                                "time": str(cval),
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                            },
                        }

                elif snak_datatype == "quantity":
                    if isinstance(cval, dict) and "amount" in cval:
                        wb["mainsnak"]["datavalue"] = {"type": "quantity", "value": cval}
                    else:
                        wb["mainsnak"]["datavalue"] = {"type": "string", "value": str(cval)}

                else:
                    wb["mainsnak"]["datavalue"] = {"type": "string", "value": "" if cval is None else str(cval)}

                # ensure a valid, unique GUID on every statement
                if _is_valid_guid_for(qid, raw_id):
                    cid = raw_id.strip().upper()
                else:
                    cid = _new_guid(qid)
                while cid in used_ids:
                    cid = _new_guid(qid)
                used_ids.add(cid)
                wb["id"] = cid

                wb_claims.append(wb)

            if wb_claims:
                out["claims"][prop_id] = wb_claims

        return self.sanitize_wikibase_json(out)

    # ----------------- XML writing -----------------
    def create_xml_header(self) -> ET.Element:
        root = ET.Element("mediawiki")
        root.set("xmlns", XML_NAMESPACE)
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
        root.set("xsi:schemaLocation", f"{XML_NAMESPACE} http://www.mediawiki.org/xml/export-0.11.xsd")
        root.set("version", "0.11")
        root.set("xml:lang", "en")

        siteinfo = ET.SubElement(root, "siteinfo")
        ET.SubElement(siteinfo, "sitename").text = "Gaiad Genealogy Wikibase"
        ET.SubElement(siteinfo, "dbname").text = "gaiad_wikibase"
        ET.SubElement(siteinfo, "base").text = "https://gaiad.example.com/"
        ET.SubElement(siteinfo, "generator").text = "MongoDB→Wikibase Exporter"
        ET.SubElement(siteinfo, "case").text = "first-letter"

        namespaces = ET.SubElement(siteinfo, "namespaces")
        ns0 = ET.SubElement(namespaces, "namespace", key="0", case="first-letter"); ns0.text = ""
        nsi = ET.SubElement(namespaces, "namespace", key="860", case="first-letter"); nsi.text = "Item"
        nsp = ET.SubElement(namespaces, "namespace", key="862", case="first-letter"); nsp.text = "Property"
        return root

    def create_page_element(self, entity: dict, parent: ET.Element) -> ET.Element:
        qid = entity["qid"]
        etype = entity.get("entity_type") or ("property" if qid.startswith("P") else "item")
        props = entity.get("properties") or {}
        is_redirect = "redirect" in props

        title = f"Item:{qid}" if etype == "item" else f"Property:{qid}"
        page = ET.SubElement(parent, "page")
        ET.SubElement(page, "title").text = title
        ET.SubElement(page, "ns").text = "860" if etype == "item" else "862"
        ET.SubElement(page, "id").text = qid[1:] if qid[1:].isdigit() else "0"

        if is_redirect:
            redirect_target = props["redirect"][0]["value"]
            ET.SubElement(page, "redirect").set("title", f"Item:{redirect_target}")
            return page

        rev = ET.SubElement(page, "revision")
        ET.SubElement(rev, "id").text = qid[1:] if qid[1:].isdigit() else "1"
        # NOTE: deliberately no <timestamp> — MW will assign server time
        contrib = ET.SubElement(rev, "contributor")
        ET.SubElement(contrib, "username").text = "Immanuelle"
        ET.SubElement(rev, "comment").text = "Exported from MongoDB"
        ET.SubElement(rev, "model").text = "wikibase-item" if etype == "item" else "wikibase-property"
        ET.SubElement(rev, "format").text = "application/json"

        text = ET.SubElement(rev, "text")
        text.set("bytes", "0")
        text.set("xml:space", "preserve")
        wb_json = self.entity_to_wikibase_json(entity)
        jtxt = json.dumps(wb_json, ensure_ascii=False, separators=(",", ":"))
        text.text = jtxt
        text.set("bytes", str(len(jtxt.encode("utf-8"))))
        return page

    def export_chunk(self, entities: list[dict], chunk_num: int) -> str | None:
        if not entities:
            return None
        fname = f"gaiad_wikibase_export_part_{chunk_num:03d}.xml"
        fpath = os.path.join(self.output_dir, fname)
        print(f"Creating {fname} with {len(entities)} entities…")
        root = self.create_xml_header()
        for e in entities:
            self.create_page_element(e, root)
        tree = ET.ElementTree(root)
        try:
            ET.indent(tree, space="  ", level=0)  # Python 3.9+
        except Exception:
            pass
        with open(fpath, "wb") as f:
            tree.write(f, encoding="utf-8", xml_declaration=True)
        self.stats["files_created"] += 1
        print(f"  OK {fname}")
        return fpath

    def export_all_entities(self) -> None:
        print("=== MongoDB → Wikibase XML Export ===\n")
        total = self.collection.count_documents({})
        redirects = self.collection.count_documents({"properties.redirect": {"$exists": True}})
        print(f"Total entities: {total:,}")
        print(f"Redirect pages: {redirects:,} (included)")
        print(f"Output dir: {os.path.abspath(self.output_dir)}")
        print(f"Chunk size: {CHUNK_SIZE}")
        print()

        chunk, n = [], 1
        for entity in self.collection.find():
            self.stats["entities_processed"] += 1
            if "redirect" in (entity.get("properties") or {}):
                self.stats["redirects_seen"] += 1
            chunk.append(entity)
            self.stats["entities_exported"] += 1
            if len(chunk) >= CHUNK_SIZE:
                self.export_chunk(chunk, n)
                chunk, n = [], n + 1
        if chunk:
            self.export_chunk(chunk, n)

        dur = time.time() - self.stats["start_time"]
        print("\n=== DONE ===")
        print(f"Processed: {self.stats['entities_processed']:,}")
        print(f"Exported:  {self.stats['entities_exported']:,}")
        print(f"Files:     {self.stats['files_created']}")
        print(f"Rate:      {int(self.stats['entities_exported']/max(dur,1))} entities/s")

    def close(self) -> None:
        self.client.close()


def main() -> None:
    exporter = WikibaseXMLExporter()
    try:
        exporter.export_all_entities()
    finally:
        exporter.close()


if __name__ == "__main__":
    main()
