#!/usr/bin/env python3
"""
Add the missing QID mappings that were found during the create attempt
"""

missing_mappings = [
    ('@I4404@', 'Q152995'),
    ('@I5963@', 'Q153128'), 
    ('@I6107@', 'Q153131'),
    ('@I6241@', 'Q153135'),
    ('@I6374@', 'Q153137'),
    ('@I6471@', 'Q153139'),
    ('@I6831@', 'Q153152'),
    ('@I6855@', 'Q153152'),  # Same QID as above
    ('@I6940@', 'Q153155'),
    ('@I6976@', 'Q153152'),  # Same QID as above
    ('@I7000@', 'Q153152'),  # Same QID as above
    ('@I7012@', 'Q153152'),  # Same QID as above
    ('@I7024@', 'Q153152'),  # Same QID as above
    ('@I7085@', 'Q153152'),  # Same QID as above
    ('@I7109@', 'Q153152'),  # Same QID as above
    ('@I770@', 'Q152943'),
    ('@I771@', 'Q152943'),   # Same QID as above
    ('@I772@', 'Q152943'),   # Same QID as above
    ('@I802@', 'Q152959'),
    ('@I813@', 'Q152962'),
    ('@I825@', 'Q152964'),
    ('@I8867@', 'Q153253'),
    ('@I9147@', 'Q153337'),
    ('@I9203@', 'Q153362'),
    ('@I9343@', 'Q153402'),
    ('@I9367@', 'Q153402'),  # Same QID as above
    ('@I9703@', 'Q152993'),
    ('@I9737@', 'Q152993'),  # Same QID as above
    ('@I9738@', 'Q152993'),  # Same QID as above
    ('@I9777@', 'Q152993'),  # Same QID as above
    ('@I9797@', 'Q152993'),  # Same QID as above
]

def main():
    print("Adding missing QID mappings...")
    
    with open('gedcom_to_qid_mapping.txt', 'a', encoding='utf-8') as f:
        for gedcom_id, qid in missing_mappings:
            f.write(f"{gedcom_id}\t{qid}\n")
            print(f"Added: {gedcom_id} -> {qid}")
    
    print(f"\nAdded {len(missing_mappings)} missing mappings!")

if __name__ == '__main__':
    main()