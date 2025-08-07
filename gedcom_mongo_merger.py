#!/usr/bin/env python3
"""
Advanced GEDCOM Merger using MongoDB for complex genealogical matching
Handles fuzzy matching with family context and reference preservation
"""

import re
import pymongo
from pymongo import MongoClient
from typing import Dict, List, Set, Optional, Tuple
import logging
from datetime import datetime
from difflib import SequenceMatcher
import unicodedata

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GedcomMongoMerger:
    def __init__(self, db_name: str = "genealogy_merge"):
        """Initialize MongoDB connection and collections"""
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        
        # Collections
        self.individuals = self.db.individuals
        self.families = self.db.families
        self.sources = self.db.sources
        self.merge_log = self.db.merge_log
        
        # Create indexes for efficient querying
        self._create_indexes()
        
    def _create_indexes(self):
        """Create MongoDB indexes for efficient querying"""
        # Individual indexes
        self.individuals.create_index([("names.given", "text"), ("names.surname", "text")])
        self.individuals.create_index("geni_id")
        self.individuals.create_index("wikidata_id") 
        self.individuals.create_index("uid")
        self.individuals.create_index("gedcom_id")
        self.individuals.create_index("source_file")
        
        # Family indexes
        self.families.create_index("husband_id")
        self.families.create_index("wife_id")
        self.families.create_index("children")
        
        logger.info("Created MongoDB indexes")
        
    def normalize_name(self, name: str) -> str:
        """Normalize names for comparison"""
        if not name:
            return ""
        # Remove diacritics and normalize unicode
        name = unicodedata.normalize('NFD', name)
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        # Convert to lowercase and remove extra whitespace
        return ' '.join(name.lower().split())
        
    def extract_links_from_notes(self, notes: str) -> Dict[str, str]:
        """Extract Geni and Wikidata links from notes field"""
        links = {}
        
        if not notes:
            return links
            
        # Geni profile patterns
        geni_patterns = [
            r'geni\.com/people/[^/]+/(\d+)',
            r'geni:(\d+)',
            r'geni\.com/profile-(\d+)'
        ]
        
        for pattern in geni_patterns:
            match = re.search(pattern, notes)
            if match:
                links['geni_id'] = match.group(1)
                break
                
        # Wikidata patterns
        wikidata_patterns = [
            r'wikidata\.org/wiki/(Q\d+)',
            r'wikidata:(Q\d+)',
            r'\b(Q\d+)\b'
        ]
        
        for pattern in wikidata_patterns:
            match = re.search(pattern, notes)
            if match:
                links['wikidata_id'] = match.group(1)
                break
                
        return links
        
    def parse_gedcom_individual(self, lines: List[str], start_idx: int) -> Tuple[Dict, int]:
        """Parse an individual record from GEDCOM lines"""
        individual = {
            'names': [],
            'dates': {},
            'places': {},
            'notes': '',
            'sources': [],
            'families_as_spouse': [],
            'families_as_child': []
        }
        
        i = start_idx + 1  # Skip the @I...@ INDI line
        
        while i < len(lines) and not lines[i].startswith('0 @'):
            line = lines[i].strip()
            
            if line.startswith('1 NAME '):
                name_parts = self._parse_name(line[7:])
                individual['names'].append(name_parts)
                
            elif line.startswith('1 SEX '):
                individual['sex'] = line[6:]
                
            elif line.startswith('1 BIRT'):
                birth_info = self._parse_event(lines, i)
                individual['dates']['birth'] = birth_info
                
            elif line.startswith('1 DEAT'):
                death_info = self._parse_event(lines, i)
                individual['dates']['death'] = death_info
                
            elif line.startswith('1 NOTE'):
                note_text = self._parse_multiline_value(lines, i)
                individual['notes'] += note_text + '\n'
                
            elif line.startswith('1 REFN '):
                refn = line[7:]
                if refn.startswith('geni:'):
                    individual['geni_id'] = refn[5:]
                elif refn.startswith('wikidata:'):
                    individual['wikidata_id'] = refn[9:]
                else:
                    individual['refn'] = refn
                    
            elif line.startswith('1 _UID '):
                individual['uid'] = line[7:]
                
            elif line.startswith('1 FAMS @'):
                fam_id = line[8:-1]  # Remove @F...@
                individual['families_as_spouse'].append(fam_id)
                
            elif line.startswith('1 FAMC @'):
                fam_id = line[8:-1]  # Remove @F...@
                individual['families_as_child'].append(fam_id)
                
            i += 1
            
        # Extract additional links from notes
        note_links = self.extract_links_from_notes(individual['notes'])
        for key, value in note_links.items():
            if key not in individual:
                individual[key] = value
                
        return individual, i
        
    def _parse_name(self, name_str: str) -> Dict[str, str]:
        """Parse GEDCOM name format 'Given /Surname/'"""
        name_parts = {'full': name_str}
        
        # Handle /Surname/ format
        surname_match = re.search(r'/([^/]+)/', name_str)
        if surname_match:
            name_parts['surname'] = surname_match.group(1)
            given_part = name_str.replace(surname_match.group(0), '').strip()
            name_parts['given'] = given_part
        else:
            # No surname markers, treat as given name
            name_parts['given'] = name_str.strip()
            
        return name_parts
        
    def _parse_event(self, lines: List[str], start_idx: int) -> Dict:
        """Parse birth/death event with date and place"""
        event = {}
        i = start_idx + 1
        
        while i < len(lines) and (lines[i].startswith('2 ') or lines[i].startswith('3 ')):
            line = lines[i].strip()
            
            if line.startswith('2 DATE '):
                event['date'] = line[7:]
            elif line.startswith('2 PLAC '):
                event['place'] = line[7:]
                
            i += 1
            
        return event
        
    def _parse_multiline_value(self, lines: List[str], start_idx: int) -> str:
        """Parse multiline values like notes"""
        text = ""
        if start_idx < len(lines):
            first_line = lines[start_idx].strip()
            if ' ' in first_line:
                text = first_line.split(' ', 2)[2] if len(first_line.split(' ', 2)) > 2 else ""
        
        i = start_idx + 1
        while i < len(lines) and (lines[i].startswith('2 CONT ') or lines[i].startswith('2 CONC ')):
            line = lines[i].strip()
            if line.startswith('2 CONT '):
                text += '\n' + line[7:]
            elif line.startswith('2 CONC '):
                text += line[7:]
            i += 1
            
        return text.strip()
        
    def import_gedcom(self, filepath: str, source_name: str):
        """Import GEDCOM file into MongoDB"""
        logger.info(f"Importing GEDCOM file: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        individuals_imported = 0
        families_imported = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if re.match(r'^0 @I\d+@ INDI$', line):
                # Parse individual
                gedcom_id = line.split()[1][1:-1]  # Extract I123 from @I123@
                individual, next_i = self.parse_gedcom_individual(lines, i)
                
                individual['gedcom_id'] = gedcom_id
                individual['source_file'] = source_name
                individual['import_date'] = datetime.now()
                
                # Insert or update individual
                self.individuals.replace_one(
                    {'gedcom_id': gedcom_id, 'source_file': source_name},
                    individual,
                    upsert=True
                )
                
                individuals_imported += 1
                i = next_i
                
            elif re.match(r'^0 @F\d+@ FAM$', line):
                # Parse family (simplified for now)
                gedcom_id = line.split()[1][1:-1]  # Extract F123 from @F123@
                family = {'gedcom_id': gedcom_id, 'source_file': source_name}
                
                # Basic family parsing
                j = i + 1
                while j < len(lines) and not lines[j].startswith('0 @'):
                    fam_line = lines[j].strip()
                    if fam_line.startswith('1 HUSB @'):
                        family['husband_id'] = fam_line[8:-1]
                    elif fam_line.startswith('1 WIFE @'):
                        family['wife_id'] = fam_line[8:-1]
                    elif fam_line.startswith('1 CHIL @'):
                        if 'children' not in family:
                            family['children'] = []
                        family['children'].append(fam_line[8:-1])
                    j += 1
                    
                self.families.replace_one(
                    {'gedcom_id': gedcom_id, 'source_file': source_name},
                    family,
                    upsert=True
                )
                
                families_imported += 1
                i = j
            else:
                i += 1
                
        logger.info(f"Imported {individuals_imported} individuals and {families_imported} families from {source_name}")
        
    def name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        if not norm1 or not norm2:
            return 0.0
            
        return SequenceMatcher(None, norm1, norm2).ratio()
        
    def find_potential_matches(self, individual: Dict) -> List[Dict]:
        """Find potential matches for an individual using fuzzy matching"""
        matches = []
        
        # Skip if this is from the same source file
        query = {'source_file': {'$ne': individual['source_file']}}
        
        # Get all candidates from other source files
        candidates = list(self.individuals.find(query))
        
        for candidate in candidates:
            score = self.calculate_match_score(individual, candidate)
            if score > 0.5:  # Threshold for potential matches
                matches.append({
                    'candidate': candidate,
                    'score': score,
                    'reasons': self.get_match_reasons(individual, candidate)
                })
                
        return sorted(matches, key=lambda x: x['score'], reverse=True)
        
    def calculate_match_score(self, ind1: Dict, ind2: Dict) -> float:
        """Calculate overall match score between two individuals"""
        score = 0.0
        factors = 0
        
        # Name similarity
        if ind1.get('names') and ind2.get('names'):
            best_name_score = 0.0
            for name1 in ind1['names']:
                for name2 in ind2['names']:
                    name_score = 0.0
                    if 'given' in name1 and 'given' in name2:
                        name_score += self.name_similarity(name1['given'], name2['given']) * 0.6
                    if 'surname' in name1 and 'surname' in name2:
                        name_score += self.name_similarity(name1['surname'], name2['surname']) * 0.4
                    best_name_score = max(best_name_score, name_score)
            score += best_name_score * 0.4
            factors += 0.4
            
        # Date similarity
        date_score = self.compare_dates(ind1.get('dates', {}), ind2.get('dates', {}))
        if date_score >= 0:
            score += date_score * 0.3
            factors += 0.3
            
        # Family context (parents, spouses, children)
        family_score = self.compare_family_context(ind1, ind2)
        score += family_score * 0.3
        factors += 0.3
        
        return score / factors if factors > 0 else 0.0
        
    def compare_dates(self, dates1: Dict, dates2: Dict) -> float:
        """Compare birth and death dates between individuals"""
        # Simplified date comparison - would need more sophisticated date parsing
        score = 0.0
        comparisons = 0
        
        for event_type in ['birth', 'death']:
            if event_type in dates1 and event_type in dates2:
                date1 = dates1[event_type].get('date', '')
                date2 = dates2[event_type].get('date', '')
                if date1 and date2:
                    # Simple string comparison - would need proper date parsing
                    if date1 == date2:
                        score += 1.0
                    elif any(part in date2 for part in date1.split() if len(part) > 2):
                        score += 0.5
                    comparisons += 1
                    
        return score / comparisons if comparisons > 0 else -1
        
    def compare_family_context(self, ind1: Dict, ind2: Dict) -> float:
        """Compare family relationships to validate matches"""
        # This would need to be implemented to check if parents/spouses/children
        # have similar names or are already matched
        return 0.0  # Placeholder
        
    def get_match_reasons(self, ind1: Dict, ind2: Dict) -> List[str]:
        """Get human-readable reasons for why these individuals might match"""
        reasons = []
        
        # Check name similarities
        if ind1.get('names') and ind2.get('names'):
            for name1 in ind1['names']:
                for name2 in ind2['names']:
                    if 'given' in name1 and 'given' in name2:
                        sim = self.name_similarity(name1['given'], name2['given'])
                        if sim > 0.8:
                            reasons.append(f"Similar given names: '{name1['given']}' vs '{name2['given']}'")
                    if 'surname' in name1 and 'surname' in name2:
                        sim = self.name_similarity(name1['surname'], name2['surname'])
                        if sim > 0.8:
                            reasons.append(f"Similar surnames: '{name1['surname']}' vs '{name2['surname']}'")
                            
        return reasons

if __name__ == "__main__":
    merger = GedcomMongoMerger()
    
    # Import both files
    merger.import_gedcom("new_gedcoms/geni plus wikidata after merge.ged", "geni_wikidata")
    merger.import_gedcom("new_gedcoms/gaiad_ftb_simple_conversion.ged", "gaiad_ftb")
    
    logger.info("Import completed. Ready for matching and merging.")