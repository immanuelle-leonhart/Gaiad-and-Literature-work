#!/usr/bin/env python3
"""
Get the names of the remaining 7 individuals that couldn't be created
"""

remaining_ids = ['@I7000@', '@I7012@', '@I7024@', '@I7085@', '@I7109@', '@I9777@', '@I9797@']

def get_individual_names():
    individuals_data = {}
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        reading_individual = False
        current_id = None
        
        for line in f:
            line = line.strip()
            
            # Check if we're starting to read one of our target individuals
            for target_id in remaining_ids:
                if line == f"0 {target_id} INDI":
                    reading_individual = True
                    current_id = target_id
                    individuals_data[current_id] = {'names': [], 'full_name': None}
                    break
            
            # If we started reading a different individual, stop
            if line.startswith('0 @') and line.endswith('@ INDI') and reading_individual:
                if current_id and line != f"0 {current_id} INDI":
                    reading_individual = False
                    current_id = None
            
            # If we hit another record type, stop reading individual
            if line.startswith('0 ') and not line.endswith('@ INDI') and reading_individual:
                reading_individual = False
                current_id = None
            
            # Extract name information
            if reading_individual and current_id:
                if line.startswith('1 NAME '):
                    name = line[7:].strip()
                    individuals_data[current_id]['full_name'] = name
                    individuals_data[current_id]['names'].append(name)
                elif line.startswith('2 GIVN '):
                    given_name = line[7:].strip()
                    individuals_data[current_id]['names'].append(f"Given: {given_name}")
                elif line.startswith('2 SURN '):
                    surname = line[7:].strip()
                    individuals_data[current_id]['names'].append(f"Surname: {surname}")
                elif line.startswith('2 NSFX '):
                    suffix = line[7:].strip()
                    individuals_data[current_id]['names'].append(f"Suffix: {suffix}")
    
    return individuals_data

def main():
    print("Getting names for the 7 remaining unsolvable individuals...")
    
    individuals_data = get_individual_names()
    
    for individual_id in remaining_ids:
        if individual_id in individuals_data:
            data = individuals_data[individual_id]
            print(f"\n{individual_id}:")
            if data['full_name']:
                print(f"  Full name: {data['full_name']}")
            for name_part in data['names']:
                if not name_part.startswith('1 NAME'):
                    print(f"  {name_part}")
        else:
            print(f"\n{individual_id}: [NAME NOT FOUND IN GEDCOM]")

if __name__ == '__main__':
    main()