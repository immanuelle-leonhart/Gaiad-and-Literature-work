#!/usr/bin/env python3
"""
Fix Negative Years - Step 1
Convert negative years to BC format: -10 -> 10 BC
"""

import sys
import re
import tempfile
import shutil

def fix_negative_years(input_file, output_file):
    """Fix negative years in GEDCOM file."""
    
    print(f"Fixing negative years: {input_file} -> {output_file}")
    
    # If input and output are the same, use a temporary file
    use_temp = (input_file == output_file)
    
    if use_temp:
        temp_output = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ged', encoding='utf-8')
        actual_output = temp_output.name
        temp_output.close()
    else:
        actual_output = output_file
    
    stats = {
        'total_lines': 0,
        'date_lines_found': 0,
        'negative_years_fixed': 0
    }
    
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile:
            lines = infile.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    print(f"Read {len(lines):,} lines from input file")
    
    try:
        with open(actual_output, 'w', encoding='utf-8') as outfile:
            
            for line_num, line in enumerate(lines, 1):
                if line_num % 500000 == 0:
                    print(f"Processed {line_num:,} lines...")
                
                stats['total_lines'] += 1
                original_line = line.rstrip()
                
                # Process date lines only
                if line.strip().startswith('2 DATE '):
                    stats['date_lines_found'] += 1
                    date_value = line[7:].strip()
                    
                    if not date_value:
                        outfile.write(original_line + '\n')
                        continue
                    
                    # Fix negative years
                    fixed_date = fix_negative_year_in_date(date_value)
                    
                    if fixed_date != date_value:
                        stats['negative_years_fixed'] += 1
                        outfile.write(f"2 DATE {fixed_date}\n")
                    else:
                        outfile.write(original_line + '\n')
                
                else:
                    # Non-date line - keep as is
                    outfile.write(original_line + '\n')
    except Exception as e:
        print(f"Error processing file: {e}")
        return False
    
    # If using temp file, move it to the final location
    if use_temp:
        shutil.move(actual_output, output_file)
        print(f"Moved temporary file to: {output_file}")
    
    print(f"\nNegative Years Fix Statistics:")
    print(f"  Total lines processed: {stats['total_lines']:,}")
    print(f"  Date lines found: {stats['date_lines_found']:,}")
    print(f"  Negative years fixed: {stats['negative_years_fixed']:,}")
    
    return True

def fix_negative_year_in_date(date_str):
    """Fix negative years in a single date string."""
    if not date_str or '-' not in date_str:
        return date_str
    
    # Convert negative years to BC format
    # Pattern: -10 -> 10 BC, -48 -> 48 BC
    result = re.sub(r'-(\d+)', r'\1 BC', date_str)
    
    return result

def main():
    if len(sys.argv) != 3:
        print("Usage: python fix_negative_years.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = fix_negative_years(input_file, output_file)
    
    if success:
        print(f"\nNegative years fix completed: {output_file}")
    else:
        print("Negative years fix failed")
        sys.exit(1)

if __name__ == "__main__":
    main()