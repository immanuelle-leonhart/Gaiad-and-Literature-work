#!/usr/bin/env python3
"""
Fix Monolingualtext Format for Wikibase API

The issue is that the Wikibase API expects a very specific JSON structure for labels and descriptions.
Based on the API documentation and error messages, the correct format should be:

For labels/descriptions in API calls:
{
    "labels": {
        "en": {
            "language": "en", 
            "value": "The actual text"
        }
    }
}

But for claims/properties, entity references need this format:
{
    "claims": {
        "P20": [{
            "mainsnak": {
                "snaktype": "value",
                "property": "P20",
                "datavalue": {
                    "value": {
                        "entity-type": "item",
                        "numeric-id": 123,
                        "id": "Q123"
                    },
                    "type": "wikibase-entityid"
                }
            },
            "type": "statement",
            "rank": "normal"
        }]
    }
}

This script creates a test entity with the EXACT correct format.
"""

import pymongo
import requests
import json
import sys

# Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "gaiad_processing_db"
WIKI_URL = "https://evolutionism.miraheze.org"
API_ENDPOINT = f"{WIKI_URL}/w/api.php"

def get_test_entity():
    """Get a test entity from MongoDB"""
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db['entities']
    
    # Find entity with both labels and some properties
    for entity in collection.find().limit(100):
        properties = entity.get('properties', {})
        labels = entity.get('labels', {})
        
        # Look for entity with P61 (external ID) and labels
        if 'P61' in properties and labels:
            client.close()
            return entity
    
    client.close()
    return None

def create_perfect_wikibase_data(entity):
    """Create the EXACT format that Wikibase API expects"""
    qid = entity['qid']
    
    # Start with empty structure
    wikibase_data = {}
    
    # Labels - EXACT monolingualtext format
    labels = entity.get('labels', {})
    if labels:
        wikibase_data['labels'] = {}
        for lang, text in labels.items():
            if isinstance(text, str) and text.strip():
                wikibase_data['labels'][lang] = {
                    "language": lang,
                    "value": text.strip()
                }
    
    # Descriptions - same exact format
    descriptions = entity.get('descriptions', {})
    if descriptions:
        wikibase_data['descriptions'] = {}
        for lang, text in descriptions.items():
            if isinstance(text, str) and text.strip():
                wikibase_data['descriptions'][lang] = {
                    "language": lang,
                    "value": text.strip()
                }
    
    # Claims - EXACT Wikibase API claim structure
    properties = entity.get('properties', {})
    if properties:
        wikibase_data['claims'] = {}
        
        for prop_id, claims in properties.items():
            if prop_id == 'redirect':
                continue
                
            wikibase_claims = []
            for claim in claims:
                claim_value = claim.get('value')
                claim_type = claim.get('type', 'string')
                
                if not claim_value:
                    continue
                
                # Build the exact claim structure
                wikibase_claim = {
                    "mainsnak": {
                        "snaktype": "value",
                        "property": prop_id
                    },
                    "type": "statement",
                    "rank": "normal"
                }
                
                # Handle different data types with EXACT Wikibase formats
                if claim_type == 'external-id':
                    # External identifiers like P61, P62, P63
                    wikibase_claim['mainsnak']['datavalue'] = {
                        "value": str(claim_value),
                        "type": "string"
                    }
                    wikibase_claim['mainsnak']['datatype'] = 'external-id'
                    
                elif claim_type == 'wikibase-item':
                    # Entity references like P20, P42, P47, P48
                    if isinstance(claim_value, str) and claim_value.startswith('Q'):
                        try:
                            numeric_id = int(claim_value[1:])
                            wikibase_claim['mainsnak']['datavalue'] = {
                                "value": {
                                    "entity-type": "item",
                                    "numeric-id": numeric_id,
                                    "id": claim_value
                                },
                                "type": "wikibase-entityid"
                            }
                            wikibase_claim['mainsnak']['datatype'] = 'wikibase-item'
                        except (ValueError, IndexError):
                            continue
                    else:
                        continue
                        
                elif claim_type == 'time':
                    # Date properties P56, P57
                    if isinstance(claim_value, dict):
                        wikibase_claim['mainsnak']['datavalue'] = {
                            "value": claim_value,
                            "type": "time"
                        }
                    else:
                        # Try to parse as simple date
                        wikibase_claim['mainsnak']['datavalue'] = {
                            "value": {
                                "time": str(claim_value),
                                "timezone": 0,
                                "before": 0,
                                "after": 0,
                                "precision": 11,
                                "calendarmodel": "http://www.wikidata.org/entity/Q1985727"
                            },
                            "type": "time"
                        }
                    wikibase_claim['mainsnak']['datatype'] = 'time'
                    
                else:
                    # String properties (default)
                    wikibase_claim['mainsnak']['datavalue'] = {
                        "value": str(claim_value),
                        "type": "string"
                    }
                    wikibase_claim['mainsnak']['datatype'] = 'string'
                
                wikibase_claims.append(wikibase_claim)
            
            if wikibase_claims:
                wikibase_data['claims'][prop_id] = wikibase_claims
    
    return wikibase_data

def test_wikibase_api_format(username, password):
    """Test the exact Wikibase API format"""
    print("=== TESTING PERFECT WIKIBASE API FORMAT ===")
    print()
    
    # Get test entity
    entity = get_test_entity()
    if not entity:
        print("ERROR: No suitable test entity found")
        return False
    
    qid = entity['qid']
    print(f"Testing with entity {qid}")
    
    # Create session and login
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Gaiad Genealogy Format Test/1.0'
    })
    
    try:
        # Get login token
        response = session.post(API_ENDPOINT, data={
            'action': 'query',
            'meta': 'tokens',
            'type': 'login', 
            'format': 'json'
        })
        login_token = response.json()['query']['tokens']['logintoken']
        
        # Login
        response = session.post(API_ENDPOINT, data={
            'action': 'login',
            'lgname': username,
            'lgpassword': password,
            'lgtoken': login_token,
            'format': 'json'
        })
        
        result = response.json()
        if result['login']['result'] != 'Success':
            print(f"ERROR: Login failed: {result}")
            return False
        
        print("SUCCESS: Successfully logged in")
        
        # Get CSRF token
        response = session.post(API_ENDPOINT, data={
            'action': 'query',
            'meta': 'tokens',
            'type': 'csrf',
            'format': 'json'
        })
        csrf_token = response.json()['query']['tokens']['csrftoken']
        
        # Create perfect Wikibase data
        wikibase_data = create_perfect_wikibase_data(entity)
        
        print()
        print("PERFECT WIKIBASE DATA STRUCTURE:")
        print("=" * 50)
        
        # Show the exact structure we're sending
        if 'labels' in wikibase_data and wikibase_data['labels']:
            first_label_key = list(wikibase_data['labels'].keys())[0]
            first_label = wikibase_data['labels'][first_label_key]
            print(f"Label format: {json.dumps(first_label, indent=2)}")
        
        if 'claims' in wikibase_data and wikibase_data['claims']:
            first_claim_key = list(wikibase_data['claims'].keys())[0]
            first_claim = wikibase_data['claims'][first_claim_key][0]
            print(f"Claim format ({first_claim_key}): {json.dumps(first_claim, indent=2)}")
        
        print("=" * 50)
        print()
        
        # Test with minimal data first (just labels)
        minimal_data = {}
        if 'labels' in wikibase_data:
            minimal_data['labels'] = wikibase_data['labels']
        
        print("Testing with MINIMAL data (labels only)...")
        
        # Try to create entity
        response = session.post(API_ENDPOINT, data={
            'action': 'wbeditentity',
            'new': 'item',
            'data': json.dumps(minimal_data),
            'token': csrf_token,
            'format': 'json'
        })
        
        result = response.json()
        print(f"API Response: {json.dumps(result, indent=2)}")
        
        if 'entity' in result:
            created_qid = result['entity']['id']
            print(f"SUCCESS: Created entity {created_qid}")
            print("Monolingualtext format is CORRECT!")
            return True
        else:
            error_info = result.get('error', {})
            print(f"FAILED: {error_info}")
            
            # Analyze the specific error
            error_msg = error_info.get('info', '')
            if 'monolingualtext' in error_msg.lower():
                print()
                print("ANALYSIS: Still has monolingualtext format error")
                print("This suggests the API expects a different structure")
            elif 'wikibase-item' in error_msg.lower():
                print()
                print("ANALYSIS: Wikibase-item format error")
                print("This suggests entity references need different structure")
            
            return False
    
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python fix_monolingualtext_format.py <username> <password>")
        return False
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    success = test_wikibase_api_format(username, password)
    
    if success:
        print()
        print("FORMAT IS PERFECT!")
        print("Ready to proceed with full import using this exact format.")
    else:
        print()
        print("FORMAT NEEDS MORE WORK")
        print("Need to analyze the API response to fix remaining issues.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)