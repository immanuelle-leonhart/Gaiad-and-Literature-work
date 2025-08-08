#!/usr/bin/env python3
"""
Wikidata GEDCOM Checker
Extracts names from GEDCOM files and checks for Wikidata entries with throttling.
Outputs results to CSV with English labels if available.
"""

import os
import re
import csv
import time
import requests
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GedcomParser:
    """Parse GEDCOM files to extract individual names."""
    
    def __init__(self):
        self.individuals = []
    
    def parse_gedcom_file(self, filepath: str) -> List[Dict[str, str]]:
        """Parse a single GEDCOM file and extract individual names."""
        individuals = []
        current_individual = None
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for line in lines:
                line = line.strip()
                
                # Start of new individual record
                if re.match(r'^\d+\s+@I\d+@\s+INDI', line):
                    if current_individual:
                        individuals.append(current_individual)
                    current_individual = {'id': '', 'given': '', 'surname': '', 'full_name': ''}
                    # Extract individual ID
                    match = re.search(r'@(I\d+)@', line)
                    if match:
                        current_individual['id'] = match.group(1)
                
                # Extract names
                elif current_individual and re.match(r'^\d+\s+NAME\s+', line):
                    name_match = re.search(r'NAME\s+(.+)', line)
                    if name_match:
                        name = name_match.group(1).strip()
                        # Parse GEDCOM name format: "Given /Surname/"
                        if '/' in name:
                            parts = name.split('/')
                            if len(parts) >= 2:
                                current_individual['given'] = parts[0].strip()
                                current_individual['surname'] = parts[1].strip()
                                current_individual['full_name'] = f"{current_individual['given']} {current_individual['surname']}".strip()
                        else:
                            current_individual['full_name'] = name
                
                # Extract given name specifically
                elif current_individual and re.match(r'^\d+\s+GIVN\s+', line):
                    givn_match = re.search(r'GIVN\s+(.+)', line)
                    if givn_match:
                        current_individual['given'] = givn_match.group(1).strip()
                
                # Extract surname specifically
                elif current_individual and re.match(r'^\d+\s+SURN\s+', line):
                    surn_match = re.search(r'SURN\s+(.+)', line)
                    if surn_match:
                        current_individual['surname'] = surn_match.group(1).strip()
            
            # Add the last individual
            if current_individual:
                individuals.append(current_individual)
                
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")
            
        return individuals
    
    def parse_all_gedcoms(self, directory: str) -> List[Dict[str, str]]:
        """Parse all GEDCOM files in a directory."""
        all_individuals = []
        gedcom_files = Path(directory).glob('**/*.ged')
        
        for filepath in gedcom_files:
            logger.info(f"Parsing {filepath}")
            individuals = self.parse_gedcom_file(str(filepath))
            for individual in individuals:
                individual['source_file'] = str(filepath.name)
            all_individuals.extend(individuals)
        
        logger.info(f"Total individuals found: {len(all_individuals)}")
        return all_individuals

class WikidataChecker:
    """Check Wikidata for entities matching GEDCOM names."""
    
    def __init__(self, throttle_delay: float = 2.0):
        self.throttle_delay = throttle_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GedcomWikidataChecker/1.0 (https://github.com/user/project) requests/2.31.0'
        })
        self.last_request_time = 0
    
    def throttle(self):
        """Implement throttling between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.throttle_delay:
            sleep_time = self.throttle_delay - time_since_last
            logger.debug(f"Throttling: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def search_wikidata(self, search_term: str, limit: int = 10) -> List[Dict]:
        """Search Wikidata for entities matching the search term."""
        self.throttle()
        
        url = "https://www.wikidata.org/w/api.php"
        params = {
            'action': 'wbsearchentities',
            'search': search_term,
            'language': 'en',
            'format': 'json',
            'limit': limit
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'search' in data:
                return data['search']
            else:
                logger.warning(f"Unexpected response format for '{search_term}': {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for '{search_term}': {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for '{search_term}': {e}")
            return []
    
    def get_entity_details(self, entity_id: str) -> Optional[Dict]:
        """Get detailed information about a Wikidata entity."""
        self.throttle()
        
        url = "https://www.wikidata.org/w/api.php"
        params = {
            'action': 'wbgetentities',
            'ids': entity_id,
            'languages': 'en',
            'format': 'json'
        }
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'entities' in data and entity_id in data['entities']:
                return data['entities'][entity_id]
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for entity '{entity_id}': {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for entity '{entity_id}': {e}")
            return None
    
    def check_individual(self, individual: Dict[str, str]) -> Dict[str, any]:
        """Check if an individual exists in Wikidata."""
        result = {
            'gedcom_id': individual['id'],
            'given_name': individual['given'],
            'surname': individual['surname'],
            'full_name': individual['full_name'],
            'source_file': individual['source_file'],
            'wikidata_found': False,
            'wikidata_id': '',
            'english_label': '',
            'description': '',
            'search_results_count': 0,
            'top_match_score': 0.0
        }
        
        search_terms = []
        if individual['full_name']:
            search_terms.append(individual['full_name'])
        if individual['given'] and individual['surname']:
            search_terms.append(f"{individual['given']} {individual['surname']}")
        if individual['given']:
            search_terms.append(individual['given'])
        
        best_match = None
        best_score = 0.0
        all_results = []
        
        for search_term in search_terms:
            if not search_term.strip():
                continue
                
            logger.info(f"Searching Wikidata for: {search_term}")
            results = self.search_wikidata(search_term)
            all_results.extend(results)
            
            for item in results:
                # Simple scoring based on label match
                label = item.get('label', '')
                description = item.get('description', '')
                
                # Calculate match score
                score = self.calculate_match_score(search_term, label, description)
                
                if score > best_score:
                    best_score = score
                    best_match = item
        
        result['search_results_count'] = len(all_results)
        result['top_match_score'] = best_score
        
        if best_match and best_score > 0.5:  # Threshold for considering a match
            result['wikidata_found'] = True
            result['wikidata_id'] = best_match.get('id', '')
            result['english_label'] = best_match.get('label', '')
            result['description'] = best_match.get('description', '')
        
        return result
    
    def calculate_match_score(self, search_term: str, label: str, description: str) -> float:
        """Calculate a simple match score between search term and Wikidata result."""
        if not label:
            return 0.0
        
        search_lower = search_term.lower().strip()
        label_lower = label.lower().strip()
        
        # Exact match
        if search_lower == label_lower:
            return 1.0
        
        # Partial match
        if search_lower in label_lower or label_lower in search_lower:
            return 0.8
        
        # Word overlap
        search_words = set(search_lower.split())
        label_words = set(label_lower.split())
        
        if search_words and label_words:
            overlap = len(search_words.intersection(label_words))
            union = len(search_words.union(label_words))
            return overlap / union if union > 0 else 0.0
        
        return 0.0

def main():
    """Main function to run the Wikidata checker."""
    # Configuration
    gedcom_directory = "C:/Users/Immanuelle/Documents/Github/Gaiad-Genealogy/new_gedcoms"
    output_file = "wikidata_results.csv"
    throttle_delay = 3.0  # High throttle rate as requested
    
    logger.info("Starting Wikidata GEDCOM checker")
    
    # Parse GEDCOM files
    parser = GedcomParser()
    individuals = parser.parse_all_gedcoms(gedcom_directory)
    
    if not individuals:
        logger.error("No individuals found in GEDCOM files")
        return
    
    # Remove duplicates based on full name
    seen_names = set()
    unique_individuals = []
    for individual in individuals:
        name_key = individual['full_name'].lower().strip()
        if name_key and name_key not in seen_names:
            seen_names.add(name_key)
            unique_individuals.append(individual)
    
    logger.info(f"Unique individuals to check: {len(unique_individuals)}")
    
    # Initialize Wikidata checker
    checker = WikidataChecker(throttle_delay=throttle_delay)
    
    # Process individuals and save results
    results = []
    total = len(unique_individuals)
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'gedcom_id', 'given_name', 'surname', 'full_name', 'source_file',
                'wikidata_found', 'wikidata_id', 'english_label', 'description',
                'search_results_count', 'top_match_score'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, individual in enumerate(unique_individuals, 1):
                logger.info(f"Processing {i}/{total}: {individual['full_name']}")
                
                try:
                    result = checker.check_individual(individual)
                    results.append(result)
                    writer.writerow(result)
                    csvfile.flush()  # Flush after each row to avoid data loss
                    
                except Exception as e:
                    logger.error(f"Error processing individual {individual['full_name']}: {e}")
                    # Write error result
                    error_result = {
                        'gedcom_id': individual['id'],
                        'given_name': individual['given'],
                        'surname': individual['surname'],
                        'full_name': individual['full_name'],
                        'source_file': individual['source_file'],
                        'wikidata_found': False,
                        'wikidata_id': 'ERROR',
                        'english_label': f'Error: {str(e)}',
                        'description': '',
                        'search_results_count': 0,
                        'top_match_score': 0.0
                    }
                    writer.writerow(error_result)
                    csvfile.flush()
    
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    
    # Summary
    found_count = sum(1 for r in results if r['wikidata_found'])
    logger.info(f"Processing complete!")
    logger.info(f"Total processed: {len(results)}")
    logger.info(f"Wikidata matches found: {found_count}")
    logger.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()