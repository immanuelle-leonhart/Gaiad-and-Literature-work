#!/usr/bin/env python3
"""
Comprehensive Poetry Analysis Tool for Gaiad Epic
Analyzes all chapters for meter, rhyme, and grammatical issues
"""

import os
import re
import glob
from collections import defaultdict
import argparse

class PoetryAnalyzer:
    def __init__(self, epic_dir="epic"):
        self.epic_dir = epic_dir
        self.issues = defaultdict(list)
        
        # Common patterns that indicate poetry issues
        self.patterns = {
            'meter_issues': [
                r'\blifelong\b',  # Should be "life long" for proper meter
                r'For me and you\.$',  # Missing syllable, should be "For me and you today."
                r'And stay alive$',  # Incomplete line
                r'\bwho.*errs\b',  # Should be "err" not "errs"
                r'\bwhole lifelong\b',  # Should be "whole life long"
                r'\bthroughout.*lifelong\b',  # Meter issues
            ],
            'rhyme_scheme_issues': [
                r'different way$',  # Often missing article "a different way"
                r'different goal',  # Often missing article "a different goal"
                r'sweet kiss$',  # Weak rhyme
                r'bright power$',  # Weak internal rhyme
            ],
            'grammar_issues': [
                r'\berrs\b',  # Should be "err"
                r'chose different',  # Missing article
                r'set on different',  # Missing article
                r'the airbreather$',  # Missing comma or article
            ],
            'syllable_count_issues': [
                r'^.{1,30}$',  # Lines that seem too short for iambic pentameter
                r'^.{70,}$',  # Lines that seem too long
            ]
        }
    
    def count_syllables(self, word):
        """Rough syllable counting for meter analysis"""
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
        
        # Minimum of 1 syllable per word
        return max(1, syllables)
    
    def analyze_line_meter(self, line):
        """Analyze if a line follows iambic pentameter (roughly 10 syllables)"""
        # Remove punctuation for syllable counting
        clean_line = re.sub(r'[^\w\s]', '', line)
        words = clean_line.split()
        
        total_syllables = sum(self.count_syllables(word) for word in words)
        
        # Iambic pentameter should be around 10 syllables
        if total_syllables < 8 or total_syllables > 12:
            return False, total_syllables
        return True, total_syllables
    
    def check_rhyme_scheme(self, stanza_lines):
        """Check if a 4-line stanza follows ABAB rhyme scheme"""
        if len(stanza_lines) != 4:
            return True  # Only check 4-line stanzas
        
        # Extract last word from each line
        last_words = []
        for line in stanza_lines:
            clean_line = re.sub(r'[^\w\s]', '', line.strip())
            words = clean_line.split()
            if words:
                last_words.append(words[-1].lower())
        
        if len(last_words) != 4:
            return False
        
        # Simple rhyme detection (same ending sounds)
        def get_rhyme_pattern(word):
            if len(word) < 2:
                return word
            return word[-2:]  # Last 2 characters as rough rhyme indicator
        
        patterns = [get_rhyme_pattern(word) for word in last_words]
        
        # ABAB pattern: 1st and 3rd should rhyme, 2nd and 4th should rhyme
        return patterns[0] == patterns[2] and patterns[1] == patterns[3]
    
    def analyze_file(self, filepath):
        """Analyze a single chapter file"""
        chapter_name = os.path.basename(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.issues[chapter_name].append(f"Error reading file: {e}")
            return
        
        lines = content.split('\n')
        
        # Remove line numbers and arrows if present
        clean_lines = []
        for line in lines:
            # Remove patterns like "   123→"
            clean_line = re.sub(r'^\s*\d+→', '', line)
            if clean_line.strip():
                clean_lines.append(clean_line.strip())
        
        # Check for pattern issues
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                for i, line in enumerate(clean_lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        self.issues[chapter_name].append(
                            f"Line {i} ({category}): {line.strip()[:50]}..."
                        )
        
        # Check meter for each line
        for i, line in enumerate(clean_lines, 1):
            if line.strip():
                is_good_meter, syllable_count = self.analyze_line_meter(line)
                if not is_good_meter:
                    self.issues[chapter_name].append(
                        f"Line {i} (meter - {syllable_count} syllables): {line.strip()[:50]}..."
                    )
        
        # Check rhyme scheme in 4-line groups
        stanza = []
        stanza_start = 1
        
        for i, line in enumerate(clean_lines):
            if line.strip():
                stanza.append(line.strip())
                
                if len(stanza) == 4:
                    if not self.check_rhyme_scheme(stanza):
                        self.issues[chapter_name].append(
                            f"Lines {stanza_start}-{stanza_start+3} (rhyme scheme): ABAB pattern issue"
                        )
                    stanza = []
                    stanza_start = i + 2
    
    def analyze_all_chapters(self):
        """Analyze all chapter files"""
        pattern = os.path.join(self.epic_dir, "chapter_*.md")
        files = glob.glob(pattern)
        files.sort()  # Process in order
        
        print(f"Analyzing {len(files)} chapter files...")
        
        for filepath in files:
            print(f"Processing {os.path.basename(filepath)}...")
            self.analyze_file(filepath)
    
    def generate_report(self, output_file="poetry_analysis_report.md"):
        """Generate a comprehensive report of all issues found"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Gaiad Epic Poetry Analysis Report\n\n")
            f.write(f"Total chapters analyzed: {len(self.issues)}\n\n")
            
            # Summary statistics
            total_issues = sum(len(issues) for issues in self.issues.values())
            f.write(f"Total issues found: {total_issues}\n\n")
            
            # Issues by category
            categories = defaultdict(int)
            for chapter_issues in self.issues.values():
                for issue in chapter_issues:
                    for category in ['meter', 'rhyme_scheme', 'grammar', 'syllable_count']:
                        if category in issue:
                            categories[category] += 1
                            break
            
            f.write("## Issues by Category\n\n")
            for category, count in categories.items():
                f.write(f"- {category}: {count}\n")
            f.write("\n")
            
            # Detailed issues by chapter
            f.write("## Detailed Issues by Chapter\n\n")
            
            for chapter in sorted(self.issues.keys()):
                if self.issues[chapter]:
                    f.write(f"### {chapter}\n\n")
                    f.write(f"Issues found: {len(self.issues[chapter])}\n\n")
                    
                    for issue in self.issues[chapter]:
                        f.write(f"- {issue}\n")
                    f.write("\n")
                else:
                    f.write(f"### {chapter}\n\nNo issues found.\n\n")
        
        print(f"Report generated: {output_file}")
    
    def generate_fixes(self, output_file="poetry_fixes.md"):
        """Generate suggested fixes for common issues"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Suggested Poetry Fixes\n\n")
            
            common_fixes = {
                'lifelong': 'life long',
                'For me and you.': 'For me and you today.',
                'chose different': 'chose a different',
                'set on different': 'set on a different',
                'who errs': 'who err',
                'whole lifelong': 'whole life long',
            }
            
            f.write("## Common Pattern Fixes\n\n")
            for old, new in common_fixes.items():
                f.write(f"- Replace `{old}` with `{new}`\n")
            
            f.write("\n## Chapter-specific Recommendations\n\n")
            
            for chapter in sorted(self.issues.keys()):
                if self.issues[chapter]:
                    meter_issues = [i for i in self.issues[chapter] if 'meter' in i]
                    rhyme_issues = [i for i in self.issues[chapter] if 'rhyme' in i]
                    
                    if meter_issues or rhyme_issues:
                        f.write(f"### {chapter}\n\n")
                        
                        if meter_issues:
                            f.write("**Meter Issues:**\n")
                            for issue in meter_issues[:5]:  # Show first 5
                                f.write(f"- {issue}\n")
                            if len(meter_issues) > 5:
                                f.write(f"- ... and {len(meter_issues) - 5} more\n")
                            f.write("\n")
                        
                        if rhyme_issues:
                            f.write("**Rhyme Issues:**\n")
                            for issue in rhyme_issues[:3]:  # Show first 3
                                f.write(f"- {issue}\n")
                            if len(rhyme_issues) > 3:
                                f.write(f"- ... and {len(rhyme_issues) - 3} more\n")
                            f.write("\n")
        
        print(f"Fixes generated: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Analyze Gaiad Epic poetry')
    parser.add_argument('--epic-dir', default='epic', help='Directory containing chapter files')
    parser.add_argument('--report', default='poetry_analysis_report.md', help='Output report file')
    parser.add_argument('--fixes', default='poetry_fixes.md', help='Output fixes file')
    
    args = parser.parse_args()
    
    # Change to the correct directory
    os.chdir('C:\\Users\\Immanuelle\\Documents\\Github\\Gaiad-Genealogy')
    
    analyzer = PoetryAnalyzer(args.epic_dir)
    
    print("Starting comprehensive poetry analysis...")
    analyzer.analyze_all_chapters()
    
    print("Generating reports...")
    analyzer.generate_report(args.report)
    analyzer.generate_fixes(args.fixes)
    
    print("Analysis complete!")
    
    # Print summary
    total_issues = sum(len(issues) for issues in analyzer.issues.values())
    chapters_with_issues = len([c for c, issues in analyzer.issues.items() if issues])
    
    print(f"\nSUMMARY:")
    print(f"- Total chapters: {len(analyzer.issues)}")
    print(f"- Chapters with issues: {chapters_with_issues}")
    print(f"- Total issues found: {total_issues}")
    print(f"- Average issues per chapter: {total_issues / len(analyzer.issues):.1f}")

if __name__ == "__main__":
    main()