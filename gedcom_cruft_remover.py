#!/usr/bin/env python3
"""
GEDCOM Cruft Remover
Removes bloat from GEDCOM files while preserving essential genealogical data
"""

import re
import os
import logging
from typing import List, Set

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GedcomCruftRemover:
    def __init__(self):
        self.stats = {
            'lines_processed': 0,
            'lines_removed': 0,
            'uid_rin_removed': 0,
            'source_citations_removed': 0,
            'event_updates_removed': 0,
            'empty_html_removed': 0,
            'import_errors_removed': 0,
            'large_notes_compressed': 0,
            'html_cleaned': 0,
            'original_size': 0,
            'cleaned_size': 0
        }
        
        # Tags to completely remove
        self.remove_tags = {
            '_UID',     # Internal UIDs
            'RIN',      # Record identification numbers
            '_RIN'      # More record IDs
        }
        
        # Event types that are just update timestamps
        self.remove_event_types = {
            '_UPD',     # Update events
            'UPD'       # More update events
        }
        
        # Import error patterns
        self.import_error_patterns = [
            r'could not import',
            r'line ignored',
            r'tag recognised but not supported',
            r'records not imported',
            r'line \d+:'
        ]
        
        # HTML patterns to clean
        self.empty_html_patterns = [
            r'<p></p>',
            r'<p>\s*</p>',
            r'<br\s*/?>\s*',
            r'<div>\s*</div>',
            r'<span>\s*</span>'
        ]
    
    def should_remove_line(self, line: str) -> bool:
        """Determine if a line should be completely removed"""
        parts = line.split(' ', 2)
        if len(parts) < 2:
            return False
        
        try:
            level = int(parts[0])
            tag = parts[1]
            value = parts[2] if len(parts) > 2 else ""
        except ValueError:
            return False
        
        # Remove technical metadata
        if tag in self.remove_tags:
            return True
        
        # Remove event updates
        if tag == 'TYPE' and value in self.remove_event_types:
            return True
        
        # Remove update events entirely
        if level == 1 and tag == 'EVEN' and len(parts) == 2:
            # This might be followed by TYPE _UPD, so we'll mark for context removal
            return False  # Handle in context
        
        return False
    
    def clean_note_content(self, content: str) -> str:
        """Clean note content while preserving essential information"""
        if not content:
            return content
        
        original_length = len(content)
        
        # Remove import errors
        for pattern in self.import_error_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Clean empty HTML
        for pattern in self.empty_html_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Remove excessive whitespace but preserve structure
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Multiple blank lines -> double
        content = re.sub(r'[ \t]+', ' ', content)  # Multiple spaces -> single
        content = content.strip()
        
        # If content is extremely long (>50KB), try to compress it
        if len(content) > 50000:
            # Try to extract just the essential biographical info
            compressed = self.compress_large_note(content)
            if len(compressed) < len(content) * 0.7:  # Only if significant reduction
                content = compressed
                self.stats['large_notes_compressed'] += 1
        
        if len(content) < original_length:
            self.stats['html_cleaned'] += 1
        
        return content
    
    def compress_large_note(self, content: str) -> str:
        """Compress very large notes while keeping essential information"""
        lines = content.split('\n')
        essential_lines = []
        
        # Keep lines that seem genealogically important
        important_patterns = [
            r'\b(born?|birth|b\.)\b.*\d{3,4}',  # Birth dates
            r'\b(died?|death|d\.)\b.*\d{3,4}',  # Death dates  
            r'\b(married?|marriage|m\.)\b',      # Marriage info
            r'\b(son|daughter|child) of\b',      # Parent relationships
            r'\b(father|mother|parent) of\b',    # Child relationships
            r'\bwife of\b|\bhusband of\b',       # Spouse relationships
            r'\bking|queen|duke|count|lord\b',   # Titles
            r'https?://\S+',                     # URLs
            r'wikipedia\.org',                   # Wikipedia references
            r'geni\.com'                         # Geni references
        ]
        
        for line in lines[:100]:  # Only check first 100 lines to avoid huge processing
            line = line.strip()
            if not line:
                continue
            
            # Keep short lines (likely important)
            if len(line) < 200:
                essential_lines.append(line)
                continue
            
            # Keep lines matching important patterns
            for pattern in important_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    essential_lines.append(line)
                    break
        
        # If we couldn't compress much, return original
        compressed = '\n'.join(essential_lines)
        if len(compressed) > len(content) * 0.8:
            return content
        
        return compressed + '\n\n[Note: Large biographical content compressed for space]'
    
    def clean_source_citation(self, line: str) -> bool:
        """Determine if source citation should be kept or removed"""
        # Keep source citations that reference external sources
        # Remove internal/technical source citations
        
        if 'SOUR @S' in line and line.count('@') == 2:
            # This is a reference to a source record, keep it
            return False
        
        # Remove technical source metadata
        parts = line.split(' ', 2)
        if len(parts) >= 2 and parts[1] in ['QUAY', '_DESCRIPTION']:
            return True  # Remove quality and description metadata
        
        return False
    
    def process_event_block(self, lines: List[str], start_idx: int) -> tuple[List[str], int]:
        """Process an event block and remove update events"""
        if start_idx >= len(lines):
            return [], start_idx
        
        current_line = lines[start_idx]
        if not (current_line.strip().startswith('1 EVEN') and len(current_line.split()) == 2):
            return [current_line], start_idx + 1
        
        # Look ahead to see if this is an update event
        event_lines = [current_line]
        idx = start_idx + 1
        
        is_update_event = False
        while idx < len(lines):
            line = lines[idx]
            if not (line.startswith('2 ') or line.startswith('3 ')):
                break
            
            if line.strip().startswith('2 TYPE _UPD') or line.strip().startswith('2 TYPE UPD'):
                is_update_event = True
            
            event_lines.append(line)
            idx += 1
        
        if is_update_event:
            self.stats['event_updates_removed'] += len(event_lines)
            return [], idx  # Remove entire event block
        
        return event_lines, idx
    
    def clean_gedcom_file(self, input_file: str, output_file: str):
        """Clean the GEDCOM file"""
        logger.info(f"Cleaning GEDCOM file: {input_file}")
        
        self.stats['original_size'] = os.path.getsize(input_file)
        
        with open(input_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
            lines = f.readlines()
        
        logger.info(f"Processing {len(lines):,} lines...")
        
        cleaned_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip()
            self.stats['lines_processed'] += 1
            
            if self.stats['lines_processed'] % 100000 == 0:
                logger.info(f"Processed {self.stats['lines_processed']:,} lines...")
            
            # Check for complete line removal
            if self.should_remove_line(line):
                self.stats['lines_removed'] += 1
                self.stats['uid_rin_removed'] += 1
                i += 1
                continue
            
            # Handle event blocks specially
            if line.strip().startswith('1 EVEN') and len(line.split()) == 2:
                event_lines, next_i = self.process_event_block(lines, i)
                cleaned_lines.extend(event_lines)
                i = next_i
                continue
            
            # Handle source citations
            if self.clean_source_citation(line):
                self.stats['lines_removed'] += 1
                self.stats['source_citations_removed'] += 1
                i += 1
                continue
            
            # Handle notes with content cleaning
            if line.startswith('1 NOTE ') or line.startswith('2 CONT ') or line.startswith('2 CONC '):
                # Clean the note content
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    tag = parts[1]
                    content = parts[2]
                    
                    # Check for import errors
                    is_import_error = any(re.search(pattern, content, re.IGNORECASE) 
                                        for pattern in self.import_error_patterns)
                    
                    if is_import_error:
                        self.stats['lines_removed'] += 1
                        self.stats['import_errors_removed'] += 1
                        i += 1
                        continue
                    
                    # Clean the content
                    cleaned_content = self.clean_note_content(content)
                    
                    # Remove if content became empty
                    if not cleaned_content.strip():
                        self.stats['lines_removed'] += 1
                        self.stats['empty_html_removed'] += 1
                        i += 1
                        continue
                    
                    # Reconstruct line if content changed
                    if cleaned_content != content:
                        line = f"{parts[0]} {tag} {cleaned_content}"
                
                cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
            
            i += 1
        
        # Write cleaned file
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in cleaned_lines:
                f.write(line + '\n')
        
        self.stats['cleaned_size'] = os.path.getsize(output_file)
        
        self.report_stats(input_file, output_file)
    
    def report_stats(self, input_file: str, output_file: str):
        """Report cleaning statistics"""
        original_mb = self.stats['original_size'] / 1024 / 1024
        cleaned_mb = self.stats['cleaned_size'] / 1024 / 1024
        reduction_mb = original_mb - cleaned_mb
        reduction_pct = (reduction_mb / original_mb) * 100 if original_mb > 0 else 0
        
        logger.info("=== GEDCOM CRUFT REMOVAL RESULTS ===")
        logger.info(f"Original file: {input_file}")
        logger.info(f"Cleaned file: {output_file}")
        logger.info(f"Lines processed: {self.stats['lines_processed']:,}")
        logger.info(f"Lines removed: {self.stats['lines_removed']:,}")
        logger.info("")
        logger.info("Removal breakdown:")
        logger.info(f"  Source citations removed: {self.stats['source_citations_removed']:,}")
        logger.info(f"  Technical metadata (_UID, RIN): {self.stats['uid_rin_removed']:,}")
        logger.info(f"  Event updates removed: {self.stats['event_updates_removed']:,}")
        logger.info(f"  Import error notes: {self.stats['import_errors_removed']:,}")
        logger.info(f"  Empty HTML tags: {self.stats['empty_html_removed']:,}")
        logger.info(f"  Large notes compressed: {self.stats['large_notes_compressed']:,}")
        logger.info(f"  Notes with HTML cleaned: {self.stats['html_cleaned']:,}")
        logger.info("")
        logger.info("File size results:")
        logger.info(f"  Original size: {original_mb:.1f} MB")
        logger.info(f"  Cleaned size: {cleaned_mb:.1f} MB")
        logger.info(f"  Size reduction: {reduction_mb:.1f} MB ({reduction_pct:.1f}%)")

def main():
    input_file = "new_gedcoms/source gedcoms/merged_attempt.ged"
    output_file = "new_gedcoms/source gedcoms/merged_attempt_cleaned.ged"
    
    cleaner = GedcomCruftRemover()
    cleaner.clean_gedcom_file(input_file, output_file)
    
    print(f"\nGEDCOM cruft removal completed!")
    print(f"Cleaned file: {output_file}")

if __name__ == "__main__":
    main()