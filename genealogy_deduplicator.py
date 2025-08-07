#!/usr/bin/env python3
"""
Genealogy Deduplication and Merging Tool
Phase 2: Internal deduplication and intelligent merging
"""

import pymongo
from pymongo import MongoClient
from typing import Dict, List, Set, Optional, Tuple, Any
import logging
from datetime import datetime
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class GenealogicalDeduplicator:
    def __init__(self, db_name: str = "genealogy_merge"):
        """Initialize MongoDB connection"""
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        
        self.individuals = self.db.individuals
        self.families = self.db.families
        self.duplicates = self.db.duplicates
        self.merge_log = self.db.merge_log
        
    def find_internal_duplicates(self, source_file: str) -> List[Dict]:
        """Find duplicates within a single source file (e.g., geni+wikidata)"""
        logger.info(f"Finding internal duplicates in {source_file}")
        
        duplicates = []
        processed = set()
        
        # Get all individuals from this source
        individuals = list(self.individuals.find({'source_file': source_file}))
        
        for i, ind1 in enumerate(individuals):
            if ind1['_id'] in processed:
                continue
                
            potential_duplicates = []
            
            for j, ind2 in enumerate(individuals[i+1:], i+1):
                if ind2['_id'] in processed:
                    continue
                    
                # Check if these might be the same person
                if self.are_likely_duplicates(ind1, ind2):
                    potential_duplicates.append(ind2)
                    processed.add(ind2['_id'])
                    
            if potential_duplicates:
                duplicate_group = {
                    'primary': ind1,
                    'duplicates': potential_duplicates,
                    'source_file': source_file,
                    'found_date': datetime.now()
                }
                duplicates.append(duplicate_group)
                processed.add(ind1['_id'])
                
        logger.info(f"Found {len(duplicates)} potential duplicate groups in {source_file}")
        return duplicates
        
    def are_likely_duplicates(self, ind1: Dict, ind2: Dict) -> bool:
        """Determine if two individuals are likely the same person"""
        
        # Exact Geni ID match
        if (ind1.get('geni_id') and ind2.get('geni_id') and 
            ind1['geni_id'] == ind2['geni_id']):
            return True
            
        # Exact Wikidata ID match
        if (ind1.get('wikidata_id') and ind2.get('wikidata_id') and 
            ind1['wikidata_id'] == ind2['wikidata_id']):
            return True
            
        # High name similarity + date compatibility
        name_sim = self.best_name_similarity(ind1, ind2)
        date_compatible = self.dates_compatible(ind1, ind2)
        
        if name_sim > 0.85 and date_compatible:
            return True
            
        # Similar names + same family context
        if name_sim > 0.7 and self.similar_family_context(ind1, ind2):
            return True
            
        return False
        
    def best_name_similarity(self, ind1: Dict, ind2: Dict) -> float:
        """Get the best name similarity score between two individuals"""
        if not ind1.get('names') or not ind2.get('names'):
            return 0.0
            
        best_score = 0.0
        
        for name1 in ind1['names']:
            for name2 in ind2['names']:
                score = 0.0
                comparisons = 0
                
                # Compare given names
                if name1.get('given') and name2.get('given'):
                    given_sim = self.fuzzy_name_match(name1['given'], name2['given'])
                    score += given_sim * 0.6
                    comparisons += 0.6
                    
                # Compare surnames
                if name1.get('surname') and name2.get('surname'):
                    surname_sim = self.fuzzy_name_match(name1['surname'], name2['surname'])
                    score += surname_sim * 0.4
                    comparisons += 0.4
                    
                if comparisons > 0:
                    final_score = score / comparisons
                    best_score = max(best_score, final_score)
                    
        return best_score
        
    def fuzzy_name_match(self, name1: str, name2: str) -> float:
        """Fuzzy matching for names with various normalizations"""
        from difflib import SequenceMatcher
        
        # Normalize both names
        norm1 = self.normalize_name_for_matching(name1)
        norm2 = self.normalize_name_for_matching(name2)
        
        if not norm1 or not norm2:
            return 0.0
            
        # Direct comparison
        direct_sim = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Check for common name variations
        variation_sim = self.check_name_variations(norm1, norm2)
        
        return max(direct_sim, variation_sim)
        
    def normalize_name_for_matching(self, name: str) -> str:
        """Normalize name for matching purposes"""
        if not name:
            return ""
            
        import unicodedata
        
        # Remove diacritics
        name = unicodedata.normalize('NFD', name)
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        
        # Convert to lowercase
        name = name.lower()
        
        # Remove common prefixes/suffixes
        prefixes = ['mr.', 'mrs.', 'dr.', 'prof.', 'sir', 'lady']
        suffixes = ['jr.', 'sr.', 'ii', 'iii', 'iv']
        
        words = name.split()
        filtered_words = []
        
        for word in words:
            if word not in prefixes and word not in suffixes:
                # Remove punctuation
                clean_word = re.sub(r'[^\w]', '', word)
                if clean_word:
                    filtered_words.append(clean_word)
                    
        return ' '.join(filtered_words)
        
    def check_name_variations(self, name1: str, name2: str) -> float:
        """Check for common name variations and nicknames"""
        # Common nickname mappings
        nicknames = {
            'william': ['bill', 'will', 'billy', 'willy'],
            'robert': ['bob', 'rob', 'bobby', 'robbie'],
            'richard': ['rick', 'dick', 'richie', 'rich'],
            'michael': ['mike', 'mickey', 'mick'],
            'elizabeth': ['liz', 'beth', 'betty', 'eliza'],
            'margaret': ['maggie', 'meg', 'peggy', 'margie'],
            'catherine': ['kate', 'katie', 'cathy', 'kitty'],
            'patricia': ['pat', 'patty', 'trish', 'tricia']
        }
        
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        # Check if any word in name1 is a nickname of any word in name2 or vice versa
        for word1 in words1:
            for word2 in words2:
                # Check direct nickname match
                for full_name, nicks in nicknames.items():
                    if ((word1 == full_name and word2 in nicks) or 
                        (word2 == full_name and word1 in nicks)):
                        return 0.9
                        
                # Check partial matches (e.g., "Alex" and "Alexander")
                if len(word1) >= 3 and len(word2) >= 3:
                    if word1.startswith(word2) or word2.startswith(word1):
                        return 0.8
                        
        return 0.0
        
    def dates_compatible(self, ind1: Dict, ind2: Dict) -> bool:
        """Check if dates are compatible (not conflicting)"""
        dates1 = ind1.get('dates', {})
        dates2 = ind2.get('dates', {})
        
        # If no dates, assume compatible
        if not dates1 or not dates2:
            return True
            
        # Check birth dates
        if 'birth' in dates1 and 'birth' in dates2:
            if not self.dates_match_or_compatible(
                dates1['birth'].get('date'), 
                dates2['birth'].get('date')
            ):
                return False
                
        # Check death dates  
        if 'death' in dates1 and 'death' in dates2:
            if not self.dates_match_or_compatible(
                dates1['death'].get('date'),
                dates2['death'].get('date')
            ):
                return False
                
        return True
        
    def dates_match_or_compatible(self, date1: str, date2: str) -> bool:
        """Check if two date strings are compatible"""
        if not date1 or not date2:
            return True
            
        # Simple compatibility check - would need more sophisticated parsing
        # For now, just check if they share common elements
        if date1 == date2:
            return True
            
        # Extract years
        year1 = re.search(r'\b(1\d{3}|20\d{2})\b', date1)
        year2 = re.search(r'\b(1\d{3}|20\d{2})\b', date2)
        
        if year1 and year2:
            y1, y2 = int(year1.group(1)), int(year2.group(1))
            # Allow 1-2 year difference for birth dates
            return abs(y1 - y2) <= 2
            
        # If we can't parse years, assume compatible
        return True
        
    def similar_family_context(self, ind1: Dict, ind2: Dict) -> bool:
        """Check if individuals have similar family contexts"""
        # Compare parents, spouses, children names
        # This would require loading family records and comparing
        # For now, simplified implementation
        
        families1 = set(ind1.get('families_as_spouse', []) + ind1.get('families_as_child', []))
        families2 = set(ind2.get('families_as_spouse', []) + ind2.get('families_as_child', []))
        
        # If they share any family IDs, they're definitely related
        if families1.intersection(families2):
            return True
            
        # More sophisticated family context comparison would go here
        return False
        
    def merge_duplicate_individuals(self, duplicate_group: Dict) -> Dict:
        """Merge a group of duplicate individuals into one consolidated record"""
        primary = duplicate_group['primary'].copy()
        duplicates = duplicate_group['duplicates']
        
        # Collect all data from duplicates
        all_names = set()
        all_geni_ids = set()
        all_wikidata_ids = set()
        all_notes = []
        all_sources = set()
        
        # Process primary record
        for name in primary.get('names', []):
            if name.get('full'):
                all_names.add(name['full'])
        if primary.get('geni_id'):
            all_geni_ids.add(primary['geni_id'])
        if primary.get('wikidata_id'):
            all_wikidata_ids.add(primary['wikidata_id'])
        if primary.get('notes'):
            all_notes.append(primary['notes'])
            
        # Process duplicates
        for dup in duplicates:
            for name in dup.get('names', []):
                if name.get('full'):
                    all_names.add(name['full'])
            if dup.get('geni_id'):
                all_geni_ids.add(dup['geni_id'])
            if dup.get('wikidata_id'):
                all_wikidata_ids.add(dup['wikidata_id'])
            if dup.get('notes'):
                all_notes.append(dup['notes'])
                
        # Create merged record
        merged = primary.copy()
        merged['all_names'] = list(all_names)
        merged['all_geni_ids'] = list(all_geni_ids) 
        merged['all_wikidata_ids'] = list(all_wikidata_ids)
        merged['merged_notes'] = '\n---\n'.join(all_notes)
        merged['merge_date'] = datetime.now()
        merged['original_ids'] = [primary['_id']] + [dup['_id'] for dup in duplicates]
        
        return merged
        
    def process_deduplication(self, source_file: str):
        """Main deduplication process for a source file"""
        logger.info(f"Starting deduplication process for {source_file}")
        
        # Find duplicates
        duplicate_groups = self.find_internal_duplicates(source_file)
        
        # Process each duplicate group
        merged_count = 0
        for group in duplicate_groups:
            merged_record = self.merge_duplicate_individuals(group)
            
            # Save merged record
            self.individuals.insert_one(merged_record)
            
            # Mark original records as merged
            original_ids = [group['primary']['_id']] + [dup['_id'] for dup in group['duplicates']]
            self.individuals.update_many(
                {'_id': {'$in': original_ids}},
                {'$set': {'merged': True, 'merged_into': merged_record['_id']}}
            )
            
            merged_count += 1
            
        logger.info(f"Completed deduplication: merged {merged_count} duplicate groups")

if __name__ == "__main__":
    deduplicator = GenealogicalDeduplicator()
    
    # First deduplicate the geni+wikidata file internally
    deduplicator.process_deduplication("geni_wikidata")
    
    logger.info("Deduplication completed")