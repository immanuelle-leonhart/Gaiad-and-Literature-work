#!/usr/bin/env python3
"""
Comprehensive GEDCOM Date Analyzer
Analyzes ALL date formats and identifies problems for standardization.
Expected timeline: Billions of years ago -> Ancient times -> Antiquity -> Medieval (to 1000 AD)
"""

import re
import csv
from collections import Counter, defaultdict
from datetime import datetime

class DateAnalyzer:
    def __init__(self):
        self.date_patterns = {
            # Time scales
            'mya_dates': [],           # Million years ago
            'bya_dates': [],           # Billion years ago  
            'kya_dates': [],           # Thousand years ago
            'ya_dates': [],            # Years ago
            
            # BC dates
            'bc_standard': [],         # 1000 BC
            'bc_periods': [],          # B.C.
            'bc_parenthetical': [],    # (1000 BC)
            'bc_range': [],            # 1000-900 BC
            'bc_approximate': [],      # ABT 1000 BC, c. 1000 BC
            
            # AD dates  
            'ad_standard': [],         # 1000, 1000 AD
            'ad_periods': [],          # A.D.
            'ad_ce': [],               # 1000 CE
            'ad_parenthetical': [],    # (1000 AD)
            'ad_range': [],            # 1000-1100
            'ad_approximate': [],      # ABT 1000, c. 1000
            
            # Modern dates (suspicious)
            'future_dates': [],        # 2025+
            'recent_dates': [],        # 1800-2024
            'medieval_late': [],       # 1000-1500 (should be trimmed)
            
            # Problematic formats
            'mixed_era': [],           # BC and AD in same date
            'malformed': [],           # Unparseable
            'empty_dates': [],         # Empty or just whitespace
            'non_standard': [],        # Weird formats
            
            # Special formats
            'partial_dates': [],       # JAN 1000, 1000s
            'estimated': [],           # EST, CALC, etc.
            'before_after': [],        # BEF, AFT
            'date_ranges': [],         # FROM/TO, BET/AND
        }
        
        self.date_counter = Counter()
        self.line_numbers = defaultdict(list)
        self.individual_dates = []  # Store individual records for analysis
        
    def extract_dates_from_gedcom(self, file_path):
        """Extract all dates from GEDCOM file with context."""
        print(f"Analyzing dates in {file_path}...")
        
        current_individual = None
        current_individual_name = ""
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if line_num % 500000 == 0:
                        print(f"Processed {line_num:,} lines...")
                    
                    line = line.strip()
                    
                    # Track current individual
                    if line.startswith('0 @I') and line.endswith('@ INDI'):
                        current_individual = line.split()[1].strip('@')
                        current_individual_name = ""
                    elif line.startswith('1 NAME') and current_individual:
                        current_individual_name = line[7:].strip()
                    
                    # Extract dates
                    if line.startswith('2 DATE'):
                        date_value = line[7:].strip()
                        if date_value:  # Not empty
                            self.analyze_date(date_value, line_num, current_individual, current_individual_name)
                        else:
                            self.date_patterns['empty_dates'].append({
                                'date': date_value,
                                'line': line_num,
                                'individual': current_individual,
                                'name': current_individual_name
                            })
        
        except Exception as e:
            print(f"Error processing file: {e}")
    
    def analyze_date(self, date_str, line_num, individual_id, individual_name):
        """Analyze a single date string and categorize it."""
        original_date = date_str
        date_lower = date_str.lower().strip()
        
        # Count occurrences
        self.date_counter[date_str] += 1
        self.line_numbers[date_str].append(line_num)
        
        # Store individual record
        record = {
            'date': date_str,
            'line': line_num,
            'individual': individual_id,
            'name': individual_name,
            'category': 'unknown',
            'issues': []
        }
        
        # Check for empty/whitespace
        if not date_str or not date_str.strip():
            record['category'] = 'empty'
            self.date_patterns['empty_dates'].append(record)
            return
        
        # Million/Billion Years Ago
        if re.search(r'\d+(?:\.\d+)?\s*(mya|million\s+years?\s+ago)', date_lower):
            record['category'] = 'mya'
            self.date_patterns['mya_dates'].append(record)
            return
            
        if re.search(r'\d+(?:\.\d+)?\s*(bya|billion\s+years?\s+ago)', date_lower):
            record['category'] = 'bya'
            self.date_patterns['bya_dates'].append(record)
            return
            
        if re.search(r'\d+(?:\.\d+)?\s*(kya|thousand\s+years?\s+ago)', date_lower):
            record['category'] = 'kya'
            self.date_patterns['kya_dates'].append(record)
            return
            
        if re.search(r'\d+\s*ya\b', date_lower):
            record['category'] = 'ya'
            self.date_patterns['ya_dates'].append(record)
            return
        
        # Check for mixed BC/AD (problematic)
        if ('bc' in date_lower or 'b.c.' in date_lower) and ('ad' in date_lower or 'a.d.' in date_lower):
            record['category'] = 'mixed_era'
            record['issues'].append('Contains both BC and AD')
            self.date_patterns['mixed_era'].append(record)
            return
        
        # BC Dates
        if 'bc' in date_lower or 'b.c.' in date_lower:
            record['category'] = 'bc'
            
            # Extract year for analysis
            year_match = re.search(r'(\d+)', date_str)
            if year_match:
                year = int(year_match.group(1))
                record['year'] = -year  # Negative for BC
                
                # Check for suspicious BC dates
                if year > 50000:  # Extremely ancient
                    record['issues'].append(f'Extremely ancient BC date: {year}')
                elif 1500 <= year <= 2024:  # Suspiciously recent for BC
                    record['issues'].append(f'Recent year marked as BC: {year}')
            
            # Categorize BC format
            if re.search(r'\(.*bc.*\)', date_lower):
                self.date_patterns['bc_parenthetical'].append(record)
            elif 'b.c.' in date_lower:
                self.date_patterns['bc_periods'].append(record)
            elif '-' in date_str and 'bc' in date_lower:
                self.date_patterns['bc_range'].append(record)
            elif any(word in date_lower for word in ['abt', 'about', 'circa', 'c.', '~']):
                self.date_patterns['bc_approximate'].append(record)
            else:
                self.date_patterns['bc_standard'].append(record)
            return
        
        # AD/CE Dates
        year_match = re.search(r'\b(\d{3,4})\b', date_str)
        if year_match:
            year = int(year_match.group(1))
            record['year'] = year
            
            # Categorize by time period
            if year >= 2025:
                record['category'] = 'future'
                record['issues'].append(f'Future date: {year}')
                self.date_patterns['future_dates'].append(record)
            elif year >= 1800:
                record['category'] = 'recent'
                record['issues'].append(f'Recent date (should not exist): {year}')
                self.date_patterns['recent_dates'].append(record)
            elif year > 1000:
                record['category'] = 'medieval_late'
                record['issues'].append(f'Post-1000 AD (should be trimmed): {year}')
                self.date_patterns['medieval_late'].append(record)
            else:
                record['category'] = 'ad_standard'
        
        # Check AD formats
        if 'a.d.' in date_lower:
            self.date_patterns['ad_periods'].append(record)
        elif 'ce' in date_lower:
            self.date_patterns['ad_ce'].append(record)
        elif re.search(r'\(.*\d.*\)', date_str):
            self.date_patterns['ad_parenthetical'].append(record)
        elif '-' in date_str and year_match:
            self.date_patterns['ad_range'].append(record)
        elif any(word in date_lower for word in ['abt', 'about', 'circa', 'c.', '~']):
            self.date_patterns['ad_approximate'].append(record)
        elif year_match:
            self.date_patterns['ad_standard'].append(record)
        else:
            # Special formats
            if any(word in date_lower for word in ['est', 'calc', 'calculated']):
                record['category'] = 'estimated'
                self.date_patterns['estimated'].append(record)
            elif any(word in date_lower for word in ['bef', 'before', 'aft', 'after']):
                record['category'] = 'before_after'
                self.date_patterns['before_after'].append(record)
            elif any(word in date_lower for word in ['bet', 'from', 'to', 'and']):
                record['category'] = 'date_range'
                self.date_patterns['date_ranges'].append(record)
            elif re.search(r'^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', date_lower):
                record['category'] = 'partial'
                self.date_patterns['partial_dates'].append(record)
            else:
                record['category'] = 'malformed'
                record['issues'].append('Unparseable date format')
                self.date_patterns['malformed'].append(record)
        
        self.individual_dates.append(record)
    
    def generate_report(self, output_file):
        """Generate comprehensive CSV report."""
        print(f"Generating report: {output_file}")
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Date_Value', 'Category', 'Count', 'Year', 'Issues', 
                'Sample_Line', 'Sample_Individual', 'Sample_Name'
            ])
            
            # Process all patterns
            all_dates = {}
            for category, dates in self.date_patterns.items():
                for record in dates:
                    date_val = record['date']
                    if date_val not in all_dates:
                        all_dates[date_val] = {
                            'category': record['category'],
                            'count': self.date_counter[date_val],
                            'year': record.get('year', ''),
                            'issues': record.get('issues', []),
                            'sample_line': record['line'],
                            'sample_individual': record['individual'] or '',
                            'sample_name': record['name'] or ''
                        }
            
            # Sort by count (most common first)
            for date_val, data in sorted(all_dates.items(), key=lambda x: x[1]['count'], reverse=True):
                writer.writerow([
                    date_val,
                    data['category'],
                    data['count'],
                    data['year'],
                    '; '.join(data['issues']),
                    data['sample_line'],
                    data['sample_individual'],
                    data['sample_name']
                ])
    
    def print_summary(self):
        """Print analysis summary."""
        print("\n" + "="*80)
        print("COMPREHENSIVE DATE ANALYSIS SUMMARY")
        print("="*80)
        
        total_dates = sum(len(dates) for dates in self.date_patterns.values())
        unique_dates = len(self.date_counter)
        
        print(f"Total date entries: {total_dates:,}")
        print(f"Unique date formats: {unique_dates:,}")
        
        print(f"\nDate Categories:")
        for category, dates in self.date_patterns.items():
            if dates:
                print(f"  - {category}: {len(dates):,}")
        
        # Show most problematic issues
        print(f"\nMost Common Date Values:")
        for date_val, count in self.date_counter.most_common(10):
            print(f"  - '{date_val}': {count:,} occurrences")
        
        # Highlight major issues
        issues = []
        if self.date_patterns['future_dates']:
            issues.append(f"❌ {len(self.date_patterns['future_dates'])} future dates (2025+)")
        if self.date_patterns['recent_dates']:
            issues.append(f"❌ {len(self.date_patterns['recent_dates'])} recent dates (1800-2024)")
        if self.date_patterns['mixed_era']:
            issues.append(f"❌ {len(self.date_patterns['mixed_era'])} mixed BC/AD dates")
        if self.date_patterns['malformed']:
            issues.append(f"⚠️  {len(self.date_patterns['malformed'])} malformed dates")
        if self.date_patterns['medieval_late']:
            issues.append(f"⚠️  {len(self.date_patterns['medieval_late'])} post-1000 AD dates (should be trimmed)")
        
        if issues:
            print(f"\nMajor Issues Found:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"\n✅ No major date issues found!")

def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python comprehensive_date_analyzer.py <input_file> <output_csv>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_csv = sys.argv[2]
    
    analyzer = DateAnalyzer()
    analyzer.extract_dates_from_gedcom(input_file)
    analyzer.generate_report(output_csv)
    analyzer.print_summary()
    
    print(f"\nDetailed analysis saved to: {output_csv}")

if __name__ == "__main__":
    main()