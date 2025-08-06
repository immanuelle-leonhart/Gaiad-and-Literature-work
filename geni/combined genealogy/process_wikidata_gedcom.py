#!/usr/bin/env python3
"""
Script to process wikidata_combined.ged file:
1. Extract Q-IDs from entries with Q-ID names
2. Fetch Wikidata labels in all languages
3. Extract Geni.com profile IDs (P2600)
4. Update GEDCOM with proper names and Geni profile information
"""

import re
import json
import requests
import time
from typing import Dict, List, Set, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WikidataGedcomProcessor:
    def __init__(self, gedcom_file: str):
        self.gedcom_file = gedcom_file
        self.wikidata_api = "https://www.wikidata.org/w/api.php"
        self.sparql_endpoint = "https://query.wikidata.org/sparql"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikidataGedcomProcessor/1.0 (genealogy research)'
        })
        
        # Storage for processed data
        self.q_ids: Set[str] = set()
        self.individuals_with_qid_names: List[Dict] = []
        self.wikidata_labels: Dict[str, Dict] = {}
        self.geni_profiles: Dict[str, str] = {}
        
    def parse_gedcom(self) -> None:
        """Parse GEDCOM file to extract Q-IDs and individuals with Q-ID names"""
        logger.info("Parsing GEDCOM file...")
        
        with open(self.gedcom_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_individual = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Start of individual
            if re.match(r'0 @I\d+@ INDI', line):
                current_individual = {
                    'id': re.search(r'@(I\d+)@', line).group(1),
                    'line_start': i,
                    'refn': None,
                    'name_line': None,
                    'has_qid_name': False
                }
            
            # Name line
            elif current_individual and line.startswith('1 NAME '):
                current_individual['name_line'] = i
                name_match = re.search(r'1 NAME (Q\d+)', line)
                if name_match:
                    current_individual['has_qid_name'] = True
                    current_individual['qid'] = name_match.group(1)
                    self.q_ids.add(name_match.group(1))
            
            # REFN line
            elif current_individual and line.startswith('1 REFN '):
                refn_match = re.search(r'1 REFN (Q\d+)', line)
                if refn_match:
                    current_individual['refn'] = refn_match.group(1)
                    current_individual['refn_line'] = i
                    self.q_ids.add(refn_match.group(1))
            
            # End of individual (next individual or end of file)
            elif (re.match(r'0 @I\d+@ INDI', line) or i == len(lines) - 1) and current_individual:
                current_individual['line_end'] = i - 1 if i < len(lines) - 1 else i
                
                if current_individual['has_qid_name'] or current_individual['refn']:
                    self.individuals_with_qid_names.append(current_individual)
                
                # Start processing next individual
                if i < len(lines) - 1:
                    current_individual = {
                        'id': re.search(r'@(I\d+)@', line).group(1),
                        'line_start': i,
                        'refn': None,
                        'name_line': None,
                        'has_qid_name': False
                    }
                else:
                    current_individual = None
            
            i += 1
        
        logger.info(f"Found {len(self.q_ids)} unique Q-IDs")
        logger.info(f"Found {len(self.individuals_with_qid_names)} individuals needing processing")
    
    def fetch_wikidata_labels(self) -> None:
        """Fetch labels in all languages for all Q-IDs"""
        logger.info(f"Fetching Wikidata labels for {len(self.q_ids)} Q-IDs...")
        
        # Process Q-IDs in batches of 50
        q_id_list = list(self.q_ids)
        batch_size = 50
        total_batches = (len(q_id_list) + batch_size - 1) // batch_size
        
        for i in range(0, len(q_id_list), batch_size):
            batch_num = i // batch_size + 1
            batch = q_id_list[i:i + batch_size]
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} Q-IDs)")
            self._fetch_batch_labels(batch)
            time.sleep(0.5)  # Be respectful to Wikidata API
            
            # Save progress every 100 batches
            if batch_num % 100 == 0:
                self._save_progress()
        
        self._save_progress()  # Final save
    
    def _fetch_batch_labels(self, qids: List[str]) -> None:
        """Fetch labels for a batch of Q-IDs"""
        entities = '|'.join(qids)
        
        params = {
            'action': 'wbgetentities',
            'ids': entities,
            'props': 'labels|claims',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.wikidata_api, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'entities' in data:
                for qid, entity_data in data['entities'].items():
                    if 'missing' not in entity_data:
                        # Extract labels
                        labels = entity_data.get('labels', {})
                        self.wikidata_labels[qid] = {
                            'labels': {lang: label['value'] for lang, label in labels.items()},
                            'english_name': labels.get('en', {}).get('value', qid)
                        }
                        
                        # Extract Geni profile ID (P2600)
                        claims = entity_data.get('claims', {})
                        if 'P2600' in claims:
                            for claim in claims['P2600']:
                                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                                    geni_id = claim['mainsnak']['datavalue']['value']
                                    self.geni_profiles[qid] = geni_id
                                    break
                    else:
                        logger.warning(f"Entity {qid} not found in Wikidata")
                        
        except Exception as e:
            logger.error(f"Error fetching batch {qids}: {e}")
    
    def _save_progress(self) -> None:
        """Save progress to JSON file"""
        progress_data = {
            'wikidata_labels': self.wikidata_labels,
            'geni_profiles': self.geni_profiles
        }
        with open('wikidata_progress.json', 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Progress saved: {len(self.wikidata_labels)} labels, {len(self.geni_profiles)} Geni profiles")
    
    def _load_progress(self) -> bool:
        """Load progress from JSON file"""
        try:
            with open('wikidata_progress.json', 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                self.wikidata_labels = progress_data.get('wikidata_labels', {})
                self.geni_profiles = progress_data.get('geni_profiles', {})
                logger.info(f"Progress loaded: {len(self.wikidata_labels)} labels, {len(self.geni_profiles)} Geni profiles")
                return True
        except FileNotFoundError:
            logger.info("No progress file found, starting fresh")
            return False
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
            return False
    
    def generate_labels_report(self) -> None:
        """Generate a text file with all labels for review"""
        logger.info("Generating labels report...")
        
        with open('wikidata_labels_report.txt', 'w', encoding='utf-8') as f:
            f.write("WIKIDATA LABELS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            for qid in sorted(self.q_ids):
                f.write(f"Q-ID: {qid}\n")
                if qid in self.wikidata_labels:
                    labels = self.wikidata_labels[qid]['labels']
                    english_name = self.wikidata_labels[qid]['english_name']
                    
                    f.write(f"Suggested English Name: {english_name}\n")
                    f.write("All Language Labels:\n")
                    
                    for lang, label in sorted(labels.items()):
                        f.write(f"  {lang}: {label}\n")
                else:
                    f.write("No data found\n")
                
                if qid in self.geni_profiles:
                    f.write(f"Geni Profile ID: {self.geni_profiles[qid]}\n")
                
                f.write("\n" + "-" * 30 + "\n\n")
    
    def update_gedcom(self) -> None:
        """Update GEDCOM file with proper names and Geni profile information"""
        logger.info("Updating GEDCOM file...")
        
        # Read the original file
        with open(self.gedcom_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Process updates
        for individual in self.individuals_with_qid_names:
            # Update name if it's a Q-ID name
            if individual['has_qid_name']:
                qid = individual['qid']
                if qid in self.wikidata_labels:
                    english_name = self.wikidata_labels[qid]['english_name']
                    name_parts = english_name.split(' ', 1)
                    given_name = name_parts[0]
                    surname = name_parts[1] if len(name_parts) > 1 else ""
                    
                    # Update the NAME line
                    lines[individual['name_line']] = f"1 NAME {given_name} /{surname}/\n"
                    
                    # Find and update GIVN line if it exists
                    for j in range(individual['name_line'] + 1, individual['line_end'] + 1):
                        if lines[j].strip().startswith('2 GIVN '):
                            lines[j] = f"2 GIVN {given_name}\n"
                            break
            
            # Update REFN to include geni: prefix and add Geni profile to notes
            if individual['refn'] and individual['refn'] in self.geni_profiles:
                geni_id = self.geni_profiles[individual['refn']]
                
                # Update REFN line
                lines[individual['refn_line']] = f"1 REFN geni:{geni_id}\n"
                
                # Find NOTE line with wikidata URL and add Geni profile
                for j in range(individual['line_start'], individual['line_end'] + 1):
                    if lines[j].strip().startswith('1 NOTE https://www.wikidata.org/wiki/'):
                        # Add Geni profile URL after wikidata URL
                        original_note = lines[j].strip()
                        geni_url = f"https://www.geni.com/people/{geni_id}"
                        lines[j] = f"{original_note}\n2 CONT {geni_url}\n"
                        break
        
        # Write updated GEDCOM
        backup_file = self.gedcom_file.replace('.ged', '_backup.ged')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        with open(self.gedcom_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        logger.info(f"GEDCOM updated. Backup saved as: {backup_file}")
    
    def run(self) -> None:
        """Run the complete processing pipeline"""
        logger.info("Starting Wikidata GEDCOM processing...")
        
        # Load any existing progress
        self._load_progress()
        
        self.parse_gedcom()
        
        # Only fetch labels for Q-IDs we don't have yet
        missing_qids = self.q_ids - set(self.wikidata_labels.keys())
        if missing_qids:
            logger.info(f"Fetching data for {len(missing_qids)} missing Q-IDs")
            # Temporarily replace q_ids with missing ones
            original_qids = self.q_ids
            self.q_ids = missing_qids
            self.fetch_wikidata_labels()
            self.q_ids = original_qids
        else:
            logger.info("All Q-IDs already processed")
        
        self.generate_labels_report()
        self.update_gedcom()
        
        logger.info("Processing completed!")
        logger.info(f"- Processed {len(self.q_ids)} Q-IDs")
        logger.info(f"- Found {len(self.geni_profiles)} Geni profiles")
        logger.info(f"- Updated {len(self.individuals_with_qid_names)} individuals")
        logger.info("- Labels report saved as: wikidata_labels_report.txt")

if __name__ == "__main__":
    processor = WikidataGedcomProcessor("wikidata_combined.ged")
    processor.run()