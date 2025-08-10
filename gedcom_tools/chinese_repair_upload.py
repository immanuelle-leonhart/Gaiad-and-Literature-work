#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chinese GEDCOM Repair + Upload for Wikibase
-------------------------------------------
- Two-pass flow: (1) ensure/repair existing mapped items, (2) create missing items, (3) link relationships.
- Safe to stop/restart: mappings are persisted as JSON after each creation.
- Adds Chinese labels (zh) when available, plus English fallbacks.
- Creates missing properties if not found (mother/father/spouse/REFN/names/dates/sex/etc.).
- Optional: add instance-of=human if --human-qid is provided.
- Designed for Wikibase w/ API (Query Service optional; not required).

Usage example:
  python3 chinese_repair_upload_full.py \
      --api-url https://evolutionism.miraheze.org/w/api.php \
      --gedcom ./people.ged \
      --mapping-file ./cn_individual_mappings.json \
      --prop-file ./cn_property_mappings.json \
      --username YOUR_USER --password YOUR_PASS \
      --human-qid Q5

If you prefer env vars for credentials:
  export WIKIBASE_USERNAME=YOUR_USER
  export WIKIBASE_PASSWORD=YOUR_PASS
  python3 chinese_repair_upload_full.py --api-url ... --gedcom ...

Author: ChatGPT (GPT-5 Thinking)
License: MIT
"""
import os
import re
import json
import time
import argparse
import requests
from collections import defaultdict

# -----------------------------
# Simple GEDCOM parser (INDI/FAM)
# -----------------------------

def parse_gedcom(path):
    """
    Very lightweight GEDCOM parser tailored to fields we need:
    - Individuals: @I...@ (NAME, GIVN, SURN, SEX, REFN, BIRT/DATE, DEAT/DATE, FAMS, FAMC)
    - Families: @F...@ (HUSB, WIFE, CHIL)
    Returns:
      individuals: dict[xref] = {
        'xref': '@I1@', 'full_name': str, 'given_name': str|None, 'surname': str|None,
        'sex': 'M'|'F'|'U'|None,
        'refns': [str, ...],
        'dates': {'birth_date': str|None, 'death_date': str|None},
        'fams': [fam_id, ...],   # as spouse
        'famc': [fam_id, ...],   # as child (usually at most 1, but keep list)
      }
      families: dict[xref] = {'xref': '@F1@', 'husb': '@I..@'|None, 'wife': '@I..@'|None, 'chil': ['@I..@', ...]}
    """
    individuals = {}
    families = {}
    current_ind = None
    current_fam = None
    in_birth = False
    in_death = False

    def clean_value(s):
        # Remove leading/trailing spaces; keep content
        return s.strip()

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for raw in f:
            line = raw.rstrip('\n')

            # Match GEDCOM level/tag/value
            m = re.match(r'^(\d+)\s+(@[^@]+@)?\s*([A-Z0-9_]+)?\s*(.*)$', line)
            if not m:
                continue
            lvl, xref, tag, val = m.groups()
            lvl = int(lvl)
            val = val.strip()

            # New record
            if lvl == 0:
                in_birth = in_death = False
                if xref and tag == 'INDI':
                    current_ind = xref
                    current_fam = None
                    individuals[current_ind] = {
                        'xref': current_ind,
                        'full_name': None,
                        'given_name': None,
                        'surname': None,
                        'sex': None,
                        'refns': [],
                        'dates': {'birth_date': None, 'death_date': None},
                        'fams': [],
                        'famc': [],
                    }
                elif xref and tag == 'FAM':
                    current_fam = xref
                    current_ind = None
                    families[current_fam] = {'xref': current_fam, 'husb': None, 'wife': None, 'chil': []}
                else:
                    current_ind = None
                    current_fam = None
                continue

            # Inside individual
            if current_ind and current_ind in individuals:
                ind = individuals[current_ind]
                if lvl == 1 and tag == 'NAME':
                    # Typically "GIVEN /SURNAME/"
                    ind['full_name'] = clean_value(val) if val else ind['full_name']
                elif lvl == 1 and tag == 'GIVN':
                    ind['given_name'] = clean_value(val)
                elif lvl == 1 and tag == 'SURN':
                    ind['surname'] = clean_value(val)
                elif lvl == 1 and tag == 'SEX':
                    v = val.upper()[:1] if val else None
                    ind['sex'] = v if v in ('M','F','U') else v
                elif lvl == 1 and tag == 'REFN':
                    if val:
                        ind['refns'].append(clean_value(val))
                elif lvl == 1 and tag == 'BIRT':
                    in_birth = True
                    in_death = False
                elif lvl == 1 and tag == 'DEAT':
                    in_birth = False
                    in_death = True
                elif lvl == 2 and tag == 'DATE':
                    if in_birth:
                        ind['dates']['birth_date'] = clean_value(val)
                    elif in_death:
                        ind['dates']['death_date'] = clean_value(val)
                elif lvl == 1 and tag == 'FAMS':
                    if val:
                        ind['fams'].append(val)
                elif lvl == 1 and tag == 'FAMC':
                    if val:
                        ind['famc'].append(val)
                continue

            # Inside family
            if current_fam and current_fam in families:
                fam = families[current_fam]
                if lvl == 1 and tag in ('HUSB','WIFE'):
                    fam['husb' if tag == 'HUSB' else 'wife'] = val if val else None
                elif lvl == 1 and tag == 'CHIL':
                    if val:
                        fam['chil'].append(val)
                continue

    return individuals, families

# -----------------------------
# Wikibase client
# -----------------------------

class WikibaseChineseUploader:
    def __init__(self, api_url, username=None, password=None,
                 mapping_file='cn_individual_mappings.json',
                 prop_file='cn_property_mappings.json',
                 human_qid=None, lang_label='zh'):
        self.api_url = api_url.rstrip('?')
        self.username = username or os.getenv('WIKIBASE_USERNAME')
        self.password = password or os.getenv('WIKIBASE_PASSWORD')
        self.human_qid = human_qid  # e.g., 'Q5' if exists; else None
        self.lang_label = lang_label  # 'zh' by default

        self.session = requests.Session()
        self.csrf_token = None

        self.individual_mappings_path = mapping_file
        self.property_mappings_path = prop_file
        self.individual_mappings = {}   # GEDCOM @I@ -> QID
        self.property_mappings = {}     # our key -> PID

        self.needed_properties = {
            'gedcom_refn': 'GEDCOM REFN',
            'full_name': 'full name',
            'given_name': 'given name',
            'surname': 'surname',
            'sex': 'sex',
            'birth_date': 'birth date',
            'death_date': 'death date',
            'instance_of': 'instance of',
            'mother': 'mother',
            'father': 'father',
            'spouse': 'spouse',
            # 'child': 'child',  # Optional: can add if you want reciprocal
        }

        # cache of entity json to reduce API calls during relationship linking
        self.entity_cache = {}

    # ---------- utils ----------
    def load_json(self, path, default):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return default

    def save_json(self, path, data):
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)

    # ---------- auth ----------
    def login(self):
        if not self.username or not self.password:
            raise RuntimeError("Username/password required (env or args).")
        # Step 1: get login token
        r1 = self.session.get(self.api_url, params={
            'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'
        }).json()
        login_token = r1.get('query', {}).get('tokens', {}).get('logintoken')
        if not login_token:
            raise RuntimeError("Could not obtain login token.")
        # Step 2: login
        r2 = self.session.post(self.api_url, data={
            'action': 'login',
            'lgname': self.username,
            'lgpassword': self.password,
            'lgtoken': login_token,
            'format': 'json'
        }).json()
        if r2.get('login', {}).get('result') != 'Success':
            raise RuntimeError(f"Login failed: {r2}")
        # Step 3: csrf token
        r3 = self.session.get(self.api_url, params={
            'action': 'query',
            'meta': 'tokens',
            'format': 'json'
        }).json()
        self.csrf_token = r3.get('query', {}).get('tokens', {}).get('csrftoken')
        if not self.csrf_token:
            raise RuntimeError("Could not obtain CSRF token.")
        print("Logged in and CSRF token acquired.")

    # ---------- property helpers ----------
    def create_property(self, prop_name, prop_label):
        datatype = 'string'
        if prop_name in ['mother','father','spouse','child','instance_of']:
            datatype = 'wikibase-item'
        payload = {
            'labels': {
                'en': {'language': 'en', 'value': prop_label}
            },
            'descriptions': {
                'en': {'language': 'en', 'value': f'Property for {prop_label} (auto-created)'}
            },
            'datatype': datatype
        }
        r = self.session.post(self.api_url, data={
            'action': 'wbeditentity',
            'new': 'property',
            'data': json.dumps(payload),
            'format': 'json',
            'token': self.csrf_token
        }).json()
        pid = r.get('entity', {}).get('id')
        if pid:
            print(f"Created property {pid}: {prop_label}")
        else:
            print(f"Failed to create property for {prop_label}: {r}")
        return pid

    def ensure_properties_exist(self):
        print("Ensuring required properties exist...")
        for key, label in self.needed_properties.items():
            if key in self.property_mappings and self.property_mappings[key]:
                continue
            # search existing properties by label (en)
            sr = self.session.get(self.api_url, params={
                'action': 'wbsearchentities',
                'search': label,
                'language': 'en',
                'type': 'property',
                'limit': 10,
                'format': 'json'
            }).json()
            found = None
            for res in sr.get('search', []):
                # exact label match preferred
                if res.get('label', '').lower() == label.lower():
                    found = res['id']
                    break
            if not found:
                found = self.create_property(key, label)
            if found:
                self.property_mappings[key] = found
                self.save_json(self.property_mappings_path, self.property_mappings)
            time.sleep(0.2)

    # ---------- entity helpers ----------
    def get_entity(self, qid, use_cache=True):
        if use_cache and qid in self.entity_cache:
            return self.entity_cache[qid]
        r = self.session.get(self.api_url, params={
            'action': 'wbgetentities',
            'ids': qid,
            'format': 'json'
        }).json()
        ent = r.get('entities', {}).get(qid)
        if ent and use_cache:
            self.entity_cache[qid] = ent
        return ent

    def has_statement(self, qid, pid, value, value_type='string'):
        ent = self.get_entity(qid, use_cache=True)
        if not ent:
            return False
        claims = ent.get('claims', {}).get(pid, [])
        if not claims:
            return False
        if value_type == 'string':
            for c in claims:
                dv = c.get('mainsnak', {}).get('datavalue', {})
                if dv.get('type') == 'string' and dv.get('value') == str(value):
                    return True
        elif value_type == 'item':
            target_nid = int(value[1:]) if isinstance(value, str) and value.startswith('Q') else int(value)
            for c in claims:
                dv = c.get('mainsnak', {}).get('datavalue', {})
                if dv.get('type') == 'wikibase-entityid':
                    v = dv.get('value', {})
                    if v.get('entity-type') == 'item' and v.get('numeric-id') == target_nid:
                        return True
        return False

    def add_statement_to_item(self, qid, pid, value, value_type='string'):
        try:
            if not pid or not value:
                return False
            # avoid duplicates
            if self.has_statement(qid, pid, value, value_type=value_type):
                return True

            if value_type == 'string':
                datavalue = {'value': str(value), 'type': 'string'}
            elif value_type == 'item':
                numeric_id = int(value[1:]) if isinstance(value, str) and value.startswith('Q') else int(value)
                datavalue = {'value': {'entity-type': 'item', 'numeric-id': numeric_id},
                             'type': 'wikibase-entityid'}
            else:
                datavalue = {'value': str(value), 'type': 'string'}

            statement_data = {
                'claims': [{
                    'mainsnak': {
                        'snaktype': 'value',
                        'property': pid,
                        'datavalue': datavalue
                    },
                    'type': 'statement'
                }]
            }
            r = self.session.post(self.api_url, data={
                'action': 'wbeditentity',
                'id': qid,
                'data': json.dumps(statement_data),
                'format': 'json',
                'token': self.csrf_token
            }).json()
            ok = 'entity' in r
            if ok:
                # refresh cache
                if qid in self.entity_cache:
                    del self.entity_cache[qid]
            else:
                print(f"add_statement_to_item failed for {qid}/{pid}: {r}")
            return ok
        except Exception as e:
            print(f"add_statement_to_item error on {qid}: {e}")
            return False

    def set_labels(self, qid, labels=None, aliases=None, descriptions=None):
        payload = {}
        if labels:
            payload['labels'] = {lang: {'language': lang, 'value': val}
                                 for lang, val in labels.items() if val}
        if aliases:
            payload['aliases'] = {lang: [{'language': lang, 'value': v} for v in vals if v]
                                  for lang, vals in aliases.items() if vals}
        if descriptions:
            payload['descriptions'] = {lang: {'language': lang, 'value': val}
                                       for lang, val in descriptions.items() if val}
        if not payload:
            return True
        r = self.session.post(self.api_url, data={
            'action': 'wbeditentity',
            'id': qid,
            'data': json.dumps(payload),
            'format': 'json',
            'token': self.csrf_token
        }).json()
        ok = 'entity' in r
        if not ok:
            print(f"set_labels failed for {qid}: {r}")
        else:
            if qid in self.entity_cache:
                del self.entity_cache[qid]
        return ok

    def create_item(self, labels=None, descriptions=None):
        data = {}
        if labels:
            data['labels'] = {lang: {'language': lang, 'value': val}
                              for lang, val in labels.items() if val}
        if descriptions:
            data['descriptions'] = {lang: {'language': lang, 'value': val}
                                    for lang, val in descriptions.items() if val}
        r = self.session.post(self.api_url, data={
            'action': 'wbeditentity',
            'new': 'item',
            'data': json.dumps(data),
            'format': 'json',
            'token': self.csrf_token
        }).json()
        qid = r.get('entity', {}).get('id')
        if not qid:
            print(f"create_item failed: {r}")
        return qid

    # ---------- enrichment ----------
    def enrich_person_item(self, qid, ind):
        """Add statements like REFN, names, dates, sex (+ instance_of if configured)."""
        # instance of: only if provided
        if self.human_qid and self.property_mappings.get('instance_of'):
            self.add_statement_to_item(qid, self.property_mappings['instance_of'],
                                       self.human_qid, 'item')

        # REFN(s)
        if ind.get('refns') and self.property_mappings.get('gedcom_refn'):
            for rfn in ind['refns']:
                self.add_statement_to_item(qid, self.property_mappings['gedcom_refn'], rfn, 'string')

        # names
        if ind.get('full_name') and self.property_mappings.get('full_name'):
            self.add_statement_to_item(qid, self.property_mappings['full_name'], ind['full_name'], 'string')
        if ind.get('given_name') and self.property_mappings.get('given_name'):
            self.add_statement_to_item(qid, self.property_mappings['given_name'], ind['given_name'], 'string')
        if ind.get('surname') and self.property_mappings.get('surname'):
            self.add_statement_to_item(qid, self.property_mappings['surname'], ind['surname'], 'string')

        # sex
        if ind.get('sex') and self.property_mappings.get('sex'):
            self.add_statement_to_item(qid, self.property_mappings['sex'], ind['sex'], 'string')

        # dates
        for df_key in ('birth_date', 'death_date'):
            if self.property_mappings.get(df_key) and ind.get('dates', {}).get(df_key):
                self.add_statement_to_item(qid, self.property_mappings[df_key], ind['dates'][df_key], 'string')

    # ---------- repair phase ----------
    def repair_existing_items(self, individuals_data):
        print("Repairing already-mapped items (enriching statements/labels)...")
        for gid, qid in list(self.individual_mappings.items()):
            ind = individuals_data.get(gid)
            if not ind:
                continue
            # labels: prefer Chinese if present; otherwise use full_name as both en/zh
            fullname = ind.get('full_name') or ''
            labels = {}
            if fullname:
                labels['en'] = fullname
                labels[self.lang_label] = fullname
            if labels:
                self.set_labels(qid, labels=labels)
            self.enrich_person_item(qid, ind)
            time.sleep(0.05)

    # ---------- creation phase ----------
    def create_or_get_person(self, ind):
        gid = ind['xref']
        if gid in self.individual_mappings and self.individual_mappings[gid]:
            return self.individual_mappings[gid]

        # Prepare initial labels/descriptions
        fullname = ind.get('full_name') or ''
        labels = {}
        if fullname:
            labels['en'] = fullname
            labels[self.lang_label] = fullname
        desc = {'en': 'Person (imported from GEDCOM)', self.lang_label: '人物（来自 GEDCOM 导入）'}

        qid = self.create_item(labels=labels, descriptions=desc)
        if not qid:
            raise RuntimeError("Failed to create item for {}".format(fullname or gid))

        # persist mapping immediately (safe resume)
        self.individual_mappings[gid] = qid
        self.save_json(self.individual_mappings_path, self.individual_mappings)

        # Enrich with statements
        self.enrich_person_item(qid, ind)
        return qid

    # ---------- relationship linking ----------
    def link_relationships(self, individuals, families):
        print("Linking relationships (mother/father/spouse)...")
        pid_mother = self.property_mappings.get('mother')
        pid_father = self.property_mappings.get('father')
        pid_spouse = self.property_mappings.get('spouse')
        if not any([pid_mother, pid_father, pid_spouse]):
            print("Relationship properties missing; skipping linking.")
            return

        # For each family: add spouse<->spouse, and child->mother/father
        for fam_id, fam in families.items():
            husb = fam.get('husb')
            wife = fam.get('wife')
            chil = fam.get('chil', [])

            q_husb = self.individual_mappings.get(husb) if husb else None
            q_wife = self.individual_mappings.get(wife) if wife else None

            # spouses (both directions)
            if pid_spouse and q_husb and q_wife:
                self.add_statement_to_item(q_husb, pid_spouse, q_wife, 'item')
                self.add_statement_to_item(q_wife, pid_spouse, q_husb, 'item')

            # children (mother/father on child)
            for c in chil:
                q_child = self.individual_mappings.get(c)
                if not q_child:
                    continue
                if pid_father and q_husb:
                    self.add_statement_to_item(q_child, pid_father, q_husb, 'item')
                if pid_mother and q_wife:
                    self.add_statement_to_item(q_child, pid_mother, q_wife, 'item')

            time.sleep(0.02)

    # ---------- driver ----------
    def run(self, gedcom_path):
        # load persisted maps
        self.individual_mappings = self.load_json(self.individual_mappings_path, {})
        self.property_mappings = self.load_json(self.property_mappings_path, {})

        self.login()
        self.ensure_properties_exist()

        individuals, families = parse_gedcom(gedcom_path)
        print(f"Parsed GEDCOM: {len(individuals)} individuals, {len(families)} families.")

        # Repair pass on already-mapped items
        if self.individual_mappings:
            self.repair_existing_items(individuals)

        # Creation pass
        created = 0
        for gid, ind in individuals.items():
            if gid in self.individual_mappings and self.individual_mappings[gid]:
                continue
            self.create_or_get_person(ind)
            created += 1
            if created % 20 == 0:
                print(f"Created {created} items so far...")
            time.sleep(0.05)
        print(f"Creation complete. Newly created: {created}")

        # Relationship linking (pass B)
        self.link_relationships(individuals, families)

        # Save final maps
        self.save_json(self.individual_mappings_path, self.individual_mappings)
        self.save_json(self.property_mappings_path, self.property_mappings)
        print("All done.")
        print(f"Individuals mapped: {len(self.individual_mappings)}")
        print(f"Properties mapped: {len(self.property_mappings)}")


def main():
    ap = argparse.ArgumentParser(description="Chinese GEDCOM Repair+Upload for Wikibase")
    ap.add_argument('--api-url', required=True, help='Wikibase API endpoint, e.g. https://example.org/w/api.php')
    ap.add_argument('--gedcom', required=True, help='Path to GEDCOM file')
    ap.add_argument('--mapping-file', default='cn_individual_mappings.json', help='Path to save/load GEDCOM->QID mapping')
    ap.add_argument('--prop-file', default='cn_property_mappings.json', help='Path to save/load property mappings')
    ap.add_argument('--username', help='Wikibase username (or set env WIKIBASE_USERNAME)')
    ap.add_argument('--password', help='Wikibase password (or set env WIKIBASE_PASSWORD)')
    ap.add_argument('--human-qid', help='QID for "human" to use in instance of (optional)')
    ap.add_argument('--lang', default='zh', help='Language code for labels (default: zh)')

    args = ap.parse_args()

    uploader = WikibaseChineseUploader(
        api_url=args.api_url,
        username=args.username,
        password=args.password,
        mapping_file=args.mapping_file,
        prop_file=args.prop_file,
        human_qid=args.human_qid,
        lang_label=args.lang
    )
    uploader.run(args.gedcom)


if __name__ == '__main__':
    main()
