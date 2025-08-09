#!/usr/bin/env python3
"""
Final Date Fixer for Cleaned GEDCOM
Removes remaining problematic dates after source cleaning:
1. All "7 AUG 2025" dates (editing metadata that survived)
2. Future dates (2025+)
3. Recent dates (1800-2024) 
4. Standardizes BC/MYA formats
"""

import sys
import re

def fix_dates_final(input_file, output_file):
    """Final pass to fix remaining date issues."""
    
    print(f"Final date fixing: {input_file} -> {output_file}")
    
    stats = {
        'total_lines': 0,
        'date_lines_found': 0,
        'aug_2025_removed': 0,
        'future_dates_removed': 0,
        'recent_dates_removed': 0,
        'bc_standardized': 0,
        'mya_converted': 0,
        'lines_removed': 0,
        'lines_kept': 0
    }
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile:
        with open(output_file, 'w', encoding='utf-8') as outfile:
            
            for line_num, line in enumerate(infile, 1):
                if line_num % 500000 == 0:
                    print(f"Processed {line_num:,} lines...")
                
                stats['total_lines'] += 1
                original_line = line.rstrip()
                
                # Process date lines
                if line.strip().startswith('2 DATE '):
                    stats['date_lines_found'] += 1
                    date_value = line[7:].strip()
                    
                    if not date_value:
                        # Empty date - keep as is
                        outfile.write(original_line + '\n')
                        stats['lines_kept'] += 1
                        continue
                    
                    # Check for problematic dates to remove
                    should_remove = False
                    
                    # Remove "7 AUG 2025" and variants
                    if '7 aug 2025' in date_value.lower() or 'aug 2025' in date_value.lower():
                        should_remove = True
                        stats['aug_2025_removed'] += 1
                    
                    # Remove future dates (2025+)
                    elif re.search(r'\b(20[2-9][5-9]|2[1-9]\d\d)\b', date_value):
                        should_remove = True
                        stats['future_dates_removed'] += 1
                    
                    # Remove clearly modern dates (1800-2024)
                    elif re.search(r'\b(1[89]\d\d|20[0-2][0-4])\b', date_value):
                        should_remove = True
                        stats['recent_dates_removed'] += 1
                    
                    if should_remove:
                        stats['lines_removed'] += 1
                        continue  # Skip this line entirely
                    
                    # Standardize remaining dates
                    new_date = standardize_date_value(date_value)
                    
                    if new_date != date_value:
                        if 'MYA' in date_value.upper():
                            stats['mya_converted'] += 1
                        elif 'B.C.' in date_value or 'BC' in date_value:
                            stats['bc_standardized'] += 1
                        
                        outfile.write(f"2 DATE {new_date}\n")
                    else:
                        outfile.write(original_line + '\n')
                    
                    stats['lines_kept'] += 1
                
                else:
                    # Non-date line - keep as is
                    outfile.write(original_line + '\n')
                    stats['lines_kept'] += 1
    
    print_statistics(stats)
    return True

def standardize_date_value(date_str):
    """Standardize a date value."""
    
    # Handle MYA (Million Years Ago)
    mya_match = re.search(r'(\d+(?:\.\d+)?)\s*MYA', date_str.upper())
    if mya_match:
        mya = float(mya_match.group(1))
        bc_year = int(mya * 1000000)
        return f"{bc_year} BC"
    
    # Handle BYA (Billion Years Ago)
    bya_match = re.search(r'(\d+(?:\.\d+)?)\s*BYA', date_str.upper())
    if bya_match:
        bya = float(bya_match.group(1))
        bc_year = int(bya * 1000000000)
        return f"{bc_year} BC"
    
    # Standardize BC formats
    if 'B.C.' in date_str.upper() or ' BC' in date_str.upper():
        # Remove parentheses if present
        if date_str.startswith('(') and date_str.endswith(')'):
            date_str = date_str[1:-1].strip()
        
        # Standardize B.C. to BC
        result = re.sub(r'\s*B\.?C\.?\s*', ' BC', date_str, flags=re.IGNORECASE).strip()
        return result
    
    # Check for suspicious recent years marked as BC
    if 'BC' in date_str.upper():
        year_match = re.search(r'(\d+)', date_str)
        if year_match and 1500 <= int(year_match.group(1)) <= 2024:
            # This is probably wrong - remove BC marking
            return re.sub(r'\s*BC\s*', '', date_str, flags=re.IGNORECASE).strip()
    
    return date_str

def print_statistics(stats):
    """Print processing statistics."""
    print(f"\nFinal Date Fixing Statistics:")
    print(f"  Total lines processed: {stats['total_lines']:,}")
    print(f"  Date lines found: {stats['date_lines_found']:,}")
    print(f"  '7 AUG 2025' dates removed: {stats['aug_2025_removed']:,}")
    print(f"  Future dates removed: {stats['future_dates_removed']:,}")
    print(f"  Recent dates removed: {stats['recent_dates_removed']:,}")
    print(f"  BC dates standardized: {stats['bc_standardized']:,}")
    print(f"  MYA dates converted: {stats['mya_converted']:,}")
    print(f"  Total lines removed: {stats['lines_removed']:,}")
    print(f"  Lines kept: {stats['lines_kept']:,}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python final_date_fixer.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = fix_dates_final(input_file, output_file)
    
    if success:
        print(f"\nDate fixing completed successfully: {output_file}")
    else:
        print("Date fixing failed")
        sys.exit(1)

if __name__ == "__main__":
    main()