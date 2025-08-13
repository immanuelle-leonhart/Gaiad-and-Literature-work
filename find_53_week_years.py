#!/usr/bin/env python3
"""
Find which years have 53 weeks for intercalary day calculation
"""

from datetime import date

def has_week_53(year):
    """Check if a year has 53 ISO weeks"""
    try:
        # Try to create a date for week 53, day 1
        date.fromisocalendar(year, 53, 1)
        return True
    except ValueError:
        return False

def find_53_week_years(start_year=2020, end_year=2030):
    """Find all years in range that have 53 weeks"""
    years_53 = []
    for year in range(start_year, end_year + 1):
        if has_week_53(year):
            years_53.append(year)
    return years_53

if __name__ == "__main__":
    print("=== FINDING 53-WEEK YEARS ===")
    
    # Test recent years
    recent_53 = find_53_week_years(2020, 2030)
    print(f"Years 2020-2030 with 53 weeks: {recent_53}")
    
    # Test longer range for patterns
    long_53 = find_53_week_years(2000, 2050)
    print(f"\nYears 2000-2050 with 53 weeks:")
    for i in range(0, len(long_53), 10):
        chunk = long_53[i:i+10]
        print(f"  {chunk}")
    
    print(f"\nTotal 53-week years in 2000-2050: {len(long_53)} out of 51 years")
    print(f"Percentage: {len(long_53)/51*100:.1f}%")
    
    # Calculate the pattern
    if len(long_53) >= 2:
        gaps = [long_53[i+1] - long_53[i] for i in range(len(long_53)-1)]
        print(f"\nGaps between 53-week years: {gaps}")
        print(f"Average gap: {sum(gaps)/len(gaps):.1f} years")