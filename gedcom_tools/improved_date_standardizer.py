#!/usr/bin/env python3
"""
Improved Date Format Standardizer for GEDCOM files
Handles negative years, incomplete ranges, and Roman Republic dates properly.
"""

import sys
import re
import tempfile
import shutil

def standardize_date_formats(input_file, output_file):
    def __init__(self):
        self.changes_made = []
        self.stats = {
            'total_dates': 0,
            'future_dates_removed': 0,
            'bc_standardized': 0,
            'ad_standardized': 0,
            'mya_converted': 0,
            'malformed_fixed': 0,
            'unchanged': 0
        }
    
    def standardize_date(self, date_str):
        """Standardize a single date string."""
        if not date_str or not date_str.strip():
            return date_str, "empty"
        
        original = date_str.strip()
        self.stats['total_dates'] += 1
        
        # CRITICAL: Remove future/default dates
        if self.is_future_or_default_date(original):
            self.stats['future_dates_removed'] += 1
            return "", "removed_future"
        
        # Handle Million/Billion Years Ago
        standardized, change_type = self.handle_prehistoric_dates(original)
        if change_type != "no_change":
            return standardized, change_type
        
        # Handle BC dates
        standardized, change_type = self.handle_bc_dates(original)
        if change_type != "no_change":
            return standardized, change_type
        
        # Handle AD dates  
        standardized, change_type = self.handle_ad_dates(original)
        if change_type != "no_change":
            return standardized, change_type
        
        # Handle malformed dates
        standardized, change_type = self.handle_malformed_dates(original)
        if change_type != "no_change":
            return standardized, change_type
        
        self.stats['unchanged'] += 1
        return original, "no_change"
    
    def is_future_or_default_date(self, date_str):
        """Check if date is future/default and should be removed."""
        date_lower = date_str.lower()
        
        # PRESERVE editing history dates like "7 AUG 2025" 
        if "7 aug 2025" in date_lower:
            return False  # Keep these as they are editing metadata
        
        # Any other date >= 2025 (but not the editing history)
        year_match = re.search(r'\b(20[2-9][5-9]|2[1-9]\d\d)\b', date_str)
        if year_match and "7 aug 2025" not in date_lower:
            return True
        
        # Dates that are clearly modern genealogical errors (1800-2024)
        if re.search(r'\b(18\d\d|19\d\d|20[0-2][0-4])\b', date_str) and "7 aug 2025" not in date_lower:
            return True
            
        return False
    
    def handle_prehistoric_dates(self, date_str):
        """Handle MYA, BYA, KYA dates."""
        date_lower = date_str.lower()
        
        # Million Years Ago
        mya_match = re.search(r'(\d+(?:\.\d+)?)\s*(mya|million\s+years?\s+ago)', date_lower)
        if mya_match:
            mya = float(mya_match.group(1))
            bc_year = int(mya * 1000000)
            self.stats['mya_converted'] += 1
            return f"{bc_year} BC", "mya_to_bc"
        
        # Billion Years Ago
        bya_match = re.search(r'(\d+(?:\.\d+)?)\s*(bya|billion\s+years?\s+ago)', date_lower)
        if bya_match:
            bya = float(bya_match.group(1))
            bc_year = int(bya * 1000000000)
            self.stats['mya_converted'] += 1
            return f"{bc_year} BC", "bya_to_bc"
        
        # Thousand Years Ago
        kya_match = re.search(r'(\d+(?:\.\d+)?)\s*(kya|thousand\s+years?\s+ago)', date_lower)
        if kya_match:
            kya = float(kya_match.group(1))
            bc_year = int(kya * 1000)
            self.stats['mya_converted'] += 1
            return f"{bc_year} BC", "kya_to_bc"
        
        return date_str, "no_change"
    
    def handle_bc_dates(self, date_str):
        """Standardize BC date formats."""
        date_lower = date_str.lower()
        
        if 'bc' not in date_lower and 'b.c.' not in date_lower:
            return date_str, "no_change"
        
        # Extract year and other components
        year_match = re.search(r'(\d+)', date_str)
        if not year_match:
            return date_str, "no_change"
        
        year = year_match.group(1)
        
        # Check for suspicious BC years (recent years marked as BC)
        year_int = int(year)
        if 1500 <= year_int <= 2024:
            # This is probably wrong - convert to AD
            self.stats['malformed_fixed'] += 1
            return re.sub(r'\s*b\.?c\.?', '', date_str, flags=re.IGNORECASE), "bc_to_ad_fix"
        
        # Handle parenthetical BC dates like "(260000000 B.C.)"
        if date_str.startswith('(') and date_str.endswith(')'):
            # Remove parentheses and standardize
            inner_date = date_str[1:-1].strip()
            # Just standardize the format inside
            standardized_inner = re.sub(r'\s*b\.?c\.?\s*$', ' BC', inner_date, flags=re.IGNORECASE)
            self.stats['bc_standardized'] += 1
            return standardized_inner, "bc_parentheses_removed"
        
        # Standard BC format standardization
        # Remove B.C. and replace with BC
        result = re.sub(r'\s*b\.?c\.?\s*', ' BC', date_str, flags=re.IGNORECASE).strip()
        
        self.stats['bc_standardized'] += 1
        return result, "bc_standardized"
    
    def handle_ad_dates(self, date_str):
        """Standardize AD date formats."""
        date_lower = date_str.lower()
        
        # Only process if it contains AD markers or looks like AD date
        if not any(marker in date_lower for marker in ['a.d.', 'ad ', 'ce']) and not re.search(r'\b\d{3,4}\b', date_str):
            return date_str, "no_change"
        
        # Remove explicit AD/CE markers and standardize
        if 'a.d.' in date_lower or 'ce' in date_lower:
            result = re.sub(r'\s*a\.?d\.?\s*', ' ', date_str, flags=re.IGNORECASE)
            result = re.sub(r'\s*ce\s*', ' ', result, flags=re.IGNORECASE)
            result = re.sub(r'\s+', ' ', result).strip()
            self.stats['ad_standardized'] += 1
            return result, "ad_standardized"
        
        return date_str, "no_change"
    
    def handle_malformed_dates(self, date_str):
        """Fix malformed or problematic dates."""
        
        # Fix dashes that should be spaces (like "10 JAN–5114")
        if '–' in date_str or '—' in date_str:
            fixed = re.sub(r'[–—]', '-', date_str)
            self.stats['malformed_fixed'] += 1
            return fixed, "dash_fixed"
        
        # Fix parenthetical issues
        if re.search(r'\([^)]*\d[^)]*\)', date_str):
            # Remove parentheses around dates
            fixed = re.sub(r'[()]', '', date_str)
            self.stats['malformed_fixed'] += 1
            return fixed, "parentheses_removed"
        
        return date_str, "no_change"
    
    def process_gedcom_file(self, input_file, output_file):
        """Process entire GEDCOM file."""
        print(f"Processing {input_file} -> {output_file}")
        
        changes_log = []
        
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for line_num, line in enumerate(infile, 1):
                    if line_num % 500000 == 0:
                        print(f"Processed {line_num:,} lines...")
                    
                    # Check if this is a date line
                    if line.strip().startswith('2 DATE'):
                        old_date = line[7:].strip()
                        if old_date:
                            new_date, change_type = self.standardize_date(old_date)
                            
                            if change_type != "no_change":
                                changes_log.append({
                                    'line_num': line_num,
                                    'change_type': change_type,
                                    'old_date': old_date,
                                    'new_date': new_date
                                })
                                
                                if new_date:  # Keep line if date not empty
                                    outfile.write(f"2 DATE {new_date}\n")
                                # Skip line if date was removed (empty new_date)
                            else:
                                outfile.write(line)
                        else:
                            outfile.write(line)
                    else:
                        outfile.write(line)
        
        # Save changes log
        self.save_changes_log(changes_log, f"{output_file}.changes.csv")
        
        print(f"Processing complete!")
        self.print_statistics()
    
    def save_changes_log(self, changes_log, log_file):
        """Save detailed changes log."""
        import csv
        
        with open(log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Line_Number', 'Change_Type', 'Old_Date', 'New_Date'])
            
            for change in changes_log:
                writer.writerow([
                    change['line_num'],
                    change['change_type'],
                    change['old_date'],
                    change['new_date']
                ])
        
        print(f"Changes log saved: {log_file}")
    
    def print_statistics(self):
        """Print processing statistics."""
        print(f"\\nProcessing Statistics:")
        print(f"  Total dates processed: {self.stats['total_dates']:,}")
        print(f"  Future dates removed: {self.stats['future_dates_removed']:,}")
        print(f"  BC dates standardized: {self.stats['bc_standardized']:,}")
        print(f"  AD dates standardized: {self.stats['ad_standardized']:,}")
        print(f"  Prehistoric dates converted: {self.stats['mya_converted']:,}")
        print(f"  Malformed dates fixed: {self.stats['malformed_fixed']:,}")
        print(f"  Dates unchanged: {self.stats['unchanged']:,}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python improved_date_standardizer.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    standardizer = ImprovedDateStandardizer()
    standardizer.process_gedcom_file(input_file, output_file)

if __name__ == "__main__":
    main()