#!/usr/bin/env python3
"""
Debug Horus day creation specifically
"""

import sys
sys.path.append('.')
from zodiac_wiki_pages import zodiac_to_iso, ordinal_in_year, weekday_name_from_iso, MONTHS
from datetime import date

def debug_horus():
    print("=== DEBUGGING HORUS DAY CREATION ===")
    
    # Test Horus 1 (month 14, day 1)
    m_idx, d_m = 14, 1
    
    print(f"\n1. Testing zodiac_to_iso for {MONTHS[m_idx-1]} {d_m}...")
    try:
        iso_week, iso_wd = zodiac_to_iso(m_idx, d_m)
        print(f"   ISO week: {iso_week}, ISO weekday: {iso_wd}")
        
        ord_year = ordinal_in_year(m_idx, d_m)
        print(f"   Ordinal in year: {ord_year}")
        
        weekday_name = weekday_name_from_iso(iso_wd)
        print(f"   Weekday name: {weekday_name}")
        
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    print(f"\n2. Testing date.fromisocalendar for week {iso_week}...")
    test_years = [2020, 2021, 2022, 2023, 2024, 2025]
    for year in test_years:
        try:
            test_date = date.fromisocalendar(year, iso_week, iso_wd)
            print(f"   {year}: {test_date} (success)")
        except Exception as e:
            print(f"   {year}: ERROR - {e}")
    
    print(f"\n3. Testing which years have week 53...")
    for year in range(2020, 2030):
        try:
            # Test if week 53 exists by trying to create a date
            test_date = date.fromisocalendar(year, 53, 1)
            print(f"   {year}: Has week 53 ({test_date})")
        except:
            print(f"   {year}: No week 53")

if __name__ == "__main__":
    debug_horus()