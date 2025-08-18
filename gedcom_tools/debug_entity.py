#!/usr/bin/env python3
"""
DEBUG ENTITY PROPERTIES

Quick script to check what properties an entity has
"""

import requests
import json

def get_entity_data(qid):
    """Get entity data"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Debug Entity/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
        })
        
        response = session.get('https://evolutionism.miraheze.org/w/api.php', params={
            'action': 'wbgetentities',
            'ids': qid,
            'format': 'json'
        }, timeout=30)
        
        data = response.json()
        if 'entities' in data and qid in data['entities']:
            entity = data['entities'][qid]
            if 'missing' not in entity:
                return entity
        return None
    except Exception as e:
        print(f"Error getting entity {qid}: {e}")
        return None

def debug_entity(qid):
    """Debug entity properties"""
    print(f"=== DEBUGGING {qid} ===")
    
    entity = get_entity_data(qid)
    if not entity:
        print("Entity not found!")
        return
        
    print(f"Labels: {list(entity.get('labels', {}).keys())}")
    print(f"Descriptions: {list(entity.get('descriptions', {}).keys())}")
    print(f"Aliases: {list(entity.get('aliases', {}).keys())}")
    
    # Show aliases content
    aliases = entity.get('aliases', {})
    if aliases:
        for lang, alias_list in aliases.items():
            print(f"  {lang} aliases: {[alias['value'] for alias in alias_list[:3]]}")  # Show first 3
    
    claims = entity.get('claims', {})
    print(f"Properties found: {list(claims.keys())}")
    
    for prop, claim_list in claims.items():
        print(f"\n{prop}: {len(claim_list)} claims")
        for i, claim in enumerate(claim_list[:3]):  # Show first 3 claims
            if 'datavalue' in claim['mainsnak']:
                value = claim['mainsnak']['datavalue']['value']
                print(f"  [{i}] {value}")
            else:
                print(f"  [{i}] {claim['mainsnak']['snaktype']}")

if __name__ == "__main__":
    debug_entity("Q115039")