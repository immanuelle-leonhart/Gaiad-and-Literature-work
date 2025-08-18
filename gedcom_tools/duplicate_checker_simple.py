#!/usr/bin/env python3
"""
DUPLICATE CHECKER (Simple version without Unicode)

Reads qid_correspondence.csv and checks for duplications in ID fields.
Safe to run while other scripts are writing to the CSV.
"""

import csv
from collections import defaultdict

def check_duplicates():
    """Check for duplicates in the CSV file"""
    print("Duplicate Checker - Reading qid_correspondence.csv...")
    
    # Dictionaries to track occurrences of each ID type
    evolutionism_qids = defaultdict(list)  # QID -> list of rows
    wikidata_qids = defaultdict(list)      # Wikidata QID -> list of rows
    geni_ids = defaultdict(list)           # Geni ID -> list of rows
    uuids = defaultdict(list)              # UUID -> list of rows
    
    total_rows = 0
    
    try:
        with open('qid_correspondence.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                total_rows += 1
                
                evolutionism_qid = row.get('evolutionism_qid', '').strip()
                wikidata_qid = row.get('wikidata_qid', '').strip()
                geni_id = row.get('geni_id', '').strip()
                uuid = row.get('uuid', '').strip()
                en_label = row.get('en_label', '').strip()
                
                # Track evolutionism QIDs (should all be unique)
                if evolutionism_qid:
                    evolutionism_qids[evolutionism_qid].append((row_num, en_label))
                
                # Track Wikidata QIDs (duplicates might be valid but worth noting)
                if wikidata_qid:
                    wikidata_qids[wikidata_qid].append((row_num, evolutionism_qid, en_label))
                
                # Track Geni IDs (duplicates might indicate issues)
                if geni_id:
                    geni_ids[geni_id].append((row_num, evolutionism_qid, en_label))
                
                # Track UUIDs (should be unique)
                if uuid:
                    uuids[uuid].append((row_num, evolutionism_qid, en_label))
                
                # Progress indicator
                if total_rows % 1000 == 0:
                    print(f"  Processed {total_rows} rows...")
    
    except FileNotFoundError:
        print("ERROR: qid_correspondence.csv not found!")
        return
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        return
    
    print(f"\nCompleted analysis of {total_rows} rows")
    print("=" * 60)
    
    # Check for duplicates in evolutionism QIDs (should never happen)
    evo_duplicates = {qid: rows for qid, rows in evolutionism_qids.items() if len(rows) > 1}
    if evo_duplicates:
        print(f"\nCRITICAL: {len(evo_duplicates)} EVOLUTIONISM QID DUPLICATES FOUND!")
        for qid, rows in evo_duplicates.items():
            print(f"  {qid} appears {len(rows)} times:")
            for row_num, label in rows:
                try:
                    print(f"    Row {row_num}: '{label}'")
                except UnicodeEncodeError:
                    print(f"    Row {row_num}: [Unicode label]")
    else:
        print(f"OK: Evolutionism QIDs: All {len(evolutionism_qids)} are unique")
    
    # Check for duplicates in Wikidata QIDs
    wiki_duplicates = {qid: rows for qid, rows in wikidata_qids.items() if len(rows) > 1}
    if wiki_duplicates:
        print(f"\nWARNING: {len(wiki_duplicates)} WIKIDATA QID DUPLICATES:")
        for qid, rows in sorted(wiki_duplicates.items()):
            print(f"  {qid} appears {len(rows)} times:")
            for row_num, evo_qid, label in rows:
                try:
                    print(f"    Row {row_num}: {evo_qid} '{label}'")
                except UnicodeEncodeError:
                    print(f"    Row {row_num}: {evo_qid} [Unicode label]")
    else:
        print(f"OK: Wikidata QIDs: All {len(wikidata_qids)} are unique")
    
    # Check for duplicates in Geni IDs
    geni_duplicates = {gid: rows for gid, rows in geni_ids.items() if len(rows) > 1}
    if geni_duplicates:
        print(f"\nWARNING: {len(geni_duplicates)} GENI ID DUPLICATES:")
        for gid, rows in sorted(geni_duplicates.items()):
            print(f"  {gid} appears {len(rows)} times:")
            for row_num, evo_qid, label in rows:
                try:
                    print(f"    Row {row_num}: {evo_qid} '{label}'")
                except UnicodeEncodeError:
                    print(f"    Row {row_num}: {evo_qid} [Unicode label]")
    else:
        print(f"OK: Geni IDs: All {len(geni_ids)} are unique")
    
    # Check for duplicates in UUIDs
    uuid_duplicates = {uid: rows for uid, rows in uuids.items() if len(rows) > 1}
    if uuid_duplicates:
        print(f"\nCRITICAL: {len(uuid_duplicates)} UUID DUPLICATES FOUND!")
        for uid, rows in sorted(uuid_duplicates.items()):
            print(f"  {uid} appears {len(rows)} times:")
            for row_num, evo_qid, label in rows:
                try:
                    print(f"    Row {row_num}: {evo_qid} '{label}'")
                except UnicodeEncodeError:
                    print(f"    Row {row_num}: {evo_qid} [Unicode label]")
    else:
        print(f"OK: UUIDs: All {len(uuids)} are unique")
    
    # Summary statistics
    print(f"\n" + "=" * 60)
    print("SUMMARY STATISTICS:")
    print(f"  Total rows: {total_rows}")
    print(f"  Evolutionism QIDs: {len(evolutionism_qids)}")
    print(f"  Wikidata QIDs: {len(wikidata_qids)}")
    print(f"  Geni IDs: {len(geni_ids)}")
    print(f"  UUIDs: {len(uuids)}")
    
    # Calculate entities with no external identifiers
    entities_with_ids = set()
    for qid_list in wikidata_qids.values():
        for _, evo_qid, _ in qid_list:
            entities_with_ids.add(evo_qid)
    for gid_list in geni_ids.values():
        for _, evo_qid, _ in gid_list:
            entities_with_ids.add(evo_qid)
    for uid_list in uuids.values():
        for _, evo_qid, _ in uid_list:
            entities_with_ids.add(evo_qid)
    
    entities_without_ids = len(evolutionism_qids) - len(entities_with_ids)
    print(f"  Entities with external IDs: {len(entities_with_ids)}")
    print(f"  Entities without external IDs: {entities_without_ids}")
    
    # Issue summary
    total_issues = len(evo_duplicates) + len(wiki_duplicates) + len(geni_duplicates) + len(uuid_duplicates)
    if total_issues == 0:
        print(f"\nSUCCESS: NO DUPLICATE ISSUES FOUND!")
    else:
        print(f"\nTOTAL DUPLICATE ISSUES: {total_issues}")
        if evo_duplicates:
            print(f"  CRITICAL evolutionism QID duplicates: {len(evo_duplicates)}")
        if wiki_duplicates:
            print(f"  WARNING Wikidata QID duplicates: {len(wiki_duplicates)}")
        if geni_duplicates:
            print(f"  WARNING Geni ID duplicates: {len(geni_duplicates)}")
        if uuid_duplicates:
            print(f"  CRITICAL UUID duplicates: {len(uuid_duplicates)}")

def main():
    print("=" * 60)
    print("DUPLICATE CHECKER FOR QID_CORRESPONDENCE.CSV")
    print("=" * 60)
    check_duplicates()
    print("=" * 60)

if __name__ == '__main__':
    main()