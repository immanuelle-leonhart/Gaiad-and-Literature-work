#!/usr/bin/env python3
"""
Simple GEDCOM Duplicate Detection (No MongoDB Required)
Pure Python approach for finding duplicates in GEDCOM files
"""

import re
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

class SimpleGedcomDuplicateDetector:
    """Simple GEDCOM duplicate detection without MongoDB"""
    
    def __init__(self):
        self.individuals = {}
        self.families = {}
    
    def parse_name(self, name_str: str) -> Dict[str, str]:
        """Parse GEDCOM name format: Given /Surname/"""
        if not name_str:
            return {"given": "", "surname": "", "full": ""}
        
        # Handle format: Given /Surname/
        surname_match = re.search(r'/([^/]+)/', name_str)
        if surname_match:
            surname = surname_match.group(1).strip()
            given = name_str.replace(f"/{surname}/", "").strip()
        else:
            # No surname markers, treat as given name
            given = name_str.strip()
            surname = ""
        
        return {
            "given": given,
            "surname": surname,
            "full": name_str.strip()
        }
    
    def parse_date(self, date_str: str) -> Dict:
        """Parse GEDCOM date into structured format"""
        if not date_str:
            return {"raw": "", "year": None, "estimated": False}
        
        # Extract year from various GEDCOM date formats
        year_match = re.search(r'\b(\d{4})\b', date_str)
        year = int(year_match.group(1)) if year_match else None
        
        # Check if it's estimated (ABT, AFT, BEF, etc.)
        estimated = any(prefix in date_str.upper() for prefix in ['ABT', 'AFT', 'BEF', 'EST', 'CAL'])
        
        return {
            "raw": date_str.strip(),
            "year": year,
            "estimated": estimated
        }
    
    def import_gedcom(self, gedcom_path: str) -> int:
        """Import GEDCOM file into memory"""
        print(f"Importing GEDCOM: {gedcom_path}")
        
        self.individuals = {}
        self.families = {}
        current_record = None
        current_type = None
        current_birth = False
        current_death = False
        current_marriage = False
        
        # Handle BOM and encoding issues
        with open(gedcom_path, 'r', encoding='utf-8-sig') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip()
                if not line:
                    continue
                
                # Parse GEDCOM level and content
                try:
                    parts = line.split(' ', 2)
                    if len(parts) < 2:
                        continue
                    
                    level = int(parts[0])
                    tag = parts[1]
                    value = parts[2] if len(parts) > 2 else ""
                except (ValueError, IndexError):
                    continue
                
                # Start new record
                if level == 0:
                    current_birth = False
                    current_death = False
                    current_marriage = False
                    
                    if tag.startswith('@') and tag.endswith('@'):
                        record_id = tag[1:-1]  # Remove @ symbols
                        record_type = value
                        
                        if record_type == "INDI":
                            current_record = {
                                "_id": record_id,
                                "gedcom_id": tag,
                                "names": [],
                                "birth": {"raw": "", "year": None, "estimated": False},
                                "death": {"raw": "", "year": None, "estimated": False},
                                "sex": "",
                                "father_id": "",
                                "mother_id": "",
                                "families": []
                            }
                            self.individuals[record_id] = current_record
                            current_type = "INDI"
                        elif record_type == "FAM":
                            current_record = {
                                "_id": record_id,
                                "gedcom_id": tag,
                                "husband_id": "",
                                "wife_id": "",
                                "children": [],
                                "marriage": {"raw": "", "year": None, "estimated": False}
                            }
                            self.families[record_id] = current_record
                            current_type = "FAM"
                        else:
                            current_record = None
                            current_type = None
                
                elif current_record and level == 1:
                    if current_type == "INDI":
                        if tag == "NAME":
                            parsed_name = self.parse_name(value)
                            current_record["names"].append(parsed_name)
                        elif tag == "SEX":
                            current_record["sex"] = value
                        elif tag == "BIRT":
                            current_birth = True
                            current_death = False
                        elif tag == "DEAT":
                            current_death = True
                            current_birth = False
                        elif tag == "FAMC":  # Family as child
                            current_record["families"].append({"type": "child", "family_id": value[1:-1]})
                        elif tag == "FAMS":  # Family as spouse
                            current_record["families"].append({"type": "spouse", "family_id": value[1:-1]})
                    
                    elif current_type == "FAM":
                        if tag == "HUSB":
                            current_record["husband_id"] = value[1:-1]
                        elif tag == "WIFE":
                            current_record["wife_id"] = value[1:-1]
                        elif tag == "CHIL":
                            current_record["children"].append(value[1:-1])
                        elif tag == "MARR":
                            current_marriage = True
                
                elif current_record and level == 2:
                    if tag == "DATE":
                        if current_type == "INDI":
                            if current_birth:
                                current_record["birth"] = self.parse_date(value)
                            elif current_death:
                                current_record["death"] = self.parse_date(value)
                        elif current_type == "FAM":
                            if current_marriage:
                                current_record["marriage"] = self.parse_date(value)
                
                # Progress indicator
                if line_num % 100000 == 0:
                    print(f"Processed {line_num:,} lines...")
        
        # Resolve family relationships
        print("Resolving family relationships...")
        for individual in self.individuals.values():
            for family_ref in individual["families"]:
                if family_ref["type"] == "child":
                    family_id = family_ref["family_id"]
                    if family_id in self.families:
                        family = self.families[family_id]
                        if family["husband_id"]:
                            individual["father_id"] = family["husband_id"]
                        if family["wife_id"]:
                            individual["mother_id"] = family["wife_id"]
        
        print(f"Import complete: {len(self.individuals):,} individuals, {len(self.families):,} families")
        return len(self.individuals)
    
    def calculate_name_similarity(self, name1: Dict, name2: Dict) -> float:
        """Calculate similarity between two names"""
        if not name1["full"] or not name2["full"]:
            return 0.0
        
        # Compare full names
        full_similarity = SequenceMatcher(None, 
                                        name1["full"].lower(), 
                                        name2["full"].lower()).ratio()
        
        # Compare given names specifically
        given_similarity = 0.0
        if name1["given"] and name2["given"]:
            given_similarity = SequenceMatcher(None, 
                                            name1["given"].lower(), 
                                            name2["given"].lower()).ratio()
        
        # Compare surnames specifically
        surname_similarity = 0.0
        if name1["surname"] and name2["surname"]:
            surname_similarity = SequenceMatcher(None, 
                                               name1["surname"].lower(), 
                                               name2["surname"].lower()).ratio()
        
        # Weighted average (surname is most important for genealogy)
        return (full_similarity * 0.3 + given_similarity * 0.3 + surname_similarity * 0.4)
    
    def calculate_date_similarity(self, date1: Dict, date2: Dict) -> float:
        """Calculate similarity between two dates"""
        if not date1["year"] or not date2["year"]:
            return 0.0
        
        year_diff = abs(date1["year"] - date2["year"])
        
        # Perfect match
        if year_diff == 0:
            return 1.0
        
        # Close matches get high scores
        if year_diff <= 2:
            return 0.8
        elif year_diff <= 5:
            return 0.6
        elif year_diff <= 10:
            return 0.4
        elif year_diff <= 20:
            return 0.2
        else:
            return 0.0
    
    def get_person_name(self, person_id: str) -> str:
        """Get full name for a person ID"""
        if not person_id or person_id not in self.individuals:
            return ""
        
        person = self.individuals[person_id]
        if person["names"]:
            return person["names"][0]["full"]
        return ""
    
    def calculate_individual_similarity(self, person1: Dict, person2: Dict) -> float:
        """Calculate overall similarity between two individuals"""
        
        # Skip if no names
        if not person1["names"] or not person2["names"]:
            return 0.0
        
        # Name similarity (most important)
        name_score = self.calculate_name_similarity(person1["names"][0], person2["names"][0])
        
        # Birth date similarity
        birth_score = self.calculate_date_similarity(person1["birth"], person2["birth"])
        
        # Death date similarity  
        death_score = self.calculate_date_similarity(person1["death"], person2["death"])
        
        # Parent name similarity (very important for genealogy)
        father_score = 0.0
        mother_score = 0.0
        
        if person1["father_id"] and person2["father_id"]:
            father1_name = self.get_person_name(person1["father_id"])
            father2_name = self.get_person_name(person2["father_id"])
            if father1_name and father2_name:
                father_score = SequenceMatcher(None, father1_name.lower(), father2_name.lower()).ratio()
        
        if person1["mother_id"] and person2["mother_id"]:
            mother1_name = self.get_person_name(person1["mother_id"])
            mother2_name = self.get_person_name(person2["mother_id"])
            if mother1_name and mother2_name:
                mother_score = SequenceMatcher(None, mother1_name.lower(), mother2_name.lower()).ratio()
        
        # Weighted scoring (name and parents are most important)
        total_score = (
            name_score * 0.4 +
            birth_score * 0.2 +
            death_score * 0.1 +
            father_score * 0.15 +
            mother_score * 0.15
        )
        
        return total_score
    
    def find_duplicates(self, min_score: float = 0.7) -> List[Dict]:
        """Find potential duplicates using similarity scoring"""
        print(f"Finding duplicates with minimum score: {min_score}")
        
        duplicates = []
        individuals = list(self.individuals.values())
        
        print(f"Comparing {len(individuals):,} individuals...")
        
        for i, person1 in enumerate(individuals):
            if i % 1000 == 0:
                print(f"Processed {i:,} individuals...")
            
            # Only compare with individuals that come after in the list to avoid duplicates
            for person2 in individuals[i+1:]:
                score = self.calculate_individual_similarity(person1, person2)
                
                if score >= min_score:
                    # Get parent names for context
                    father1_name = self.get_person_name(person1["father_id"])
                    mother1_name = self.get_person_name(person1["mother_id"])
                    father2_name = self.get_person_name(person2["father_id"])
                    mother2_name = self.get_person_name(person2["mother_id"])
                    
                    duplicates.append({
                        "score": round(score * 100, 1),
                        "id1": person1["_id"],
                        "name1": person1["names"][0]["full"] if person1["names"] else "",
                        "birth1": person1["birth"]["raw"],
                        "death1": person1["death"]["raw"],
                        "father1": father1_name,
                        "mother1": mother1_name,
                        "id2": person2["_id"],
                        "name2": person2["names"][0]["full"] if person2["names"] else "",
                        "birth2": person2["birth"]["raw"],
                        "death2": person2["death"]["raw"],
                        "father2": father2_name,
                        "mother2": mother2_name
                    })
        
        # Sort by score descending
        duplicates.sort(key=lambda x: x["score"], reverse=True)
        
        print(f"Found {len(duplicates)} potential duplicate pairs")
        return duplicates
    
    def export_duplicates_csv(self, duplicates: List[Dict], output_path: str):
        """Export duplicates to CSV for manual review"""
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Score', 'ID1', 'Name1', 'Birth1', 'Death1', 'Father1', 'Mother1',
                'ID2', 'Name2', 'Birth2', 'Death2', 'Father2', 'Mother2'
            ])
            
            writer.writeheader()
            for dup in duplicates:
                writer.writerow({
                    'Score': f"{dup['score']:.1f}%",
                    'ID1': dup['id1'],
                    'Name1': dup['name1'],
                    'Birth1': dup['birth1'],
                    'Death1': dup['death1'],
                    'Father1': dup['father1'],
                    'Mother1': dup['mother1'],
                    'ID2': dup['id2'],
                    'Name2': dup['name2'],
                    'Birth2': dup['birth2'],
                    'Death2': dup['death2'],
                    'Father2': dup['father2'],
                    'Mother2': dup['mother2']
                })
        
        print(f"Duplicates exported to: {output_path}")

def main():
    """Run the simple duplicate detection"""
    
    detector = SimpleGedcomDuplicateDetector()
    
    # File paths
    gedcom_path = r"C:\Users\Immanuelle\Documents\Github\Gaiad-Genealogy\new_gedcoms\source gedcoms\master_combined.ged"
    output_csv = r"C:\Users\Immanuelle\Documents\Github\Gaiad-Genealogy\simple_duplicates.csv"
    
    print("Simple GEDCOM Duplicate Detection")
    print("=" * 50)
    
    # Import GEDCOM
    if Path(gedcom_path).exists():
        count = detector.import_gedcom(gedcom_path)
        print(f"Successfully imported {count:,} individuals")
    else:
        print(f"GEDCOM file not found: {gedcom_path}")
        return
    
    # Find duplicates
    duplicates = detector.find_duplicates(min_score=0.7)
    
    # Export to CSV
    if duplicates:
        detector.export_duplicates_csv(duplicates, output_csv)
        print(f"\n{len(duplicates)} duplicate pairs found and exported to CSV")
        print("Review the CSV file to manually verify matches!")
    else:
        print("No duplicates found with the current threshold")

if __name__ == "__main__":
    main()