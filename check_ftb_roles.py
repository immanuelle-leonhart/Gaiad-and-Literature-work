#!/usr/bin/env python3
"""Check what role types exist in the FTB database"""

import sqlite3

def check_roles():
    conn = sqlite3.connect('new_gedcoms/Gaiad with uncertain merging of the roman lines.ftb')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check role types
    cursor.execute("""
        SELECT individual_role_type, COUNT(*) as count
        FROM family_individual_connection 
        WHERE delete_flag = 0
        GROUP BY individual_role_type 
        ORDER BY individual_role_type
    """)
    
    roles = cursor.fetchall()
    print("Role types in database:")
    for role in roles:
        print(f"  Role {role['individual_role_type']}: {role['count']:,} connections")
    
    # Check some examples of each role type
    print("\nExamples for each role type:")
    for role in roles:
        role_type = role['individual_role_type']
        cursor.execute("""
            SELECT fic.family_id, fic.individual_id, imd.gender
            FROM family_individual_connection fic
            JOIN individual_main_data imd ON fic.individual_id = imd.individual_id
            WHERE fic.individual_role_type = ? AND fic.delete_flag = 0 AND imd.delete_flag = 0
            LIMIT 5
        """, (role_type,))
        
        examples = cursor.fetchall()
        print(f"\n  Role {role_type} examples:")
        for ex in examples:
            print(f"    Family {ex['family_id']}, Individual {ex['individual_id']}, Gender {ex['gender']}")
    
    conn.close()

if __name__ == "__main__":
    check_roles()