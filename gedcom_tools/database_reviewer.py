#!/usr/bin/env python3
import requests
import json
import time
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Database Reviewer Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
    })
    retry_strategy = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def login_to_wiki(session):
    token_params = {'action': 'query', 'meta': 'tokens', 'type': 'login', 'format': 'json'}
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=token_params, timeout=30)
    if response.status_code != 200:
        return False
    token_data = response.json()
    login_token = token_data['query']['tokens']['logintoken']
    
    login_data = {'action': 'login', 'lgname': 'Immanuelle', 'lgpassword': '1996ToOmega!', 'lgtoken': login_token, 'format': 'json'}
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=login_data)
    return response.json().get('login', {}).get('result') == 'Success'

def get_csrf_token(session):
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params={'action': 'query', 'meta': 'tokens', 'format': 'json'})
    return response.json()['query']['tokens']['csrftoken']

def get_item_data(session, qid):
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json'
    }
    response = session.get('https://evolutionism.miraheze.org/w/api.php', params=params)
    result = response.json()
    return result.get('entities', {}).get(qid)

def get_wikidata_item(session, qid):
    params = {
        'action': 'wbgetentities',
        'ids': qid,
        'format': 'json',
        'sites': 'wikidata'
    }
    response = session.get('https://www.wikidata.org/w/api.php', params=params)
    result = response.json()
    return result.get('entities', {}).get(qid)

def add_statement(session, qid, property_id, value, value_type, csrf_token):
    if value_type == 'string':
        datavalue = {'value': str(value), 'type': 'string'}
    elif value_type == 'item':
        datavalue = {'value': {'entity-type': 'item', 'numeric-id': int(value[1:])}, 'type': 'wikibase-entityid'}
    
    claim = {
        'mainsnak': {
            'snaktype': 'value',
            'property': property_id,
            'datavalue': datavalue
        },
        'type': 'statement'
    }
    
    params = {
        'action': 'wbcreateclaim',
        'entity': qid,
        'property': property_id,
        'snaktype': 'value',
        'value': json.dumps(datavalue['value']),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def set_label(session, qid, language, label, csrf_token):
    params = {
        'action': 'wbsetlabel',
        'id': qid,
        'language': language,
        'value': label,
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def add_alias(session, qid, language, alias, csrf_token):
    params = {
        'action': 'wbsetaliases',
        'id': qid,
        'language': language,
        'add': alias,
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def set_description(session, qid, language, description, csrf_token):
    params = {
        'action': 'wbsetdescription',
        'id': qid,
        'language': language,
        'value': description,
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def main():
    print("Starting database review for Q1 to Q150000...")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    for i in range(23542, 150001):
        qid = f"Q{i}"
        print(f"Processing {qid}")
        
        try:
            item_data = get_item_data(session, qid)
            if not item_data:
                continue
            
            claims = item_data.get('claims', {})
            
            # Check if item has no properties at all
            if not claims:
                print(f"  Adding as Empty item")
                add_statement(session, qid, 'P39', 'Q33921', 'item', csrf_token)
                time.sleep(1)
                continue
            
            # Process GEDCOM REFN (P41)
            refn_claims = claims.get('P41', [])
            has_refn = False
            
            for claim in refn_claims:
                if claim.get('mainsnak', {}).get('datavalue', {}).get('value'):
                    refn_value = claim['mainsnak']['datavalue']['value']
                    has_refn = True
                    
                    if refn_value.startswith('geni:'):
                        geni_id = refn_value[5:]
                        print(f"  Adding Geni.com profile ID: {geni_id}")
                        add_statement(session, qid, 'P43', geni_id, 'string', csrf_token)
                        print(f"  Adding Geni.com URL")
                        add_statement(session, qid, 'P45', f'https://www.geni.com/profile/index/{geni_id}', 'string', csrf_token)
                    elif refn_value.startswith('Q') and refn_value[1:].isdigit():
                        wikidata_qid = refn_value
                        print(f"  Adding Wikidata ID: {wikidata_qid}")
                        add_statement(session, qid, 'P44', wikidata_qid, 'string', csrf_token)
                        print(f"  Adding Wikidata URL")
                        add_statement(session, qid, 'P45', f'https://www.wikidata.org/wiki/{wikidata_qid}', 'string', csrf_token)
                        
                        # Import from Wikidata
                        print(f"  Importing from Wikidata...")
                        wd_item = get_wikidata_item(session, wikidata_qid)
                        if wd_item:
                            # Move current English label to alias
                            current_label = item_data.get('labels', {}).get('en', {}).get('value')
                            if current_label:
                                add_alias(session, qid, 'en', current_label, csrf_token)
                            
                            # Import labels
                            for lang, label_data in wd_item.get('labels', {}).items():
                                if lang != 'mul':  # Skip mul labels
                                    set_label(session, qid, lang, label_data['value'], csrf_token)
                            
                            # Import descriptions
                            for lang, desc_data in wd_item.get('descriptions', {}).items():
                                set_description(session, qid, lang, desc_data['value'], csrf_token)
                            
                            # Check for Geni.com profile ID (P2600) in Wikidata
                            wd_claims = wd_item.get('claims', {})
                            if 'P2600' in wd_claims:
                                for wd_claim in wd_claims['P2600']:
                                    if wd_claim.get('mainsnak', {}).get('datavalue', {}).get('value'):
                                        geni_id = wd_claim['mainsnak']['datavalue']['value']
                                        print(f"  Adding Geni.com profile ID from Wikidata: {geni_id}")
                                        add_statement(session, qid, 'P43', geni_id, 'string', csrf_token)
                                        add_statement(session, qid, 'P45', f'https://www.geni.com/profile/index/{geni_id}', 'string', csrf_token)
            
            if not has_refn:
                print(f"  Adding as Referenceless item")
                add_statement(session, qid, 'P39', 'Q31342', 'item', csrf_token)
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"  ERROR processing {qid}: {e}")
            continue
    
    print("Database review complete!")

if __name__ == '__main__':
    main()