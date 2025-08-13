#!/usr/bin/env python3
"""
Analyze GEDCOM notes to find substantial notes (longer than 3 lines)
that aren't just auto-generated Wikidata/Geni references.
Creates a CSV with meaningful notes for review.
"""

import csv
import re
from pathlib import Path

def is_auto_generated_note(note_text):
    """Check if a note appears to be auto-generated (Wikidata/Geni references)."""
    note_lower = note_text.lower().strip()
    
    # Common patterns for auto-generated notes
    auto_patterns = [
        r'wikidata\s+id:?\s*q\d+',
        r'wikidata\s+url:?\s*https?://www\.wikidata\.org',
        r'geni\.com\s+profile\s+id:?\s*\d+',
        r'geni\.com\s+url:?\s*https?://www\.geni\.com',
        r'imported\s+from\s+wikidata',
        r'source:\s*wikidata',
        r'source:\s*geni',
        r'auto-generated',
        r'automatically\s+imported',
        r'^q\d+\s*$',  # Just a Q-ID
        r'^\d{4,}\s*$',  # Just a long number (likely Geni ID)
    ]
    
    for pattern in auto_patterns:
        if re.search(pattern, note_lower):
            return True
    
    return False

def parse_gedcom_individual(lines):
    """Parse an individual's GEDCOM lines to extract ID and notes."""
    individual = {'id': '', 'notes': []}
    current_note = []
    in_note = False
    
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
            if in_note and current_note:
                # Save previous note
                individual['notes'].append('\n'.join(current_note))
            current_note = [value] if value else []
            in_note = True
        elif level == 2 and tag == 'CONT' and in_note:
            current_note.append(value)
        elif level == 2 and tag == 'CONC' and in_note:
            if current_note:
                current_note[-1] += value
            else:
                current_note.append(value)
        elif level == 1 and tag != 'NOTE' and in_note:
            # End of current note
            if current_note:
                individual['notes'].append('\n'.join(current_note))
            current_note = []
            in_note = False
    
    # Don't forget the last note
    if in_note and current_note:
        individual['notes'].append('\n'.join(current_note))
    
    return individual

def parse_gedcom_notes(gedcom_file='new_gedcoms/source gedcoms/master_combined.ged'):
    """Parse the GEDCOM file and extract all notes data."""
    notes_data = {}
    
    try:
        with open(gedcom_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        # Try with different encoding
        with open(gedcom_file, 'r', encoding='latin1') as f:
            lines = f.readlines()
    
    current_individual = []
    
    for line in lines:
        if line.startswith('0 @I') and line.endswith('@ INDI\n'):
            if current_individual:
                individual = parse_gedcom_individual(current_individual)
                if individual['id'] and individual['notes']:
                    notes_data[individual['id']] = individual['notes']
            current_individual = [line]
        elif current_individual:
            current_individual.append(line)
    
    # Process the last individual
    if current_individual:
        individual = parse_gedcom_individual(current_individual)
        if individual['id'] and individual['notes']:
            notes_data[individual['id']] = individual['notes']
    
    return notes_data

def load_qid_mappings():
    """Load GEDCOM ID to QID mappings."""
    mappings = {}
    try:
        with open('gedcom_to_qid_mapping.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('@I') and '\t' in line:
                    parts = line.strip().split('\t')
                    if len(parts) == 2:
                        mappings[parts[0]] = parts[1]
    except FileNotFoundError:
        print("Warning: gedcom_to_qid_mapping.txt not found. QID column will be empty.")
    
    return mappings

def analyze_notes():
    """Main analysis function."""
    print("Analyzing GEDCOM notes for substantial content...")
    
    # Load data
    notes_data = parse_gedcom_notes()
    qid_mappings = load_qid_mappings()
    
    print(f"Found {len(notes_data)} individuals with notes")
    
    # Analyze notes
    substantial_notes = []
    
    for gedcom_id, notes_list in notes_data.items():
        qid = qid_mappings.get(gedcom_id, '')
        
        for note_text in notes_list:
            lines = note_text.split('\n')
            line_count = len([line for line in lines if line.strip()])  # Count non-empty lines
            
            # Check if note is substantial (>3 lines) and not auto-generated
            if line_count > 3 and not is_auto_generated_note(note_text):
                substantial_notes.append({
                    'gedcom_id': gedcom_id,
                    'qid': qid,
                    'line_count': line_count,
                    'char_count': len(note_text),
                    'note_preview': note_text[:100] + '...' if len(note_text) > 100 else note_text,
                    'full_note': note_text
                })
    
    # Sort by line count (longest first)
    substantial_notes.sort(key=lambda x: x['line_count'], reverse=True)
    
    print(f"Found {len(substantial_notes)} substantial notes (>3 lines, non-auto-generated)")
    
    # Write to CSV
    output_file = 'substantial_notes_analysis.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['gedcom_id', 'qid', 'line_count', 'char_count', 'note_preview', 'full_note']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for note_data in substantial_notes:
            writer.writerow(note_data)
    
    print(f"Results written to {output_file}")
    
    # Print summary statistics
    if substantial_notes:
        print("\n=== SUMMARY ===")
        print(f"Total substantial notes: {len(substantial_notes)}")
        print(f"Longest note: {max(note['line_count'] for note in substantial_notes)} lines")
        print(f"Average length: {sum(note['line_count'] for note in substantial_notes) // len(substantial_notes)} lines")
        
        # Show top 5 longest notes
        print("\n=== TOP 5 LONGEST NOTES ===")
        for i, note in enumerate(substantial_notes[:5], 1):
            print(f"{i}. {note['gedcom_id']} ({note['qid']}) - {note['line_count']} lines")
            print(f"   Preview: {note['note_preview']}")
            print()
    
    return substantial_notes

if __name__ == '__main__':
    analyze_notes()