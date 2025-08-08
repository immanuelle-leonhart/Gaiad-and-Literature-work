#!/usr/bin/env python3
"""
Analyze GEDCOM file content to identify what could be trimmed for size reduction
"""

import re
import logging
from collections import defaultdict, Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GedcomContentAnalyzer:
    def __init__(self):
        self.stats = {
            'total_lines': 0,
            'record_types': defaultdict(int),
            'note_content_types': defaultdict(int),
            'line_types': defaultdict(int),
            'large_notes': [],
            'html_content': 0,
            'empty_lines': 0,
            'source_citations': 0,
            'uid_lines': 0,
            'rin_lines': 0,
            'technical_metadata': 0,
            'event_updates': 0,
            'long_lines': 0,
            'duplicate_content': defaultdict(int),
            'content_categories': defaultdict(int)
        }
        
    def analyze_file(self, filename):
        """Comprehensive analysis of GEDCOM file content"""
        logger.info(f"Analyzing content of {filename}")
        
        with open(filename, 'r', encoding='utf-8-sig', errors='ignore') as f:
            current_note_size = 0
            current_note_lines = []
            in_note = False
            
            for line_num, line in enumerate(f, 1):
                if line_num % 100000 == 0:
                    logger.info(f"Processed {line_num:,} lines...")
                
                line = line.rstrip()
                self.stats['total_lines'] += 1
                
                # Basic line analysis
                if not line.strip():
                    self.stats['empty_lines'] += 1
                    continue
                
                if len(line) > 500:
                    self.stats['long_lines'] += 1
                
                # Parse GEDCOM structure
                parts = line.split(' ', 2)
                if len(parts) < 2:
                    continue
                
                try:
                    level = int(parts[0])
                    tag = parts[1]
                    value = parts[2] if len(parts) > 2 else ""
                except ValueError:
                    continue
                
                self.stats['line_types'][f"Level {level}"] += 1
                
                # Record type analysis
                if level == 0 and '@' in tag:
                    record_type = parts[2] if len(parts) > 2 else ""
                    self.stats['record_types'][record_type] += 1
                
                # Analyze different content types
                self.analyze_line_content(level, tag, value, line)
                
                # Note section analysis
                if tag == 'NOTE':
                    in_note = True
                    current_note_size = len(value)
                    current_note_lines = [line]
                elif tag in ['CONT', 'CONC'] and in_note:
                    current_note_size += len(value)
                    current_note_lines.append(line)
                else:
                    if in_note and current_note_size > 1000:
                        self.stats['large_notes'].append({
                            'line': line_num - len(current_note_lines),
                            'size': current_note_size,
                            'preview': current_note_lines[0][:100] + "..." if current_note_lines else ""
                        })
                    in_note = False
                    current_note_size = 0
                    current_note_lines = []
        
        self.generate_report()
    
    def analyze_line_content(self, level, tag, value, full_line):
        """Analyze specific line content for bloat"""
        
        # Technical metadata that could be removed
        if tag in ['_UID', 'RIN', '_RIN']:
            self.stats['uid_lines'] += 1
            self.stats['technical_metadata'] += 1
        
        # Source citations
        if tag == 'SOUR':
            self.stats['source_citations'] += 1
        
        # Event update timestamps
        if tag == '_UPD' or 'UPD' in value:
            self.stats['event_updates'] += 1
        
        # HTML content
        if '<' in value and '>' in value:
            self.stats['html_content'] += 1
            if '<p>' in value or '</p>' in value:
                self.stats['content_categories']['HTML paragraphs'] += 1
            if 'style=' in value:
                self.stats['content_categories']['HTML with styles'] += 1
        
        # Note content analysis
        if tag == 'NOTE' or tag in ['CONT', 'CONC']:
            self.analyze_note_content(value)
        
        # Track duplicate content
        if len(value) > 50:
            self.stats['duplicate_content'][value] += 1
    
    def analyze_note_content(self, content):
        """Analyze NOTE content for different types"""
        
        content_lower = content.lower()
        
        # Import errors and technical notes
        if 'could not import' in content_lower or 'line ignored' in content_lower:
            self.stats['content_categories']['Import errors'] += 1
        
        # Geni-specific content
        if '{geni:' in content or 'geni.com' in content:
            self.stats['content_categories']['Geni metadata'] += 1
        
        # Wikipedia content (remaining)
        if 'wikipedia' in content_lower:
            self.stats['content_categories']['Wikipedia references'] += 1
        
        # Long biographical content
        if len(content) > 200 and any(word in content_lower for word in ['born', 'died', 'was a', 'known for']):
            self.stats['content_categories']['Long biographical notes'] += 1
        
        # URLs
        if 'http://' in content or 'https://' in content:
            self.stats['content_categories']['URLs'] += 1
        
        # Empty HTML
        if content.strip() in ['<p></p>', '<p>', '</p>', '<br>', '<br/>']:
            self.stats['content_categories']['Empty HTML'] += 1
    
    def generate_report(self):
        """Generate comprehensive analysis report to file"""
        logger.info("=== GEDCOM CONTENT ANALYSIS REPORT ===")
        
        with open("gedcom_analysis_report.txt", 'w', encoding='utf-8') as f:
            f.write("=== GEDCOM CONTENT ANALYSIS REPORT ===\n\n")
            
            f.write("=== FILE OVERVIEW ===\n")
            f.write(f"Total lines: {self.stats['total_lines']:,}\n")
            f.write(f"Empty lines: {self.stats['empty_lines']:,}\n")
            f.write(f"Long lines (>500 chars): {self.stats['long_lines']:,}\n\n")
            
            f.write("=== TOP RECORD TYPES ===\n")
            top_records = sorted(self.stats['record_types'].items(), key=lambda x: x[1], reverse=True)[:20]
            for record_type, count in top_records:
                f.write(f"{record_type}: {count:,}\n")
            
            f.write(f"\n=== PLACE NAMES (_PLAC records) ===\n")
            place_records = [(k, v) for k, v in self.stats['record_types'].items() if k.startswith('_PLAC')]
            f.write(f"Total unique place names: {len(place_records):,}\n")
            f.write("Most common places:\n")
            place_records.sort(key=lambda x: x[1], reverse=True)
            for place, count in place_records[:20]:
                clean_place = place.replace('_PLAC ', '')[:80] + ('...' if len(place) > 80 else '')
                f.write(f"  {count} times: {clean_place}\n")
            
            f.write("\n=== POTENTIAL BLOAT CATEGORIES ===\n")
            bloat_categories = [
                ("Technical metadata (_UID, RIN)", self.stats['technical_metadata']),
                ("Source citations", self.stats['source_citations']),
                ("Event updates", self.stats['event_updates']),
                ("HTML content", self.stats['html_content']),
                ("Empty lines", self.stats['empty_lines']),
                ("Large notes (>1KB)", len(self.stats['large_notes'])),
                ("Unique place names", len(place_records))
            ]
            
            total_bloat = 0
            for category, count in bloat_categories:
                f.write(f"{category}: {count:,}\n")
                total_bloat += count
            
            f.write(f"\nTotal potential bloat lines: {total_bloat:,} ({(total_bloat/self.stats['total_lines'])*100:.1f}%)\n\n")
            
            f.write("=== NOTE CONTENT CATEGORIES ===\n")
            for category, count in sorted(self.stats['content_categories'].items(), key=lambda x: x[1], reverse=True):
                f.write(f"{category}: {count:,}\n")
            
            f.write("\n=== LARGEST NOTES ===\n")
            largest_notes = sorted(self.stats['large_notes'], key=lambda x: x['size'], reverse=True)[:10]
            for i, note in enumerate(largest_notes, 1):
                f.write(f"{i}. Line {note['line']}: {note['size']:,} chars\n")
                f.write(f"   Preview: {note['preview']}\n")
            
            f.write("\n=== SIZE REDUCTION RECOMMENDATIONS ===\n")
            savings_estimates = [
                ("Remove technical metadata (_UID, RIN)", self.stats['technical_metadata'], "High", "Safe to remove - just internal IDs"),
                ("Consolidate place names", len(place_records), "High", "Many duplicates with slight variations"),
                ("Remove import error notes", self.stats['content_categories'].get('Import errors', 0), "High", "Not genealogically useful"),
                ("Remove empty HTML tags", self.stats['content_categories'].get('Empty HTML', 0), "High", "Just empty <p></p> tags"),
                ("Compress large biographical notes", len(self.stats['large_notes']), "Medium", "Keep essential info only"),
                ("Remove event update timestamps", self.stats['event_updates'], "Medium", "Internal tracking data"),
                ("Remove HTML styling", self.stats['content_categories'].get('HTML with styles', 0), "Low", "Formatting only"),
            ]
            
            for description, count, priority, explanation in savings_estimates:
                if count > 0:
                    percent = (count / self.stats['total_lines']) * 100
                    f.write(f"{priority}: {description} - {count:,} lines ({percent:.1f}%)\n")
                    f.write(f"    Reason: {explanation}\n")
        
        print(f"Analysis complete! Report written to gedcom_analysis_report.txt")
        print(f"Total lines analyzed: {self.stats['total_lines']:,}")
        print(f"Major bloat sources found:")
        print(f"- Technical metadata: {self.stats['technical_metadata']:,} lines")
        print(f"- Unique place names: {len([k for k in self.stats['record_types'] if k.startswith('_PLAC')]):,}")
        print(f"- Source citations: {self.stats['source_citations']:,} lines")

def main():
    analyzer = GedcomContentAnalyzer()
    analyzer.analyze_file("new_gedcoms/source gedcoms/merged_attempt.ged")

if __name__ == "__main__":
    main()