#!/usr/bin/env python3
"""
Efficient GEDCOM Merger - processes large files with progress tracking
"""

import re
import pymongo
from pymongo import MongoClient
from typing import Dict, List, Set, Optional, Tuple
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EfficientGedcomMerger:
    def __init__(self, db_name: str = "genealogy_merge"):
        """Initialize MongoDB connection"""
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        
        # Clear existing collections
        self.db.individuals.drop()
        self.db.families.drop()
        
        self.individuals = self.db.individuals
        self.families = self.db.families
        
        # Create indexes
        self.individuals.create_index("gedcom_id")
        self.individuals.create_index("source_file")
        logger.info("MongoDB collections reset and indexed")
        
    def extract_basic_links(self, notes: str) -> Dict[str, str]:
        """Quick extraction of Geni and Wikidata links"""
        links = {}
        if not notes:
            return links
            
        # Quick Geni ID extraction
        geni_match = re.search(r'geni:(\d+)|geni\.com/people/[^/]+/(\d+)', notes)
        if geni_match:
            links['geni_id'] = geni_match.group(1) or geni_match.group(2)
            
        # Quick Wikidata extraction  
        wikidata_match = re.search(r'(Q\d+)', notes)
        if wikidata_match:
            links['wikidata_id'] = wikidata_match.group(1)
            
        return links
        
    def parse_gedcom_fast(self, filepath: str, source_name: str):
        """Fast GEDCOM parsing with progress tracking"""
        logger.info(f"Starting fast import of {filepath}")
        start_time = time.time()
        
        individuals = []
        families = []
        current_record = None
        record_type = None
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            line_count = 0
            
            for line in f:
                line_count += 1
                if line_count % 100000 == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"Processed {line_count} lines in {elapsed:.1f}s ({source_name})")
                
                line = line.strip()
                
                # Start of individual record
                if re.match(r'^0 @I\d+@ INDI$', line):
                    # Save previous record
                    if current_record and record_type == 'INDI':
                        individuals.append(current_record)
                        
                    gedcom_id = line.split()[1][1:-1]
                    current_record = {
                        'gedcom_id': gedcom_id,
                        'source_file': source_name,
                        'names': [],
                        'import_date': datetime.now()
                    }
                    record_type = 'INDI'
                    
                # Start of family record
                elif re.match(r'^0 @F\d+@ FAM$', line):
                    # Save previous record
                    if current_record:
                        if record_type == 'INDI':
                            individuals.append(current_record)
                        elif record_type == 'FAM':
                            families.append(current_record)
                            
                    gedcom_id = line.split()[1][1:-1]
                    current_record = {
                        'gedcom_id': gedcom_id,
                        'source_file': source_name,
                        'children': []
                    }
                    record_type = 'FAM'
                    
                # Parse individual fields
                elif current_record and record_type == 'INDI':
                    if line.startswith('1 NAME '):
                        name = line[7:]
                        current_record['names'].append({'full': name})
                    elif line.startswith('1 SEX '):
                        current_record['sex'] = line[6:]
                    elif line.startswith('1 NOTE'):
                        note_text = line[7:] if len(line) > 7 else ""
                        current_record['notes'] = note_text
                        # Extract links quickly
                        links = self.extract_basic_links(note_text)
                        current_record.update(links)
                    elif line.startswith('1 REFN '):
                        refn = line[7:]
                        if refn.startswith('geni:'):
                            current_record['geni_id'] = refn[5:]
                        elif refn.startswith('wikidata:'):
                            current_record['wikidata_id'] = refn[9:]
                    elif line.startswith('1 _UID '):
                        current_record['uid'] = line[7:]
                        
                # Parse family fields
                elif current_record and record_type == 'FAM':
                    if line.startswith('1 HUSB @'):
                        current_record['husband_id'] = line[8:-1]
                    elif line.startswith('1 WIFE @'):
                        current_record['wife_id'] = line[8:-1]
                    elif line.startswith('1 CHIL @'):
                        current_record['children'].append(line[8:-1])
                        
                # Batch insert every 5000 records
                if len(individuals) >= 5000:
                    self.individuals.insert_many(individuals)
                    individuals = []
                    logger.info(f"Inserted batch of individuals ({source_name})")
                    
                if len(families) >= 2000:
                    self.families.insert_many(families) 
                    families = []
                    logger.info(f"Inserted batch of families ({source_name})")
                    
            # Save final records
            if current_record:
                if record_type == 'INDI':
                    individuals.append(current_record)
                elif record_type == 'FAM':
                    families.append(current_record)
                    
            # Insert remaining records
            if individuals:
                self.individuals.insert_many(individuals)
            if families:
                self.families.insert_many(families)
                
        total_time = time.time() - start_time
        ind_count = self.individuals.count_documents({'source_file': source_name})
        fam_count = self.families.count_documents({'source_file': source_name})
        
        logger.info(f"Completed {source_name}: {ind_count} individuals, {fam_count} families in {total_time:.1f}s")
        
    def find_obvious_duplicates(self):
        """Find obvious duplicates based on exact ID matches"""
        logger.info("Finding obvious duplicates...")
        
        # Find Geni ID duplicates
        pipeline = [
            {'$match': {'geni_id': {'$exists': True, '$ne': None}}},
            {'$group': {'_id': '$geni_id', 'docs': {'$push': '$$ROOT'}, 'count': {'$sum': 1}}},
            {'$match': {'count': {'$gt': 1}}}
        ]
        
        geni_duplicates = list(self.individuals.aggregate(pipeline))
        logger.info(f"Found {len(geni_duplicates)} Geni ID duplicate groups")
        
        # Find Wikidata ID duplicates  
        pipeline[0]['$match'] = {'wikidata_id': {'$exists': True, '$ne': None}}
        pipeline[1]['$group']['_id'] = '$wikidata_id'
        
        wikidata_duplicates = list(self.individuals.aggregate(pipeline))
        logger.info(f"Found {len(wikidata_duplicates)} Wikidata ID duplicate groups")
        
        return geni_duplicates + wikidata_duplicates
        
    def merge_obvious_duplicates(self):
        """Merge obvious duplicates and mark originals"""
        duplicates = self.find_obvious_duplicates()
        merged_count = 0
        
        for dup_group in duplicates:
            docs = dup_group['docs']
            if len(docs) < 2:
                continue
                
            # Use the most complete record as primary
            primary = max(docs, key=lambda x: len(str(x.get('notes', '')) + str(x.get('names', []))))
            others = [doc for doc in docs if doc['_id'] != primary['_id']]
            
            # Merge data
            merged = primary.copy()
            all_names = set()
            all_notes = []
            
            for doc in docs:
                for name in doc.get('names', []):
                    all_names.add(name.get('full', ''))
                if doc.get('notes'):
                    all_notes.append(doc['notes'])
                    
            merged['all_names'] = list(all_names)
            merged['merged_notes'] = '\n---\n'.join(all_notes)
            merged['merge_date'] = datetime.now()
            merged['original_count'] = len(docs)
            
            # Insert merged record
            result = self.individuals.insert_one(merged)
            
            # Mark originals as merged
            original_ids = [doc['_id'] for doc in docs]
            self.individuals.update_many(
                {'_id': {'$in': original_ids}},
                {'$set': {'merged': True, 'merged_into': result.inserted_id}}
            )
            
            merged_count += 1
            
        logger.info(f"Merged {merged_count} obvious duplicate groups")
        
    def get_stats(self):
        """Get database statistics"""
        stats = {}
        stats['total_individuals'] = self.individuals.count_documents({})
        stats['active_individuals'] = self.individuals.count_documents({'merged': {'$ne': True}})
        stats['merged_individuals'] = self.individuals.count_documents({'merged': True})
        stats['total_families'] = self.families.count_documents({})
        
        # Source breakdown
        stats['by_source'] = {}
        for source in ['geni_wikidata', 'gaiad_ftb']:
            stats['by_source'][source] = self.individuals.count_documents({
                'source_file': source, 
                'merged': {'$ne': True}
            })
            
        return stats

if __name__ == "__main__":
    merger = EfficientGedcomMerger()
    
    # Import files
    merger.parse_gedcom_fast("new_gedcoms/geni plus wikidata after merge.ged", "geni_wikidata")
    merger.parse_gedcom_fast("new_gedcoms/gaiad_ftb_simple_conversion.ged", "gaiad_ftb")
    
    # Quick deduplication
    merger.merge_obvious_duplicates()
    
    # Show stats
    stats = merger.get_stats()
    print("\n=== FINAL STATISTICS ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
        
    logger.info("Import and basic merging completed!")