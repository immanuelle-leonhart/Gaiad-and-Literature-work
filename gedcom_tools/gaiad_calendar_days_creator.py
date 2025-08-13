#!/usr/bin/env python3
"""
GAIAD CALENDAR DAYS CREATOR

Creates wikibase items for all 364 Gaiad calendar days.
Each day is an instance of "Gaian calendar day" (Q151960).
Days belong to months which are instances of "Gaian calendar month" (Q151959).

Based on the calendar structure from zodiac_wiki_pages.py:
- 13 months of 28 days each = 364 days
- Months: Sagittarius, Capricorn, Aquarius, Pisces, Aries, Taurus,
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
        'User-Agent': 'Gaiad Calendar Days Creator Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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
    params = {
        'action': 'wbeditentity',
        'new': 'item',
        'data': json.dumps({}),
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

def add_numeric_statement(session, qid, property_id, value, csrf_token):
    params = {
        'action': 'wbcreateclaim',
        'entity': qid,
        'property': property_id,
        'snaktype': 'value',
        'value': json.dumps({'amount': '+' + str(value), 'unit': '1'}),
        'format': 'json',
        'token': csrf_token,
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def zodiac_to_iso(m_idx, d_m):
    """Convert Gaiad calendar date to ISO week/weekday"""
    if not (1 <= m_idx <= 13 and 1 <= d_m <= 28):
        raise ValueError("month_index 1..13, day_of_month 1..28 required")
    iso_week = (m_idx - 1) * 4 + ((d_m - 1) // 7) + 1      # 1..52
    iso_wday = ((d_m - 1) % 7) + 1                         # 1..7 (Mon..Sun)
    return iso_week, iso_wday

def ordinal_in_year(m_idx, d_m):
    """Get day number within the year (1-364)"""
    w, wd = zodiac_to_iso(m_idx, d_m)
    return (w - 1) * 7 + wd

def ordinal(n):
    """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
    if 10 <= n % 100 <= 20: 
        suf = "th"
    else: 
        suf = {1:"st", 2:"nd", 3:"rd"}.get(n % 10, "th")
    return f"{n}{suf}"

def get_weekday_name(iso_wd):
    """Convert ISO weekday number to name"""
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][iso_wd-1]

def main():
    print("Starting Gaiad calendar days creation...")
    
    # Month names and properties
    MONTHS = [
        "Sagittarius", "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus",
        "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Ophiuchus"
    ]
    
    # Month QIDs (created from gaiad_calendar_months_simple.py)
    MONTH_QIDS = {
        1: "Q151987",   # Sagittarius
        2: "Q151988",   # Capricorn
        3: "Q151989",   # Aquarius (had errors but item created)
        4: "Q151990",   # Pisces (had errors but item created)
        5: "Q151991",   # Aries
        6: "Q151992",   # Taurus
        7: "Q151993",   # Gemini
        8: "Q151994",   # Cancer
        9: "Q151995",   # Leo
        10: "Q151996",  # Virgo
        11: "Q151997",  # Libra
        12: "Q151998",  # Scorpio
        13: "Q151999"   # Ophiuchus
    }
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    
    # Create all 364 calendar days (13 months × 28 days)
    for month_idx in range(1, 14):  # 1 to 13
        month_name = MONTHS[month_idx - 1]
        month_qid = MONTH_QIDS[month_idx]
        
        print(f"\nProcessing {month_name} (Month {month_idx})...")
        
        for day_num in range(1, 29):  # 1 to 28
            try:
                print(f"  Creating {month_name} {day_num}...")
                
                # Create the item
                qid = create_item(session, csrf_token)
                if not qid:
                    error_count += 1
                    continue
                
                # Calculate properties
                ordinal_day = ordinal_in_year(month_idx, day_num)
                iso_week, iso_wday = zodiac_to_iso(month_idx, day_num)
                weekday_name = get_weekday_name(iso_wday)
                japanese_informal = f"{month_idx}宮{day_num}日"
                
                # Set English label
                en_label = f"{month_name} {day_num}"
                set_label(session, qid, 'en', en_label, csrf_token)
                time.sleep(0.2)
                
                # Set English description
                en_desc = f"{ordinal(ordinal_day)} day of the year in the Gaiad calendar, {ordinal(day_num)} day of {month_name}"
                set_description(session, qid, 'en', en_desc, csrf_token)
                time.sleep(0.2)
                
                # Set Japanese label
                set_label(session, qid, 'ja', japanese_informal, csrf_token)
                time.sleep(0.2)
                
                # Add instance of "Gaian calendar day" (Q151960)
                add_statement(session, qid, 'P3', 'Q151960', csrf_token)
                time.sleep(0.2)
                
                # Add "part of" relationship to month
                add_statement(session, qid, 'P22', month_qid, csrf_token)
                time.sleep(0.2)
                
                # Add ordinal in year (day number 1-364) - P49
                add_numeric_statement(session, qid, 'P49', ordinal_day, csrf_token)
                time.sleep(0.2)
                
                # Add ordinal in month (day number 1-28) - P50
                add_numeric_statement(session, qid, 'P50', day_num, csrf_token)
                time.sleep(0.2)
                
                # Add ISO week number - P51
                add_numeric_statement(session, qid, 'P51', iso_week, csrf_token)
                time.sleep(0.2)
                
                # Add ISO weekday number - P52
                add_numeric_statement(session, qid, 'P52', iso_wday, csrf_token)
                time.sleep(0.2)
                
                print(f"    SUCCESS: Created {qid} for {en_label}")
                success_count += 1
                
                # Rate limiting between items
                time.sleep(1)
                
            except Exception as e:
                print(f"    ERROR creating {month_name} {day_num}: {e}")
                error_count += 1
    
    print(f"\nGaiad calendar days creation complete!")
    print(f"Successfully created: {success_count} days")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()