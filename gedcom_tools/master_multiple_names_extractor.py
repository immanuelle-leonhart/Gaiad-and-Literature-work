#!/usr/bin/env python3
"""
MASTER GEDCOM MULTIPLE NAMES EXTRACTOR

Finds all individuals in the master GEDCOM file that have multiple NAME entries
and exports them to a CSV file for later processing to add multiple names to the database.
"""

import csv

def parse_individual_names(lines):
    individual = {'id': '', 'names': []}
    
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
        elif level == 1 and tag == 'NAME':
            # Clean up GEDCOM name format - remove /slashes/ around surname
            cleaned_name = value.replace('/', '').strip()
            if cleaned_name:  # Only add non-empty names
                individual['names'].append(cleaned_name)
    
    return individual

def extract_multiple_names():
    print("Extracting individuals with multiple names from master GEDCOM...")
    
    multiple_names_data = []
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_individual = []
    
    for line in lines:
        if line.startswith('0 @I') and line.endswith('@ INDI'):
            if current_individual:
                individual = parse_individual_names(current_individual)
                if individual['id'] and len(individual['names']) > 1:
                    multiple_names_data.append(individual)
            current_individual = [line]
        elif current_individual:
            if line.startswith('0 ') and not line.endswith('@ INDI'):
                individual = parse_individual_names(current_individual)
                if individual['id'] and len(individual['names']) > 1:
                    multiple_names_data.append(individual)
                current_individual = []
            else:
                current_individual.append(line)
    
    # Handle last individual
    if current_individual:
        individual = parse_individual_names(current_individual)
        if individual['id'] and len(individual['names']) > 1:
            multiple_names_data.append(individual)
    
    print(f"Found {len(multiple_names_data)} individuals with multiple names")
    
    # Export to CSV
    csv_filename = 'master_multiple_names.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Write header
        writer.writerow(['GEDCOM_ID', 'NAME_COUNT', 'PRIMARY_NAME', 'ADDITIONAL_NAMES'])
        
        # Write data
        for individual in multiple_names_data:
            gedcom_id = individual['id']
            names = individual['names']
            name_count = len(names)
            primary_name = names[0]
            additional_names = '; '.join(names[1:])
            
            writer.writerow([gedcom_id, name_count, primary_name, additional_names])
    
    print(f"Exported to {csv_filename}")
    
    # Print some statistics
    name_counts = {}
    for individual in multiple_names_data:
        count = len(individual['names'])
        name_counts[count] = name_counts.get(count, 0) + 1
    
    print("\nName count distribution:")
    for count in sorted(name_counts.keys()):
        print(f"  {count} names: {name_counts[count]} individuals")
    
    # Show examples
    print(f"\nFirst 10 examples:")
    for i, individual in enumerate(multiple_names_data[:10]):
        print(f"  {individual['id']}: {', '.join(individual['names'])}")

if __name__ == '__main__':
    extract_multiple_names()