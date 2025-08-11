#!/usr/bin/env python3
"""
Quick analyzer to check where the notes are distributed in master GEDCOM
"""

def analyze_notes_distribution():
    print("Analyzing notes LENGTH distribution in master GEDCOM...")
    
    individuals_with_notes = []
    individuals_without_notes = []
    
    with open('new_gedcoms/source gedcoms/master_combined.ged', 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    current_individual = []
    
    for line in lines:
        if line.startswith('0 @I') and line.endswith('@ INDI'):
            if current_individual:
                individual = parse_individual_notes(current_individual)
                if individual['id']:
                    if individual['notes_length'] > 0:
                        individuals_with_notes.append((individual['id'], individual['notes_length']))
                    else:
                        individuals_without_notes.append(individual['id'])
            current_individual = [line]
        elif current_individual:
            if line.startswith('0 ') and not line.endswith('@ INDI'):
                individual = parse_individual_notes(current_individual)
                if individual['id']:
                    if individual['notes_length'] > 0:
                        individuals_with_notes.append((individual['id'], individual['notes_length']))
                    else:
                        individuals_without_notes.append(individual['id'])
                current_individual = []
            else:
                current_individual.append(line)
    
    if current_individual:
        individual = parse_individual_notes(current_individual)
        if individual['id']:
            if individual['notes_length'] > 0:
                individuals_with_notes.append((individual['id'], individual['notes_length']))
            else:
                individuals_without_notes.append(individual['id'])
    
    print(f"Total individuals with notes: {len(individuals_with_notes)}")
    print(f"Total individuals without notes: {len(individuals_without_notes)}")
    print(f"Total individuals: {len(individuals_with_notes) + len(individuals_without_notes)}")
    
    # Sort by note length to find longest notes
    individuals_with_notes.sort(key=lambda x: x[1], reverse=True)
    
    # Analyze note lengths
    note_lengths = [length for _, length in individuals_with_notes]
    if note_lengths:
        avg_length = sum(note_lengths) / len(note_lengths)
        print(f"\nNote length statistics:")
        print(f"  Average note length: {avg_length:.1f} characters")
        print(f"  Longest note: {max(note_lengths)} characters")
        print(f"  Shortest note: {min(note_lengths)} characters")
        
        # Find length categories
        very_long = [x for x in individuals_with_notes if x[1] > 1000]
        long_notes = [x for x in individuals_with_notes if 500 <= x[1] <= 1000]
        medium_notes = [x for x in individuals_with_notes if 100 <= x[1] < 500]
        short_notes = [x for x in individuals_with_notes if x[1] < 100]
        
        print(f"\nNote length categories:")
        print(f"  Very long (1000+ chars): {len(very_long)}")
        print(f"  Long (500-1000 chars): {len(long_notes)}")
        print(f"  Medium (100-500 chars): {len(medium_notes)}")
        print(f"  Short (<100 chars): {len(short_notes)}")
        
        # Show longest notes
        print(f"\n20 individuals with longest notes:")
        for i, (individual_id, length) in enumerate(individuals_with_notes[:20]):
            print(f"  {i+1}. {individual_id}: {length} characters")
        
        print(f"\n20 individuals with shortest notes:")
        for i, (individual_id, length) in enumerate(individuals_with_notes[-20:]):
            print(f"  {len(individuals_with_notes)-19+i}. {individual_id}: {length} characters")
    
    # Analyze distribution by ID ranges
    print("\nDistribution by ID ranges:")
    
    ranges = [
        (1, 1000, "I1-I1000"),
        (1001, 5000, "I1001-I5000"),
        (5001, 10000, "I5001-I10000"),
        (10001, 15000, "I10001-I15000"),
        (15001, 20000, "I15001-I20000"),
        (20001, 25000, "I20001-I25000"),
        (25001, 30000, "I25001-I30000"),
        (30001, 100000, "I30001+")
    ]
    
    for min_id, max_id, range_name in ranges:
        with_notes = 0
        without_notes = 0
        
        for individual_id in individuals_with_notes:
            try:
                num_id = int(individual_id[2:-1])  # Extract number from @I123@
                if min_id <= num_id <= max_id:
                    with_notes += 1
            except:
                continue
                
        for individual_id in individuals_without_notes:
            try:
                num_id = int(individual_id[2:-1])  # Extract number from @I123@
                if min_id <= num_id <= max_id:
                    without_notes += 1
            except:
                continue
        
        total_in_range = with_notes + without_notes
        if total_in_range > 0:
            percentage = (with_notes / total_in_range) * 100
            print(f"  {range_name}: {with_notes}/{total_in_range} ({percentage:.1f}%) have notes")
    
    # Show first 20 and last 20 individuals with notes
    print(f"\nFirst 20 individuals with notes:")
    for i, individual_id in enumerate(individuals_with_notes[:20]):
        print(f"  {i+1}. {individual_id}")
    
    print(f"\nLast 20 individuals with notes:")
    for i, individual_id in enumerate(individuals_with_notes[-20:]):
        print(f"  {len(individuals_with_notes)-19+i}. {individual_id}")

def parse_individual_notes(lines):
    individual = {'id': '', 'notes_length': 0, 'notes': []}
    
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
        elif level == 1 and tag == 'NOTE':
            individual['notes'].append(value)
        elif level == 2 and tag == 'CONT':
            if individual['notes']:
                individual['notes'][-1] += '\n' + value
        elif level == 2 and tag == 'CONC':
            if individual['notes']:
                individual['notes'][-1] += value
    
    # Calculate total length of all notes
    total_notes = '\n\n'.join(individual['notes'])
    individual['notes_length'] = len(total_notes)
    
    return individual

if __name__ == '__main__':
    analyze_notes_distribution()