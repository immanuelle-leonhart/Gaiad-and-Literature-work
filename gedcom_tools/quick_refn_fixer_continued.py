#!/usr/bin/env python3
import requests
import json
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Quick REFN Fixer Continued Bot/1.0 (https://github.com/Immanuelle/Gaiad-Genealogy; immanuelle@example.com)'
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

def parse_gedcom_individual(lines):
    individual = {'id': '', 'refns': []}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split(' ', 2)
        if len(parts) < 2:
            continue
            
        level = int(parts[0])
        tag = parts[1]
        value = parts[2] if len(parts) > 2 else ''
        
        if level == 0 and tag.startswith('@I') and tag.endswith('@'):
            individual['id'] = tag
        elif level == 1 and tag == 'REFN':
            individual['refns'].append(value)
    
    return individual

def get_refns_from_gedcom(gedcom_id):
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_individual = []
    
    for line in lines:
        if line.startswith('0 @I') and line.endswith('@ INDI'):
            if current_individual:
                individual = parse_gedcom_individual(current_individual)
                if individual['id'] == gedcom_id and individual['refns']:
                    return individual['refns']
            current_individual = [line]
        elif current_individual:
            if line.startswith('0 ') and not line.endswith('@ INDI'):
                individual = parse_gedcom_individual(current_individual)
                if individual['id'] == gedcom_id and individual['refns']:
                    return individual['refns']
                current_individual = []
            else:
                current_individual.append(line)
    
    if current_individual:
        individual = parse_gedcom_individual(current_individual)
        if individual['id'] == gedcom_id and individual['refns']:
            return individual['refns']
    
    return []

def add_refn_statement(session, qid, refn_value, csrf_token):
    params = {
        'action': 'wbcreateclaim',
        'entity': qid,
        'property': 'P41',
        'snaktype': 'value',
        'value': json.dumps(refn_value),
        'format': 'json',
        'token': csrf_token,
        'summary': 'Adding GEDCOM REFN from master genealogy continued patch',
        'bot': 1
    }
    
    response = session.post('https://evolutionism.miraheze.org/w/api.php', data=params)
    return response.json()

def main():
    print("Starting quick REFN fixer continued from @I63331@...")
    
    # Load mappings for I63331+
    mappings = {}
    with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('@I') and '\t' in line:
                parts = line.strip().split('\t')
                if len(parts) == 2:
                    gedcom_id = parts[0]
                    qid = parts[1]
                    # Only process I63331+
                    if gedcom_id.startswith('@I') and gedcom_id.endswith('@'):
                        try:
                            i_num = int(gedcom_id[2:-1])
                            if i_num >= 63331:
                                mappings[gedcom_id] = qid
                        except ValueError:
                            continue
    
    print(f"Found {len(mappings)} mappings for I41026+")
    
    session = create_session()
    if not login_to_wiki(session):
        print("Failed to login. Exiting.")
        return
    
    csrf_token = get_csrf_token(session)
    
    success_count = 0
    error_count = 0
    
    # Sort mappings by I-number to process in order
    sorted_mappings = sorted(mappings.items(), key=lambda x: int(x[0][2:-1]))
    
    for gedcom_id, qid in sorted_mappings:
        print(f"Processing {gedcom_id} -> {qid}")
        
        try:
            refn_values = get_refns_from_gedcom(gedcom_id)
            if refn_values:
                for refn_value in refn_values:
                    print(f"  Adding REFN: {refn_value}")
                    result = add_refn_statement(session, qid, refn_value, csrf_token)
                    if 'success' in result:
                        success_count += 1
                    else:
                        print(f"  Error: {result}")
                        error_count += 1
                    time.sleep(0.5)  # Rate limit between multiple REFNs
            else:
                print(f"  No REFNs found")
                error_count += 1
            
            time.sleep(0.5)  # Fast rate limiting
            
        except Exception as e:
            print(f"  ERROR: {e}")
            error_count += 1
    
    print(f"\nQuick fix continued complete!")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")

if __name__ == '__main__':
    main()