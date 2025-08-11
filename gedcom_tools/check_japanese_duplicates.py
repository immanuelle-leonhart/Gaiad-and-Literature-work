#!/usr/bin/env python3
"""
Quick script to check for duplicate names in the Japanese GEDCOM file
"""

def check_duplicates():
    """Check for duplicate names in Japanese GEDCOM"""
    names_seen = {}
    duplicates = []
    
    try:
        with open('new_gedcoms/source gedcoms/japan_genealogy_sample.ged', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("Error: japan_genealogy_sample.ged not found!")
        return
    
    lines = content.split('\n')
    current_id = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('0 @I') and line.endswith('@ INDI'):
            current_id = line.split()[1]  # @I123@
        elif line.startswith('1 NAME ') and current_id:
            name = line[7:].strip()
            if name in names_seen:
                duplicates.append({
                    'name': name,
                    'first_id': names_seen[name],
                    'duplicate_id': current_id
                })
            else:
                names_seen[name] = current_id
    
    print(f"Total names processed: {len(names_seen)}")
    print(f"Duplicate names found: {len(duplicates)}")
    
    if duplicates:
        print("\nDuplicate names:")
        for dup in duplicates[:10]:  # Show first 10
            print(f"  '{dup['name']}': {dup['first_id']} and {dup['duplicate_id']}")
        if len(duplicates) > 10:
            print(f"  ... and {len(duplicates) - 10} more duplicates")
    else:
        print("No duplicate names found!")

if __name__ == '__main__':
    check_duplicates()