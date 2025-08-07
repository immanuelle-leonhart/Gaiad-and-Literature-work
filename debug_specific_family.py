#!/usr/bin/env python3
"""Debug the specific Adasi/Bel-bani/Ennana-bani family relationships"""

import sqlite3

def debug_family():
    conn = sqlite3.connect('new_gedcoms/Gaiad with uncertain merging of the roman lines.ftb')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Find individuals with these names
    names_to_find = ['Adasi', 'Bel-bani', 'Ennana-bani']
    individuals = {}
    
    for name in names_to_find:
        cursor.execute("""
            SELECT DISTINCT imd.individual_id, imd.gender, ild.first_name, ild.last_name
            FROM individual_main_data imd
            JOIN individual_data_set ids ON imd.individual_id = ids.individual_id
            JOIN individual_lang_data ild ON ids.individual_data_set_id = ild.individual_data_set_id
            WHERE (ild.first_name LIKE ? OR ild.last_name LIKE ?) 
            AND imd.delete_flag = 0 AND ids.delete_flag = 0
        """, (f'%{name}%', f'%{name}%'))
        
        results = cursor.fetchall()
        if results:
            individuals[name] = results
            print(f"\nFound {name}:")
            for ind in results:
                print(f"  ID {ind['individual_id']}: {ind['first_name']} {ind['last_name']} ({ind['gender']})")
    
    # Find families containing these individuals
    all_individual_ids = []
    for name_results in individuals.values():
        for ind in name_results:
            all_individual_ids.append(ind['individual_id'])
    
    print(f"\nLooking for families containing individuals: {all_individual_ids}")
    
    for ind_id in all_individual_ids:
        cursor.execute("""
            SELECT fic.family_id, fic.individual_id, fic.individual_role_type,
                   ild.first_name, ild.last_name, imd.gender
            FROM family_individual_connection fic
            JOIN individual_main_data imd ON fic.individual_id = imd.individual_id
            JOIN individual_data_set ids ON imd.individual_id = ids.individual_id
            JOIN individual_lang_data ild ON ids.individual_data_set_id = ild.individual_data_set_id
            WHERE fic.family_id IN (
                SELECT DISTINCT family_id 
                FROM family_individual_connection 
                WHERE individual_id = ? AND delete_flag = 0
            )
            AND fic.delete_flag = 0 AND imd.delete_flag = 0 AND ids.delete_flag = 0
            ORDER BY fic.family_id, fic.individual_role_type
        """, (ind_id,))
        
        family_members = cursor.fetchall()
        if family_members:
            current_family = None
            for member in family_members:
                if member['family_id'] != current_family:
                    current_family = member['family_id']
                    print(f"\n=== FAMILY {current_family} ===")
                
                name = f"{member['first_name']} {member['last_name']}".strip()
                print(f"  Role {member['individual_role_type']}: {name} (ID {member['individual_id']}, {member['gender']})")
    
    conn.close()

if __name__ == "__main__":
    debug_family()