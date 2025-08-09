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
    """Standardize date formatting in GEDCOM file with improved handling."""
    
    print(f"Improved date standardization: {input_file} -> {output_file}")
    
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
        'dates_standardized': 0,
        'negative_years_converted': 0,
        'incomplete_ranges_fixed': 0,
        'roman_republic_fixed': 0,
        'before_after_standardized': 0,
        'between_standardized': 0,
        'circa_standardized': 0,
        'bc_standardized': 0,
        'month_standardized': 0
    }
    
    # Read all lines first, then process them
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
                
                # Process date lines
                if line.strip().startswith('2 DATE '):
                    stats['date_lines_found'] += 1
                    date_value = line[7:].strip()
                    
                    if not date_value:
                        outfile.write(original_line + '\n')
                        continue
                    
                    # Standardize the date value
                    standardized_date = standardize_date_string(date_value, stats)
                    
                    if standardized_date != date_value:
                        stats['dates_standardized'] += 1
                        outfile.write(f"2 DATE {standardized_date}\n")
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
    
    print_statistics(stats)
    return True

def standardize_date_string(date_str, stats):
    """Standardize a single date string with improved handling."""
    original = date_str.strip()
    result = original
    
    # Remove outer parentheses if they wrap the entire date
    if result.startswith('(') and result.endswith(')'):
        result = result[1:-1].strip()
    
    # Handle incomplete date formats like "(1 AUG–10)" or "(31 JAN–36)" 
    # These are NOT ranges, they are single dates with formatting issues
    incomplete_date = re.match(r'^(\d{1,2}\s+[A-Z]{3})[-–—](\d+)$', result)
    if incomplete_date:
        day_month = incomplete_date.group(1)  # e.g., "1 AUG", "28 SEP"
        year = int(incomplete_date.group(2))  # e.g., 10, 36, 48
        
        # Years under 100 in genealogical context are almost always BC (Roman era)
        if year < 100:
            result = f"{day_month} {year} BC"
            stats['roman_republic_fixed'] += 1
        else:
            result = f"{day_month} {year}"
            stats['incomplete_ranges_fixed'] += 1
        return result
    
    # Fix incorrectly parsed BET ranges that should be single BC dates
    # Pattern: "BET (28 SEP AND 48)" should be "28 SEP 48 BC"
    bad_bet_match = re.match(r'^BET \((\d{1,2}\s+[A-Z]{3}) AND (\d{1,2})\)$', result)
    if bad_bet_match:
        day_month = bad_bet_match.group(1)  # e.g., "28 SEP"
        year = int(bad_bet_match.group(2))  # e.g., 48
        
        # Years under 100 are BC in Roman context
        if year < 100:
            result = f"{day_month} {year} BC"
            stats['roman_republic_fixed'] += 1
        else:
            result = f"{day_month} {year}"
            stats['incomplete_ranges_fixed'] += 1
        return result

    # Handle negative years (convert to BC)
    if re.search(r'-\d+', result):
        result = re.sub(r'-(\d+)', r'\1 BC', result)
        stats['negative_years_converted'] += 1
        return result
    
    # Handle standard BEFORE/AFTER patterns
    before_match = re.match(r'^(?:BEF|BEFORE)\s+(.+)$', result, re.IGNORECASE)
    if before_match:
        inner_date = standardize_simple_date(before_match.group(1).strip())
        result = f"BEF {inner_date}"
        stats['before_after_standardized'] += 1
        return result
        
    after_match = re.match(r'^(?:AFT|AFTER)\s+(.+)$', result, re.IGNORECASE)
    if after_match:
        inner_date = standardize_simple_date(after_match.group(1).strip())
        result = f"AFT {inner_date}"
        stats['before_after_standardized'] += 1
        return result
    
    # Handle BETWEEN patterns
    between_match = re.match(r'^(?:BET|BETWEEN)\s+(.+?)\s+(?:AND|TO)\s+(.+)$', result, re.IGNORECASE)
    if between_match:
        start_date = standardize_simple_date(between_match.group(1).strip())
        end_date = standardize_simple_date(between_match.group(2).strip())
        result = f"BET {start_date} AND {end_date}"
        stats['between_standardized'] += 1
        return result
    
    # Handle CIRCA patterns
    circa_match = re.match(r'^(?:ABT|ABOUT|CIRCA|CA?\\.?|~)\s*(.+)$', result, re.IGNORECASE)
    if circa_match:
        inner_date = standardize_simple_date(circa_match.group(1).strip())
        result = f"ABT {inner_date}"
        stats['circa_standardized'] += 1
        return result
    
    # Handle regular date ranges with dash/hyphen (not already handled above)
    range_match = re.match(r'^(.+?)\s*[-–—]\s*(.+)$', result)
    if range_match and not any(x in result.upper() for x in ['BEF', 'AFT', 'BET', 'ABT']):
        start_date = standardize_simple_date(range_match.group(1).strip())
        end_date = standardize_simple_date(range_match.group(2).strip())
        result = f"BET {start_date} AND {end_date}"
        stats['between_standardized'] += 1
        return result
    
    # If no special patterns matched, standardize as simple date
    simple_result = standardize_simple_date(result)
    if simple_result != result:
        if 'BC' in original or 'B.C.' in original or re.search(r'-\d+', original):
            stats['bc_standardized'] += 1
        else:
            stats['month_standardized'] += 1
        return simple_result
    
    return result

def standardize_simple_date(date_str):
    """Standardize a simple date without qualifiers."""
    if not date_str:
        return date_str
    
    result = date_str.strip()
    
    # Remove extra parentheses
    if result.startswith('(') and result.endswith(')'):
        result = result[1:-1].strip()
    
    # Handle negative years first
    result = re.sub(r'-(\d+)', r'\1 BC', result)
    
    # Handle MYA (Million Years Ago) - convert to BC
    mya_match = re.search(r'([\d.]+)\s*MYA', result, re.IGNORECASE)
    if mya_match:
        mya = float(mya_match.group(1))
        bc_year = int(mya * 1000000)
        result = f"{bc_year} BC"
        return result
    
    # Handle BYA (Billion Years Ago) - convert to BC  
    bya_match = re.search(r'([\d.]+)\s*BYA', result, re.IGNORECASE)
    if bya_match:
        bya = float(bya_match.group(1))
        bc_year = int(bya * 1000000000)
        result = f"{bc_year} BC"
        return result
    
    # Standardize BC/AD formats
    result = re.sub(r'\s*B\.?C\.?\s*', ' BC', result, flags=re.IGNORECASE)
    result = re.sub(r'\s*A\.?D\.?\s*', ' AD', result, flags=re.IGNORECASE)
    
    # Standardize month abbreviations to uppercase
    months = {
        'jan': 'JAN', 'feb': 'FEB', 'mar': 'MAR', 'apr': 'APR',
        'may': 'MAY', 'jun': 'JUN', 'jul': 'JUL', 'aug': 'AUG',
        'sep': 'SEP', 'oct': 'OCT', 'nov': 'NOV', 'dec': 'DEC'
    }
    
    for month_lower, month_upper in months.items():
        # Match month abbreviation with word boundaries
        pattern = r'\b' + month_lower + r'\b'
        result = re.sub(pattern, month_upper, result, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    result = ' '.join(result.split())
    
    return result

def print_statistics(stats):
    """Print processing statistics."""
    print(f"\nImproved Date Standardization Statistics:")
    print(f"  Total lines processed: {stats['total_lines']:,}")
    print(f"  Date lines found: {stats['date_lines_found']:,}")
    print(f"  Dates standardized: {stats['dates_standardized']:,}")
    print(f"  Negative years converted to BC: {stats['negative_years_converted']:,}")
    print(f"  Roman Republic dates fixed: {stats['roman_republic_fixed']:,}")
    print(f"  Incomplete ranges fixed: {stats['incomplete_ranges_fixed']:,}")
    print(f"  BEFORE/AFTER standardized: {stats['before_after_standardized']:,}")
    print(f"  BETWEEN standardized: {stats['between_standardized']:,}")
    print(f"  CIRCA standardized: {stats['circa_standardized']:,}")
    print(f"  BC formats standardized: {stats['bc_standardized']:,}")
    print(f"  Month abbreviations: {stats['month_standardized']:,}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python improved_date_standardizer_v2.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = standardize_date_formats(input_file, output_file)
    
    if success:
        print(f"\nImproved date standardization completed: {output_file}")
    else:
        print("Date standardization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()