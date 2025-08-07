#!/usr/bin/env python3
"""
Comprehensive Poetry Fixer for Gaiad Epic
Systematically fixes common poetry issues across all chapters
"""

import os
import re
import glob
import shutil
from collections import defaultdict

class PoetryFixer:
    def __init__(self, epic_dir="epic"):
        self.epic_dir = epic_dir
        self.fixes_applied = defaultdict(list)
        
        # Define systematic fixes
        self.pattern_fixes = [
            # Meter fixes - lifelong patterns
            (r'\blifelong\b', 'life long'),
            (r'\bwhole lifelong\b', 'whole life long'),
            (r'\bthroughout.*?lifelong', lambda m: m.group().replace('lifelong', 'life long')),
            
            # Common ending fixes
            (r'For me and you\.$', 'For me and you today.'),
            
            # Grammar fixes
            (r'\bwho errs\b', 'who err'),
            (r'\berrs\b', 'err'),
            
            # Article fixes
            (r'chose different\b', 'chose a different'),
            (r'set on different\b', 'set on a different'),
            (r'found different\b', 'found a different'),
            (r'took different\b', 'took a different'),
            
            # Common meter issues
            (r'\bthe airbreather$', 'the great airbreather'),
            (r'And stay alive$', 'And stay alive below'),
            (r'sweet kiss$', 'sweetest bliss'),
            (r'bright power$', 'bright power divine'),
            
            # Fix "through night" -> "through the night"
            (r'through night\b', 'through the night'),
            (r'day and through night\b', 'day and through the night'),
            
            # Common syllable fixes
            (r'\bSiphonogloss\b', 'Siphon'),  # Too many syllables
        ]
        
        # More complex fixes that need context
        self.contextual_fixes = [
            # Fix incomplete stanzas
            (r'(\w+)\n(\w+)\nBut (\w+)', r'\1,\n\2,\nBut \3'),
        ]
    
    def backup_file(self, filepath):
        """Create backup of original file"""
        backup_path = filepath + ".backup"
        if not os.path.exists(backup_path):
            shutil.copy2(filepath, backup_path)
    
    def count_syllables(self, word):
        """Rough syllable counting"""
        word = word.lower().strip()
        if not word:
            return 0
        
        # Handle common endings
        if word.endswith('ed') and not word.endswith(('ded', 'ted', 'led', 'red', 'sed')):
            word = word[:-2]
        
        # Count vowel groups
        vowels = 'aeiouy'
        syllables = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllables += 1
            prev_was_vowel = is_vowel
        
        return max(1, syllables)
    
    def fix_meter_line(self, line):
        """Try to fix meter issues in a single line"""
        # Remove line numbers if present
        clean_line = re.sub(r'^\s*\d+→', '', line).strip()
        
        if not clean_line:
            return line
        
        # Count syllables
        words = re.findall(r'\b\w+\b', clean_line)
        syllable_count = sum(self.count_syllables(word) for word in words)
        
        # If too short, try adding articles or descriptive words
        if syllable_count < 8:
            # Add articles where missing
            clean_line = re.sub(r'\b(chose|found|took|made) (\w+) way\b', r'\1 a \2 way', clean_line)
            clean_line = re.sub(r'\b(set on|aimed for) (\w+) goal\b', r'\1 a \2 goal', clean_line)
            
            # Add "great" or "bright" as descriptive words
            if syllable_count < 7:
                clean_line = re.sub(r'\b(\w+) the (\w+)$', r'\1 the great \2', clean_line)
        
        # If too long, try contractions or shorter words
        elif syllable_count > 12:
            # Use contractions
            clean_line = re.sub(r'\bthey would\b', "they'd", clean_line)
            clean_line = re.sub(r'\bhe would\b', "he'd", clean_line)
            clean_line = re.sub(r'\bshe would\b', "she'd", clean_line)
            clean_line = re.sub(r'\bit would\b', "it'd", clean_line)
            clean_line = re.sub(r'\bwho would\b', "who'd", clean_line)
        
        return line.replace(clean_line, clean_line) if clean_line in line else line
    
    def fix_file(self, filepath):
        """Fix poetry issues in a single file"""
        chapter_name = os.path.basename(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {chapter_name}: {e}")
            return
        
        original_content = content
        
        # Apply pattern fixes
        for pattern, replacement in self.pattern_fixes:
            if callable(replacement):
                # Handle lambda replacements
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in reversed(matches):  # Reverse to maintain indices
                    new_text = replacement(match)
                    content = content[:match.start()] + new_text + content[match.end():]
                    self.fixes_applied[chapter_name].append(f"Pattern fix: {pattern}")
            else:
                # Handle string replacements
                new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                if new_content != content:
                    count = len(re.findall(pattern, content, re.IGNORECASE))
                    self.fixes_applied[chapter_name].append(f"Pattern fix ({count}x): {pattern} -> {replacement}")
                    content = new_content
        
        # Apply contextual fixes
        for pattern, replacement in self.contextual_fixes:
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.IGNORECASE)
            if new_content != content:
                self.fixes_applied[chapter_name].append(f"Contextual fix: {pattern}")
                content = new_content
        
        # Fix individual lines for meter
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if line.strip() and not re.match(r'^\s*#', line):  # Skip headers
                fixed_line = self.fix_meter_line(line)
                if fixed_line != line:
                    self.fixes_applied[chapter_name].append(f"Meter fix: {line.strip()[:30]}...")
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Only write if changes were made
        if content != original_content:
            self.backup_file(filepath)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Fixed {len(self.fixes_applied[chapter_name])} issues in {chapter_name}")
        else:
            print(f"No fixes needed for {chapter_name}")
    
    def fix_all_chapters(self):
        """Fix all chapter files"""
        pattern = os.path.join(self.epic_dir, "chapter_*.md")
        files = glob.glob(pattern)
        files = [f for f in files if not f.endswith('_DRAFT.md')]  # Skip draft files
        files.sort()
        
        print(f"Fixing {len(files)} chapter files...")
        
        for filepath in files:
            self.fix_file(filepath)
    
    def generate_fix_report(self, output_file="poetry_fixes_applied.md"):
        """Generate report of fixes applied"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Poetry Fixes Applied Report\n\n")
            
            total_fixes = sum(len(fixes) for fixes in self.fixes_applied.values())
            f.write(f"Total fixes applied: {total_fixes}\n")
            f.write(f"Files modified: {len(self.fixes_applied)}\n\n")
            
            for chapter in sorted(self.fixes_applied.keys()):
                if self.fixes_applied[chapter]:
                    f.write(f"## {chapter}\n\n")
                    f.write(f"Fixes applied: {len(self.fixes_applied[chapter])}\n\n")
                    
                    for fix in self.fixes_applied[chapter]:
                        f.write(f"- {fix}\n")
                    f.write("\n")
        
        print(f"Fix report generated: {output_file}")

def main():
    # Change to correct directory
    os.chdir('C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy')
    
    fixer = PoetryFixer()
    
    print("Starting comprehensive poetry fixes...")
    fixer.fix_all_chapters()
    
    print("\nGenerating fix report...")
    fixer.generate_fix_report()
    
    print("Poetry fixes complete!")
    
    # Print summary
    total_fixes = sum(len(fixes) for fixes in fixer.fixes_applied.values())
    files_modified = len([c for c, fixes in fixer.fixes_applied.items() if fixes])
    
    print(f"\nSUMMARY:")
    print(f"- Files processed: {len(glob.glob('epic/chapter_*.md')) - len(glob.glob('epic/chapter_*_DRAFT.md'))}")
    print(f"- Files modified: {files_modified}")
    print(f"- Total fixes applied: {total_fixes}")
    if files_modified > 0:
        print(f"- Average fixes per file: {total_fixes / files_modified:.1f}")

if __name__ == "__main__":
    main()