#!/usr/bin/env python3
"""
Script to update all REFN Q-IDs in wikidata_combined.ged with:
1. Geni.com profile IDs from Wikidata P2600 property
2. Change REFN format from Q-ID to geni:PROFILE_ID
3. Add Geni profile URLs to notes
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

class GeniProfileUpdater:
    def __init__(self, gedcom_file: str):
        self.gedcom_file = gedcom_file
        self.wikidata_api = "https://www.wikidata.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeniProfileUpdater/1.0 (genealogy research)'
        })
        
        # Storage for processed data
        self.individuals_with_refn: List[Dict] = []
        self.qid_to_geni: Dict[str, str] = {}
        self.qid_labels: Dict[str, Dict] = {}
        
    def parse_gedcom_for_refn(self) -> None:
        """Parse GEDCOM file to find all individuals with REFN Q-IDs"""
        logger.info("Parsing GEDCOM for REFN Q-IDs...")
        
        with open(self.gedcom_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        current_individual = None
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Start of individual
            if re.match(r'0 @I\d+@ INDI', line):
                if current_individual and current_individual.get('refn_qid'):
                    self.individuals_with_refn.append(current_individual)
                
                current_individual = {
                    'id': re.search(r'@(I\d+)@', line).group(1),
                    'line_start': i,
                    'refn_qid': None,
                    'refn_line': None,
                    'note_lines': []
                }
            
            # REFN line with Q-ID
            elif current_individual and line.startswith('1 REFN '):
                refn_match = re.search(r'1 REFN (Q\d+)', line)
                if refn_match:
                    current_individual['refn_qid'] = refn_match.group(1)
                    current_individual['refn_line'] = i
            
            # NOTE lines (to find where to add Geni URLs)
            elif current_individual and line.startswith('1 NOTE '):
                current_individual['note_lines'].append(i)
            
            # End of individual (next individual or end of file)
            elif re.match(r'0 @I\d+@ INDI', line) or i == len(lines) - 1:
                if current_individual and current_individual.get('refn_qid'):
                    current_individual['line_end'] = i - 1 if i < len(lines) - 1 else i
                    self.individuals_with_refn.append(current_individual)
                
                if i < len(lines) - 1:
                    current_individual = {
                        'id': re.search(r'@(I\d+)@', line).group(1),
                        'line_start': i,
                        'refn_qid': None,
                        'refn_line': None,
                        'note_lines': []
                    }
                else:
                    current_individual = None
            
            i += 1
        
        # Extract unique Q-IDs
        qids = set(ind['refn_qid'] for ind in self.individuals_with_refn if ind['refn_qid'])
        
        logger.info(f"Found {len(self.individuals_with_refn)} individuals with REFN Q-IDs")
        logger.info(f"Found {len(qids)} unique Q-IDs")
        
        return qids
    
    def fetch_geni_profiles(self, qids: Set[str]) -> None:
        """Fetch Geni profile IDs for all Q-IDs"""
        logger.info(f"Fetching Geni profiles for {len(qids)} Q-IDs...")
        
        qid_list = list(qids)
        batch_size = 50
        total_batches = (len(qid_list) + batch_size - 1) // batch_size
        
        for i in range(0, len(qid_list), batch_size):
            batch_num = i // batch_size + 1
            batch = qid_list[i:i + batch_size]
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} Q-IDs)")
            self._fetch_batch_geni_profiles(batch)
            time.sleep(0.3)  # Be respectful to Wikidata API
            
            # Save progress every 20 batches
            if batch_num % 20 == 0:
                self._save_progress()
        
        self._save_progress()  # Final save
    
    def _fetch_batch_geni_profiles(self, qids: List[str]) -> None:
        """Fetch Geni profile IDs for a batch of Q-IDs"""
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
                        # Extract labels for the report
                        labels = entity_data.get('labels', {})
                        
                        # Try to get English name first, then other languages
                        english_name = labels.get('en', {}).get('value')
                        if not english_name:
                            for lang in ['ru', 'de', 'fr', 'es', 'it', 'hy', 'ar']:
                                if lang in labels:
                                    english_name = labels[lang]['value']
                                    break
                            
                            if not english_name and labels:
                                first_lang = list(labels.keys())[0]
                                english_name = labels[first_lang]['value']
                            
                            if not english_name:
                                english_name = qid
                        
                        self.qid_labels[qid] = {
                            'english_name': english_name,
                            'all_labels': {lang: label['value'] for lang, label in labels.items()}
                        }
                        
                        # Extract Geni profile ID (P2600)
                        claims = entity_data.get('claims', {})
                        if 'P2600' in claims:
                            for claim in claims['P2600']:
                                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                                    geni_id = claim['mainsnak']['datavalue']['value']
                                    self.qid_to_geni[qid] = geni_id
                                    logger.debug(f"Found Geni ID for {qid}: {geni_id}")
                                    break
                    else:
                        logger.warning(f"Entity {qid} not found in Wikidata")
                        
        except Exception as e:
            logger.error(f"Error fetching batch {qids}: {e}")
    
    def _save_progress(self) -> None:
        """Save progress to JSON file"""
        progress_data = {
            'qid_to_geni': self.qid_to_geni,
            'qid_labels': self.qid_labels
        }
        with open('geni_profiles_progress.json', 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Progress saved: {len(self.qid_to_geni)} Geni profiles found")
    
    def _load_progress(self) -> bool:
        """Load progress from JSON file"""
        try:
            with open('geni_profiles_progress.json', 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                self.qid_to_geni = progress_data.get('qid_to_geni', {})
                self.qid_labels = progress_data.get('qid_labels', {})
                logger.info(f"Progress loaded: {len(self.qid_to_geni)} Geni profiles")
                return True
        except FileNotFoundError:
            logger.info("No progress file found, starting fresh")
            return False
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
            return False
    
    def generate_geni_profiles_report(self) -> None:
        """Generate report of all Geni profiles found"""
        logger.info("Generating Geni profiles report...")
        
        with open('geni_profiles_report.txt', 'w', encoding='utf-8') as f:
            f.write("GENI PROFILES REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Statistics
            total_qids = len(set(ind['refn_qid'] for ind in self.individuals_with_refn if ind['refn_qid']))
            geni_found = len(self.qid_to_geni)
            f.write(f"Total Q-IDs processed: {total_qids}\n")
            f.write(f"Geni profiles found: {geni_found}\n")
            f.write(f"Coverage: {(geni_found/total_qids*100):.1f}%\n\n")
            f.write("-" * 50 + "\n\n")
            
            # Q-IDs with Geni profiles
            f.write("Q-IDs WITH GENI PROFILES:\n\n")
            for qid in sorted(self.qid_to_geni.keys()):
                geni_id = self.qid_to_geni[qid]
                name = self.qid_labels.get(qid, {}).get('english_name', qid)
                
                f.write(f"Q-ID: {qid}\n")
                f.write(f"Name: {name}\n")
                f.write(f"Geni Profile ID: {geni_id}\n")
                f.write(f"Geni URL: https://www.geni.com/people/{geni_id}\n")
                f.write("\n" + "-" * 30 + "\n\n")
            
            # Q-IDs without Geni profiles
            f.write("Q-IDs WITHOUT GENI PROFILES:\n\n")
            qids_without_geni = []
            for individual in self.individuals_with_refn:
                if individual['refn_qid'] and individual['refn_qid'] not in self.qid_to_geni:
                    qids_without_geni.append(individual['refn_qid'])
            
            for qid in sorted(set(qids_without_geni)):
                name = self.qid_labels.get(qid, {}).get('english_name', qid)
                f.write(f"Q-ID: {qid} - {name}\n")
            
            if not qids_without_geni:
                f.write("All Q-IDs have Geni profiles!\n")
    
    def update_gedcom_with_geni_profiles(self) -> None:
        """Update GEDCOM file with Geni profile information"""
        logger.info("Updating GEDCOM with Geni profiles...")
        
        # Read the file
        with open(self.gedcom_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Create backup
        backup_file = self.gedcom_file.replace('.ged', '_geni_updated_backup.ged')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        updates_made = 0
        geni_notes_added = 0
        
        for individual in self.individuals_with_refn:
            qid = individual['refn_qid']
            
            if qid in self.qid_to_geni:
                geni_id = self.qid_to_geni[qid]
                
                # Update REFN line
                if individual['refn_line'] < len(lines):
                    old_refn = lines[individual['refn_line']].strip()
                    if f"1 REFN {qid}" in old_refn:
                        lines[individual['refn_line']] = f"1 REFN geni:{geni_id}\n"
                        updates_made += 1
                        logger.debug(f"Updated REFN {qid} -> geni:{geni_id}")
                
                # Add Geni URL to notes (after existing Wikidata URL if present)
                geni_url = f"https://www.geni.com/people/{geni_id}"
                
                # Find wikidata note and add geni URL after it
                for note_line in individual['note_lines']:
                    if note_line < len(lines):
                        note_content = lines[note_line].strip()
                        if 'wikidata.org/wiki/' in note_content:
                            # Add Geni URL as continuation of the note
                            lines.insert(note_line + 1, f"2 CONT {geni_url}\n")
                            geni_notes_added += 1
                            break
        
        # Write updated file
        with open(self.gedcom_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        logger.info(f"GEDCOM updated:")
        logger.info(f"- Updated {updates_made} REFN entries")
        logger.info(f"- Added {geni_notes_added} Geni profile URLs to notes")
        logger.info(f"- Backup saved as: {backup_file}")
    
    def run(self) -> None:
        """Run the complete processing pipeline"""
        logger.info("Starting Geni profile update process...")
        
        # Load any existing progress
        self._load_progress()
        
        # Parse GEDCOM to find REFN Q-IDs
        qids = self.parse_gedcom_for_refn()
        
        # Only fetch profiles for Q-IDs we don't have yet
        missing_qids = qids - set(self.qid_to_geni.keys())
        if missing_qids:
            logger.info(f"Fetching Geni profiles for {len(missing_qids)} missing Q-IDs")
            self.fetch_geni_profiles(missing_qids)
        else:
            logger.info("All Q-IDs already processed")
        
        # Generate report
        self.generate_geni_profiles_report()
        
        # Update GEDCOM file
        self.update_gedcom_with_geni_profiles()
        
        # Final statistics
        total_qids = len(qids)
        geni_found = len(self.qid_to_geni)
        
        logger.info("Processing completed!")
        logger.info(f"- Processed {total_qids} Q-IDs")
        logger.info(f"- Found {geni_found} Geni profiles ({(geni_found/total_qids*100):.1f}% coverage)")
        logger.info("- Report saved as: geni_profiles_report.txt")

if __name__ == "__main__":
    updater = GeniProfileUpdater("wikidata_combined.ged")
    updater.run()