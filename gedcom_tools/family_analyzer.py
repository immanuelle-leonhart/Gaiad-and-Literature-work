#!/usr/bin/env python3
"""
Quick analyzer to check what family information exists in master GEDCOM
"""

def analyze_families():
    print("Analyzing family sections in master GEDCOM...")
    
    families = {}
    family_count = 0
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_family = []
    in_family = False
    
    for line in lines:
        if line.startswith('0 @F') and line.endswith('@ FAM'):
            if current_family:
                family = parse_family(current_family)
                if family['id']:
                    families[family['id']] = family
                    family_count += 1
            current_family = [line]
            in_family = True
        elif in_family:
            if line.startswith('0 ') and not line.endswith('@ FAM'):
                family = parse_family(current_family)
                if family['id']:
                    families[family['id']] = family
                    family_count += 1
                current_family = []
                in_family = False
            else:
                current_family.append(line)
    
    # Process last family
    if current_family and in_family:
        family = parse_family(current_family)
        if family['id']:
            families[family['id']] = family
            family_count += 1
    
    print(f"Total families found: {family_count}")
    
    # Analyze what data exists
    has_marriage_date = 0
    has_marriage_place = 0
    has_divorce_date = 0
    has_notes = 0
    has_other_events = 0
    
    sample_families = []
    
    for fam_id, family in list(families.items())[:20]:  # Sample first 20
        sample_families.append(family)
        
        if family.get('marriage_date'):
            has_marriage_date += 1
        if family.get('marriage_place'):
            has_marriage_place += 1
        if family.get('divorce_date'):
            has_divorce_date += 1
        if family.get('notes'):
            has_notes += 1
        if len(family.get('other_events', [])) > 0:
            has_other_events += 1
    
    print(f"\nSample analysis of first 20 families:")
    print(f"  With marriage dates: {has_marriage_date}")
    print(f"  With marriage places: {has_marriage_place}")
    print(f"  With divorce dates: {has_divorce_date}")
    print(f"  With notes: {has_notes}")
    print(f"  With other events: {has_other_events}")
    
    # Show detailed examples
    print(f"\nDetailed examples:")
    for i, family in enumerate(sample_families[:5]):
        print(f"\nFamily {family['id']}:")
        print(f"  Husband: {family.get('husband', 'None')}")
        print(f"  Wife: {family.get('wife', 'None')}")
        print(f"  Children: {len(family.get('children', []))}")
        if family.get('marriage_date'):
            print(f"  Marriage date: {family['marriage_date']}")
        if family.get('marriage_place'):
            print(f"  Marriage place: {family['marriage_place']}")
        if family.get('notes'):
            print(f"  Notes: {family['notes'][:100]}...")
        if family.get('other_events'):
            print(f"  Other events: {family['other_events']}")

def parse_family(lines):
    family = {
        'id': '',
        'husband': '',
        'wife': '',
        'children': [],
        'marriage_date': '',
        'marriage_place': '',
        'divorce_date': '',
        'notes': '',
        'other_events': []
    }
    
    current_event = None
    
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
        
        if level == 0 and tag.startswith('@F') and tag.endswith('@'):
            family['id'] = tag
        elif level == 1:
            if tag == 'HUSB':
                family['husband'] = value
            elif tag == 'WIFE':
                family['wife'] = value
            elif tag == 'CHIL':
                family['children'].append(value)
            elif tag == 'MARR':
                current_event = 'marriage'
            elif tag == 'DIV':
                current_event = 'divorce'
            elif tag == 'NOTE':
                family['notes'] = value
            else:
                family['other_events'].append(f"{tag}: {value}")
        elif level == 2:
            if current_event == 'marriage':
                if tag == 'DATE':
                    family['marriage_date'] = value
                elif tag == 'PLAC':
                    family['marriage_place'] = value
            elif current_event == 'divorce':
                if tag == 'DATE':
                    family['divorce_date'] = value
    
    return family

if __name__ == '__main__':
    analyze_families()