#!/usr/bin/env python3
"""
Script to ONLY update REFN fields from Q-ID to geni:PROFILE_ID format.
Uses existing names.json data. Does NOT touch NAME fields.
"""

import json
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RefnUpdater:
    def __init__(self, gedcom_file: str, names_json: str):
        self.gedcom_file = gedcom_file
        self.names_json = names_json
        self.wikidata_info = {}
        self.individuals_updated = []
        
    def load_wikidata_info(self) -> None:
        """Load Wikidata info from names.json"""
        logger.info("Loading Wikidata info from names.json...")
        
        try:
            with open(self.names_json, 'r', encoding='utf-8') as f:
                self.wikidata_info = json.load(f)
            
            # Count how many have Geni profile IDs
            with_geni = sum(1 for info in self.wikidata_info.values() 
                          if info.get('geni_profile_id'))
            
            logger.info(f"Loaded info for {len(self.wikidata_info)} Q-IDs")
            logger.info(f"{with_geni} have Geni profile IDs")
            
        except FileNotFoundError:
            logger.error(f"Could not find {self.names_json}")
            raise
        except Exception as e:
            logger.error(f"Error loading {self.names_json}: {e}")
            raise
    
    def update_refn_fields(self) -> None:
        """Update REFN fields in GEDCOM from Q-ID to geni:PROFILE_ID format"""
        logger.info("Updating REFN fields in GEDCOM...")
        
        # Read the file
        with open(self.gedcom_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Create backup
        backup_file = self.gedcom_file.replace('.ged', '_refn_updated_backup.ged')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        logger.info(f"Backup created: {backup_file}")
        
        updates_made = 0
        geni_notes_added = 0
        current_individual = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Start of individual
            if re.match(r'0 @I\d+@ INDI', line):
                current_individual = {
                    'id': re.search(r'@(I\d+)@', line).group(1),
                    'start_line': i,
                    'qid': None,
                    'refn_line': None,
                    'wikidata_note_line': None
                }
            
            # REFN line with Q-ID
            elif current_individual and line.startswith('1 REFN '):
                refn_match = re.search(r'1 REFN (Q\d+)', line)
                if refn_match:
                    qid = refn_match.group(1)
                    current_individual['qid'] = qid
                    current_individual['refn_line'] = i
                    
                    # Check if we have Geni profile ID for this Q-ID
                    if qid in self.wikidata_info and self.wikidata_info[qid].get('geni_profile_id'):
                        geni_id = self.wikidata_info[qid]['geni_profile_id']
                        
                        # Update REFN line
                        lines[i] = f"1 REFN geni:{geni_id}\n"
                        updates_made += 1
                        
                        logger.debug(f"Updated {current_individual['id']}: {qid} -> geni:{geni_id}")
                        current_individual['geni_id'] = geni_id
            
            # NOTE line with Wikidata URL
            elif (current_individual and line.startswith('1 NOTE ') and 
                  'wikidata.org/wiki/' in line):
                current_individual['wikidata_note_line'] = i
            
            # End of individual - add Geni URL if needed
            elif (re.match(r'0 @I\d+@ INDI', line) or i == len(lines) - 1) and current_individual:
                if (current_individual.get('geni_id') and 
                    current_individual.get('wikidata_note_line') is not None):
                    
                    # Add Geni URL as continuation of wikidata note
                    geni_url = f"https://www.geni.com/people/{current_individual['geni_id']}"
                    note_line = current_individual['wikidata_note_line']
                    lines.insert(note_line + 1, f"2 CONT {geni_url}\n")
                    geni_notes_added += 1
                    
                    # Adjust line counter since we inserted a line
                    i += 1
                
                # Reset for next individual (if not at end)
                if i < len(lines) - 1:
                    current_individual = {
                        'id': re.search(r'@(I\d+)@', line).group(1),
                        'start_line': i,
                        'qid': None,
                        'refn_line': None,
                        'wikidata_note_line': None
                    }
                else:
                    current_individual = None
            
            i += 1
        
        # Write updated file
        with open(self.gedcom_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        logger.info("REFN update completed!")
        logger.info(f"- Updated {updates_made} REFN entries to geni:PROFILE_ID format")
        logger.info(f"- Added {geni_notes_added} Geni profile URLs to notes")
        logger.info(f"- Backup saved as: {backup_file}")
        
        # Statistics
        total_qids = sum(1 for info in self.wikidata_info.values())
        with_geni = sum(1 for info in self.wikidata_info.values() 
                       if info.get('geni_profile_id'))
        coverage = (with_geni / total_qids * 100) if total_qids > 0 else 0
        
        logger.info(f"- Coverage: {with_geni}/{total_qids} ({coverage:.1f}%) Q-IDs have Geni profiles")
    
    def run(self) -> None:
        """Run the REFN update process"""
        logger.info("Starting REFN-only update process...")
        
        self.load_wikidata_info()
        self.update_refn_fields()
        
        logger.info("REFN update process completed!")
        logger.info("NAME fields with Q-IDs are unchanged - review names.json for manual processing")

if __name__ == "__main__":
    updater = RefnUpdater("wikidata_combined.ged", "names.json")
    updater.run()