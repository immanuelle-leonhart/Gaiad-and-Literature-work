#!/usr/bin/env python3
"""
Epic Meter Validation Tool for Gaiad Epic
Validates 10-syllable lines and ABAB rhyme scheme
"""

import re
import sys
from pathlib import Path

def count_syllables(word):
    """Count syllables in a word using basic heuristics"""
    word = word.lower().strip(".,!?;:")
    if not word:
        return 0
    
    # Handle common patterns
    vowels = "aeiouy"
    syllable_count = 0
    prev_was_vowel = False
    
    for i, char in enumerate(word):
        if char in vowels:
            if not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = True
        else:
            prev_was_vowel = False
    
    # Handle silent e
    if word.endswith('e') and syllable_count > 1:
        syllable_count -= 1
    
    # Handle special cases
    if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
        syllable_count += 1
    
    return max(1, syllable_count)

def count_line_syllables(line):
    """Count total syllables in a line"""
    # Remove line numbers and arrows
    line = re.sub(r'^\s*\d+→', '', line)
    words = re.findall(r'\b\w+\b', line)
    return sum(count_syllables(word) for word in words)

def get_rhyme_sound(line):
    """Extract the rhyme sound from end of line"""
    line = re.sub(r'^\s*\d+→', '', line)
    words = re.findall(r'\b\w+\b', line)
    if not words:
        return ""
    
    last_word = words[-1].lower()
    # Simple rhyme detection - last 2-3 characters
    if len(last_word) >= 3:
        return last_word[-3:]
    return last_word

def validate_chapter(file_path):
    """Validate syllable count and rhyme scheme for a chapter"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues = []
    stanza_lines = []
    stanza_num = 1
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Check if it's a content line (has line number arrow)
        if '→' in line:
            syllables = count_line_syllables(line)
            rhyme_sound = get_rhyme_sound(line)
            
            stanza_lines.append({
                'line_num': line_num,
                'text': line,
                'syllables': syllables,
                'rhyme_sound': rhyme_sound
            })
            
            # Check syllable count
            if syllables != 10:
                issues.append(f"Line {line_num}: {syllables} syllables (expected 10)")
            
            # Check ABAB pattern every 4 lines
            if len(stanza_lines) == 4:
                # Check ABAB rhyme scheme
                a1, b1, a2, b2 = [l['rhyme_sound'] for l in stanza_lines]
                
                if not (a1 == a2 and b1 == b2 and a1 != b1):
                    issues.append(f"Stanza {stanza_num}: Rhyme scheme not ABAB ({a1}-{b1}-{a2}-{b2})")
                
                stanza_lines = []
                stanza_num += 1
    
    return issues

def main():
    if len(sys.argv) > 1:
        chapter_file = Path(sys.argv[1])
        if chapter_file.exists():
            issues = validate_chapter(chapter_file)
            if issues:
                print(f"Issues found in {chapter_file.name}:")
                for issue in issues:
                    print(f"  {issue}")
            else:
                print(f"{chapter_file.name}: All validation checks passed!")
        else:
            print(f"File not found: {chapter_file}")
    else:
        # Validate all chapters
        for chapter_file in sorted(Path('.').glob('chapter_*.md')):
            print(f"\n=== {chapter_file.name} ===")
            issues = validate_chapter(chapter_file)
            if issues:
                for issue in issues:
                    print(f"  {issue}")
            else:
                print("  All validation checks passed!")

if __name__ == "__main__":
    main()