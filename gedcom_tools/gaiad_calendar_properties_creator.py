#!/usr/bin/env python3
"""
GAIAD CALENDAR PROPERTIES CREATOR

Creates the necessary properties for Gaiad calendar days:
- P50: ordinal within year (number 1-364)
- P51: ordinal within month (number 1-28)  
- P52: ISO week number (number 1-52)
- P53: ISO weekday number (number 1-7)

Also creates month items if needed.
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Gaiad Calendar Properties Creator Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def create_property(session, csrf_token, property_data):
    """Create a property with given data"""
    params = {
        'action': 'wbeditentity',
        'new': 'property',
        'data': json.dumps(property_data),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    result = response.json()
    
    if 'entity' in result:
        return result['entity']['id']
    else:
        print(f"Error creating property: {result}")
        return None

def create_item(session, csrf_token, item_data):
    """Create an item with given data"""
    params = {
        'action': 'wbeditentity',
        'new': 'item',
        'data': json.dumps(item_data),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    result = response.json()
    
    if 'entity' in result:
        return result['entity']['id']
    else:
        print(f"Error creating item: {result}")
        return None

def add_statement(session, qid, property_id, value_qid, csrf_token):
    params = {
        'action': 'wbcreateclaim',
        'entity': qid,
        'property': property_id,
        'snaktype': 'value',
        'value': json.dumps({'entity-type': 'item', 'numeric-id': int(value_qid[1:])}),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def main():
    print("Creating Gaiad calendar properties and month items...")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    # Create properties needed for calendar days
    properties_to_create = [
        {
            'labels': {'en': {'language': 'en', 'value': 'ordinal within year'}},
            'descriptions': {'en': {'language': 'en', 'value': 'position of this day within the year (1-364 for Gaiad calendar)'}},
            'datatype': 'quantity'
        },
        {
            'labels': {'en': {'language': 'en', 'value': 'ordinal within month'}},
            'descriptions': {'en': {'language': 'en', 'value': 'position of this day within its month (1-28 for Gaiad calendar)'}},
            'datatype': 'quantity'
        },
        {
            'labels': {'en': {'language': 'en', 'value': 'ISO week number'}},
            'descriptions': {'en': {'language': 'en', 'value': 'ISO 8601 week number that this day corresponds to (1-52)'}},
            'datatype': 'quantity'
        },
        {
            'labels': {'en': {'language': 'en', 'value': 'ISO weekday number'}},
            'descriptions': {'en': {'language': 'en', 'value': 'ISO 8601 weekday number (1=Monday, 7=Sunday)'}},
            'datatype': 'quantity'
        }
    ]
    
    created_properties = []
    
    for i, prop_data in enumerate(properties_to_create):
        print(f"Creating property: {prop_data['labels']['en']['value']}")
        prop_id = create_property(session, csrf_token, prop_data)
        if prop_id:
            created_properties.append(prop_id)
            print(f"  SUCCESS: Created {prop_id}")
        else:
            print(f"  FAILED")
        time.sleep(1)
    
    print(f"Created properties: {created_properties}")
    
    # Create month items (instances of Q151959 - Gaian calendar month)
    MONTHS = [
        "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus",
        "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Ophiuchus"
    ]
    
    created_months = []
    
    for i, month_name in enumerate(MONTHS, 1):
        print(f"Creating month: {month_name}")
        
        month_data = {
            'labels': {
                'en': {'language': 'en', 'value': month_name},
                'ja': {'language': 'ja', 'value': f'{i}宮'}
            },
            'descriptions': {
                'en': {'language': 'en', 'value': f'{month_name} month in the Gaiad calendar, the {i}{"st" if i==1 else "nd" if i==2 else "rd" if i==3 else "th"} month'}
            },
            'claims': {
                'P3': [  # instance of
                    {
                        'mainsnak': {
                            'snaktype': 'value',
                            'property': 'P3',
                            'datavalue': {
                                'value': {'entity-type': 'item', 'numeric-id': 151959},
                                'type': 'wikibase-entityid'
                            }
                        },
                        'type': 'statement'
                    }
                ]
            }
        }
        
        month_qid = create_item(session, csrf_token, month_data)
        if month_qid:
            created_months.append((i, month_name, month_qid))
            print(f"  SUCCESS: Created {month_qid} for {month_name}")
        else:
            print(f"  FAILED to create {month_name}")
        time.sleep(1)
    
    print("\n=== SUMMARY ===")
    print("Created Properties:")
    for i, prop_id in enumerate(created_properties):
        prop_names = ['ordinal within year', 'ordinal within month', 'ISO week number', 'ISO weekday number']
        print(f"  {prop_id}: {prop_names[i]}")
    
    print("\nCreated Months:")
    for month_num, month_name, qid in created_months:
        print(f"  {qid}: {month_name} ({month_num}宮)")
    
    print("\nUpdate the gaiad_calendar_days_creator.py script with these QIDs!")

if __name__ == '__main__':
    main()