#!/usr/bin/env python3
"""
Script to extract all Wikidata information for Q-IDs in the GEDCOM file.
Stores everything in names.json for analysis - does NOT modify the GEDCOM.
"""

import re
import json
import requests
import time
from typing import Dict, List, Set
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WikidataInfoExtractor:
    def __init__(self, gedcom_file: str):
        self.gedcom_file = gedcom_file
        self.wikidata_api = "https://www.wikidata.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'WikidataInfoExtractor/1.0 (genealogy research)'
        })
        
        self.qids: Set[str] = set()
        self.qid_names: Set[str] = set()  # Q-IDs that appear as names
        self.wikidata_info: Dict[str, Dict] = {}
        
    def extract_qids_from_gedcom(self) -> None:
        """Extract all Q-IDs from the GEDCOM file"""
        logger.info("Extracting Q-IDs from GEDCOM...")
        
        with open(self.gedcom_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find Q-IDs in NAME lines (these need proper names)
        name_qids = re.findall(r'1 NAME (Q\d+)', content)
        self.qid_names.update(name_qids)
        
        # Find Q-IDs in REFN lines (these need Geni profile IDs)
        refn_qids = re.findall(r'1 REFN (Q\d+)', content)
        
        # Combine all Q-IDs
        self.qids.update(name_qids)
        self.qids.update(refn_qids)
        
        logger.info(f"Found {len(self.qid_names)} Q-IDs used as names")
        logger.info(f"Found {len(self.qids)} total unique Q-IDs")
    
    def fetch_wikidata_info(self) -> None:
        """Fetch complete Wikidata information for all Q-IDs"""
        logger.info(f"Fetching Wikidata info for {len(self.qids)} Q-IDs...")
        
        qid_list = list(self.qids)
        batch_size = 50
        total_batches = (len(qid_list) + batch_size - 1) // batch_size
        
        for i in range(0, len(qid_list), batch_size):
            batch_num = i // batch_size + 1
            batch = qid_list[i:i + batch_size]
            
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} Q-IDs)")
            self._fetch_batch_info(batch)
            time.sleep(0.5)  # Be respectful to Wikidata API
            
            # Save progress every 50 batches
            if batch_num % 50 == 0:
                self._save_progress()
        
        self._save_progress()  # Final save
    
    def _fetch_batch_info(self, qids: List[str]) -> None:
        """Fetch complete info for a batch of Q-IDs"""
        entities = '|'.join(qids)
        
        params = {
            'action': 'wbgetentities',
            'ids': entities,
            'props': 'labels|descriptions|claims',
            'format': 'json'
        }
        
        try:
            response = self.session.get(self.wikidata_api, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'entities' in data:
                for qid, entity_data in data['entities'].items():
                    if 'missing' not in entity_data:
                        # Extract all labels
                        labels = entity_data.get('labels', {})
                        label_dict = {lang: label['value'] for lang, label in labels.items()}
                        
                        # Extract all descriptions
                        descriptions = entity_data.get('descriptions', {})
                        desc_dict = {lang: desc['value'] for lang, desc in descriptions.items()}
                        
                        # Extract Geni profile ID (P2600)
                        geni_id = None
                        claims = entity_data.get('claims', {})
                        if 'P2600' in claims:
                            for claim in claims['P2600']:
                                if 'mainsnak' in claim and 'datavalue' in claim['mainsnak']:
                                    geni_id = claim['mainsnak']['datavalue']['value']
                                    break
                        
                        # Store complete information
                        self.wikidata_info[qid] = {
                            'labels': label_dict,
                            'descriptions': desc_dict,
                            'geni_profile_id': geni_id,
                            'used_as_name': qid in self.qid_names,
                            'wikidata_url': f"https://www.wikidata.org/wiki/{qid}"
                        }
                        
                    else:
                        logger.warning(f"Entity {qid} not found in Wikidata")
                        self.wikidata_info[qid] = {
                            'labels': {},
                            'descriptions': {},
                            'geni_profile_id': None,
                            'used_as_name': qid in self.qid_names,
                            'wikidata_url': f"https://www.wikidata.org/wiki/{qid}",
                            'missing': True
                        }
                        
        except Exception as e:
            logger.error(f"Error fetching batch {qids}: {e}")
    
    def _save_progress(self) -> None:
        """Save progress to JSON file"""
        with open('names.json', 'w', encoding='utf-8') as f:
            json.dump(self.wikidata_info, f, indent=2, ensure_ascii=False)
        
        processed = len(self.wikidata_info)
        with_geni = sum(1 for info in self.wikidata_info.values() if info.get('geni_profile_id'))
        used_as_names = sum(1 for info in self.wikidata_info.values() if info.get('used_as_name'))
        
        logger.info(f"Progress saved: {processed} Q-IDs processed")
        logger.info(f"  - {used_as_names} used as names (need English names)")
        logger.info(f"  - {with_geni} have Geni profile IDs")
    
    def generate_summary_report(self) -> None:
        """Generate a summary report of what was found"""
        logger.info("Generating summary report...")
        
        with open('wikidata_summary.txt', 'w', encoding='utf-8') as f:
            f.write("WIKIDATA EXTRACTION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            total_qids = len(self.wikidata_info)
            used_as_names = [qid for qid, info in self.wikidata_info.items() if info.get('used_as_name')]
            with_geni = [qid for qid, info in self.wikidata_info.items() if info.get('geni_profile_id')]
            missing = [qid for qid, info in self.wikidata_info.items() if info.get('missing')]
            
            f.write(f"Total Q-IDs processed: {total_qids}\n")
            f.write(f"Q-IDs used as names: {len(used_as_names)}\n")
            f.write(f"Q-IDs with Geni profiles: {len(with_geni)}\n")
            f.write(f"Missing from Wikidata: {len(missing)}\n\n")
            
            # Language statistics
            all_languages = set()
            for info in self.wikidata_info.values():
                all_languages.update(info.get('labels', {}).keys())
            
            f.write(f"Languages found: {len(all_languages)}\n")
            f.write(f"Languages: {', '.join(sorted(all_languages))}\n\n")
            
            # Q-IDs used as names that need English names
            f.write("Q-IDs USED AS NAMES (need proper English names):\n")
            f.write("-" * 30 + "\n")
            for qid in sorted(used_as_names):
                info = self.wikidata_info[qid]
                labels = info.get('labels', {})
                english_desc = info.get('descriptions', {}).get('en', '')
                
                f.write(f"{qid}: ")
                if 'en' in labels:
                    f.write(f"{labels['en']}")
                elif labels:
                    # Show first available label
                    first_lang = list(labels.keys())[0]
                    f.write(f"{labels[first_lang]} ({first_lang})")
                else:
                    f.write("NO LABELS FOUND")
                
                if english_desc:
                    f.write(f" - {english_desc}")
                f.write("\n")
            
            f.write(f"\n\nComplete data saved to: names.json\n")
            f.write("Use this file to create proper English names for the Q-IDs used as names.\n")
    
    def run(self) -> None:
        """Run the complete extraction process"""
        logger.info("Starting Wikidata information extraction...")
        
        self.extract_qids_from_gedcom()
        self.fetch_wikidata_info()
        self.generate_summary_report()
        
        logger.info("Extraction completed!")
        logger.info("- Complete data saved to: names.json")
        logger.info("- Summary report saved to: wikidata_summary.txt")
        logger.info("- Review the data and create proper English names before updating GEDCOM")

if __name__ == "__main__":
    extractor = WikidataInfoExtractor("wikidata_combined.ged")
    extractor.run()