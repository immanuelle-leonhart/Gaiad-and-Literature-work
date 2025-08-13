#!/usr/bin/env python3
"""
Trace exactly where the Horus error is occurring
"""

import sys
import traceback
sys.path.append('.')
from zodiac_wiki_pages import build_page

def trace_error():
    print("=== TRACING HORUS ERROR ===")
    
    try:
        print("Calling build_page(14, 1)...")
        title, content = build_page(14, 1)
        print(f"SUCCESS: Title = {title}")
        print(f"Content length: {len(content)}")
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    trace_error()