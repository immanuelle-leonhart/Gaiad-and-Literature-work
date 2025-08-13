#!/usr/bin/env python3
"""
GAIAD CALENDAR MONTHS SIMPLE CREATOR

Creates wikibase items for all 13 Gaiad calendar months using separate API calls.
Each month is an instance of "Gaian calendar month" (Q151959).

Months: Sagittarius, Capricorn, Aquarius, Pisces, Aries, Taurus,
        Gemini, Cancer, Leo, Virgo, Libra, Scorpio, Ophiuchus
"""

import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Gaiad Calendar Months Creator Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def create_item(session, csrf_token):
    """Create empty item"""
    params = {
        'action': 'wbeditentity',
        'new': 'item',
        'data': '{}',
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

def ordinal(n):
    """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
    if 10 <= n % 100 <= 20: 
        suf = "th"
    else: 
        suf = {1:"st", 2:"nd", 3:"rd"}.get(n % 10, "th")
    return f"{n}{suf}"

def main():
    print("Starting Gaiad calendar months creation...")
    
    # Month names
    MONTHS = [
        "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus",
        "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Ophiuchus"
    ]
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    created_months = []
    
    # Create all 13 month items
    for i, month_name in enumerate(MONTHS, 1):
        try:
            print(f"Creating {month_name} (Month {i})...")
            
            # Step 1: Create empty item
            month_qid = create_item(session, csrf_token)
            if not month_qid:
                error_count += 1
                continue
            
            print(f"  Created item: {month_qid}")
            time.sleep(0.2)
            
            # Step 2: Set English label
            set_label(session, month_qid, 'en', month_name, csrf_token)
            time.sleep(0.2)
            
            # Step 3: Set Japanese label
            set_label(session, month_qid, 'ja', f'{i}宮', csrf_token)
            time.sleep(0.2)
            
            # Step 4: Set English description
            desc = f'{month_name} month in the Gaiad calendar, the {ordinal(i)} month of 13'
            set_description(session, month_qid, 'en', desc, csrf_token)
            time.sleep(0.2)
            
            # Step 5: Add instance of claim
            add_statement(session, month_qid, 'P3', 'Q151959', csrf_token)
            time.sleep(0.2)
            
            created_months.append((i, month_name, month_qid))
            success_count += 1
            print(f"  SUCCESS: Created {month_qid} for {month_name}")
            
            time.sleep(1)  # Rate limiting between items
            
        except Exception as e:
            print(f"  ERROR creating {month_name}: {e}")
            error_count += 1
    
    print(f"\nGaiad calendar months creation complete!")
    print(f"Successfully created: {success_count} months")
    print(f"Errors: {error_count}")
    
    print("\n=== CREATED MONTHS ===")
    for month_num, month_name, qid in created_months:
        print(f"{qid}: {month_name} ({month_num}宮)")
    
    print("\nUpdate the gaiad_calendar_days_creator.py with these QIDs!")

if __name__ == '__main__':
    main()