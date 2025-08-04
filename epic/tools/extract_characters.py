#!/usr/bin/env python3
"""
Character Extraction Tool for Gaiad Epic
Extracts character names and references from chapters
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_names_from_chapter(file_path):
    """Extract proper names from a chapter file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove line numbers
    content = re.sub(r'^\s*\d+→', '', content, flags=re.MULTILINE)
    
    # Find proper names (capitalized words, not at start of line)
    names = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]*)*\b', content)
    
    # Filter out common words that aren't names
    common_words = {
        'The', 'And', 'But', 'Yet', 'Then', 'When', 'Where', 'While', 
        'Through', 'From', 'With', 'Upon', 'Beneath', 'Above', 'Beyond',
        'Once', 'Now', 'Here', 'There', 'They', 'Their', 'Each', 'Every',
        'Alpha', 'Omega', 'Point', 'Lady', 'Great', 'Advertisement',
        'All', 'Her', 'His', 'She', 'He', 'As', 'In', 'On', 'At', 'To',
        'A', 'An', 'For', 'Of', 'By', 'So', 'Up', 'Out', 'Off', 'Down'
    }
    
    # Count occurrences
    name_counts = defaultdict(int)
    for name in names:
        if name not in common_words and len(name) > 2:
            name_counts[name] += 1
    
    return name_counts

def main():
    all_characters = defaultdict(lambda: defaultdict(int))
    
    for chapter_file in sorted(Path('.').glob('chapter_*.md')):
        chapter_names = extract_names_from_chapter(chapter_file)
        chapter_num = chapter_file.stem.split('_')[1]
        
        print(f"\n=== Chapter {chapter_num} ===")
        for name, count in sorted(chapter_names.items(), key=lambda x: -x[1]):
            if count >= 2:  # Only show names mentioned multiple times
                print(f"  {name}: {count}")
                all_characters[name][chapter_num] = count
    
    # Create character index
    print(f"\n=== Character Index ===")
    for name in sorted(all_characters.keys()):
        chapters = ', '.join(f"Ch{ch}({count})" for ch, count in sorted(all_characters[name].items()))
        print(f"{name}: {chapters}")

if __name__ == "__main__":
    main()