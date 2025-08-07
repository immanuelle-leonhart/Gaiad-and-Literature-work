#!/usr/bin/env python3
"""
Comprehensive GEDCOM Match Logger
Compares individuals and their complete family context for manual review
"""

import logging
import re
from typing import Dict, List, Set, Optional, Tuple
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveMatchLogger:
    def __init__(self):
        self.file1_individuals = {}  # id -> individual_data
        self.file2_individuals = {}
        self.file1_families = {}     # family_id -> family_data  
        self.file2_families = {}
        
    def parse_gedcom(self, filename: str, is_file1: bool = True):
        """Parse GEDCOM file completely"""
        individuals = self.file1_individuals if is_file1 else self.file2_individuals
        families = self.file1_families if is_file1 else self.file2_families
        
        current_record = None
        current_id = None
        current_content = []
        
        logger.info(f"Parsing {filename}")
        
        with open(filename, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line in f:
                line = line.rstrip()
                if not line:
                    continue
                    
                parts = line.split(' ', 2)
                if len(parts) < 2:
                    current_content.append(line)
                    continue
                
                try:
                    level = int(parts[0])
                except ValueError:
                    current_content.append(line)
                    continue
                    
                # Handle record start
                if level == 0:
                    # Save previous record
                    if current_record and current_id and current_content:
                        if current_record == 'INDI':
                            individuals[current_id] = self.parse_individual(current_content)
                        elif current_record == 'FAM':
                            families[current_id] = self.parse_family(current_content)
                    
                    # Start new record
                    if parts[1].startswith('@') and len(parts) > 2:
                        current_id = parts[1][1:-1]
                        current_record = parts[2]
                        current_content = [line]
                    else:
                        current_record = None
                        current_content = [line]
                else:
                    current_content.append(line)
            
            # Save last record
            if current_record and current_id and current_content:
                if current_record == 'INDI':
                    individuals[current_id] = self.parse_individual(current_content)
                elif current_record == 'FAM':
                    families[current_id] = self.parse_family(current_content)
                    
        logger.info(f"Parsed {len(individuals)} individuals, {len(families)} families")
        
    def parse_individual(self, content_lines: List[str]) -> Dict:
        """Parse individual record with full details"""
        individual = {
            'id': '',
            'names': [],
            'geni_refs': [],
            'wikidata_refs': [],
            'other_refs': [],
            'families_as_spouse': [],  # FAMS
            'families_as_child': [],   # FAMC
            'birth_date': '',
            'death_date': '',
            'gender': '',
            'notes': []
        }
        
        for line in content_lines:
            if line.startswith('0 @'):
                individual['id'] = line.split('@')[1]
            elif line.startswith('1 NAME '):
                name_value = line[7:].strip()
                individual['names'].append(name_value)
            elif line.startswith('1 SEX '):
                individual['gender'] = line[6:].strip()
            elif line.startswith('1 REFN '):
                refn_value = line[7:].strip()
                if refn_value.startswith('geni:'):
                    individual['geni_refs'].append(refn_value.replace('geni:', ''))
                else:
                    individual['other_refs'].append(refn_value)
            elif line.startswith('1 FAMS @'):
                family_id = line.split('@')[1]
                individual['families_as_spouse'].append(family_id)
            elif line.startswith('1 FAMC @'):
                family_id = line.split('@')[1]
                individual['families_as_child'].append(family_id)
            elif line.startswith('1 BIRT'):
                # Look for date in next lines (simplified)
                pass
            elif line.startswith('1 DEAT'):
                # Look for date in next lines (simplified)
                pass
            elif line.startswith('1 NOTE '):
                note_value = line[7:].strip()
                individual['notes'].append(note_value)
                # Extract Wikidata from notes
                wikidata_match = re.search(r'wikidata\.org/wiki/(Q\d+)', note_value)
                if wikidata_match:
                    individual['wikidata_refs'].append(wikidata_match.group(1))
                # Extract Geni from notes
                geni_match = re.search(r'geni\.com/people/[^/\s]+/(\d+)', note_value)
                if geni_match:
                    individual['geni_refs'].append(geni_match.group(1))
            elif 'wikidata.org/wiki/' in line:
                wikidata_match = re.search(r'wikidata\.org/wiki/(Q\d+)', line)
                if wikidata_match:
                    individual['wikidata_refs'].append(wikidata_match.group(1))
                    
        return individual
        
    def parse_family(self, content_lines: List[str]) -> Dict:
        """Parse family record"""
        family = {
            'id': '',
            'husband_id': '',
            'wife_id': '',
            'children': []
        }
        
        for line in content_lines:
            if line.startswith('0 @'):
                family['id'] = line.split('@')[1]
            elif line.startswith('1 HUSB @'):
                family['husband_id'] = line.split('@')[1]
            elif line.startswith('1 WIFE @'):
                family['wife_id'] = line.split('@')[1]
            elif line.startswith('1 CHIL @'):
                child_id = line.split('@')[1]
                family['children'].append(child_id)
                
        return family
        
    def get_family_context(self, individual: Dict, families: Dict, individuals: Dict) -> Dict:
        """Get complete family context for an individual"""
        context = {
            'spouses': [],
            'children': [],
            'parents': [],
            'siblings': []
        }
        
        # Get spouses and children from families where this person is a spouse
        for family_id in individual['families_as_spouse']:
            if family_id in families:
                family = families[family_id]
                
                # Find spouse
                if family['husband_id'] == individual['id'] and family['wife_id']:
                    if family['wife_id'] in individuals:
                        spouse = individuals[family['wife_id']]
                        context['spouses'].append((family['wife_id'], spouse['names'][0] if spouse['names'] else 'NO NAME'))
                elif family['wife_id'] == individual['id'] and family['husband_id']:
                    if family['husband_id'] in individuals:
                        spouse = individuals[family['husband_id']]
                        context['spouses'].append((family['husband_id'], spouse['names'][0] if spouse['names'] else 'NO NAME'))
                
                # Get children
                for child_id in family['children']:
                    if child_id in individuals:
                        child = individuals[child_id]
                        context['children'].append((child_id, child['names'][0] if child['names'] else 'NO NAME'))
        
        # Get parents and siblings from families where this person is a child
        for family_id in individual['families_as_child']:
            if family_id in families:
                family = families[family_id]
                
                # Get parents
                if family['husband_id'] and family['husband_id'] in individuals:
                    parent = individuals[family['husband_id']]
                    context['parents'].append((family['husband_id'], parent['names'][0] if parent['names'] else 'NO NAME', 'Father'))
                if family['wife_id'] and family['wife_id'] in individuals:
                    parent = individuals[family['wife_id']]
                    context['parents'].append((family['wife_id'], parent['names'][0] if parent['names'] else 'NO NAME', 'Mother'))
                
                # Get siblings
                for sibling_id in family['children']:
                    if sibling_id != individual['id'] and sibling_id in individuals:
                        sibling = individuals[sibling_id]
                        context['siblings'].append((sibling_id, sibling['names'][0] if sibling['names'] else 'NO NAME'))
        
        return context
        
    def calculate_family_similarity(self, context1: Dict, context2: Dict) -> Tuple[float, str]:
        """Calculate similarity score based on family relationships"""
        score = 0.0
        reasons = []
        
        # Compare spouse names
        spouse_matches = 0
        for spouse1_id, spouse1_name in context1['spouses']:
            for spouse2_id, spouse2_name in context2['spouses']:
                name_sim = SequenceMatcher(None, spouse1_name.lower(), spouse2_name.lower()).ratio()
                if name_sim > 0.8:
                    spouse_matches += 1
                    reasons.append(f"Spouse match: '{spouse1_name}' ~ '{spouse2_name}' ({name_sim:.2f})")
        
        if context1['spouses'] and context2['spouses']:
            score += (spouse_matches / max(len(context1['spouses']), len(context2['spouses']))) * 0.4
        
        # Compare children names
        child_matches = 0
        for child1_id, child1_name in context1['children']:
            for child2_id, child2_name in context2['children']:
                name_sim = SequenceMatcher(None, child1_name.lower(), child2_name.lower()).ratio()
                if name_sim > 0.8:
                    child_matches += 1
                    reasons.append(f"Child match: '{child1_name}' ~ '{child2_name}' ({name_sim:.2f})")
        
        if context1['children'] and context2['children']:
            score += (child_matches / max(len(context1['children']), len(context2['children']))) * 0.3
        
        # Compare parent names
        parent_matches = 0
        for parent1_id, parent1_name, parent1_role in context1['parents']:
            for parent2_id, parent2_name, parent2_role in context2['parents']:
                if parent1_role == parent2_role:  # Same role (father/mother)
                    name_sim = SequenceMatcher(None, parent1_name.lower(), parent2_name.lower()).ratio()
                    if name_sim > 0.8:
                        parent_matches += 1
                        reasons.append(f"Parent match ({parent1_role}): '{parent1_name}' ~ '{parent2_name}' ({name_sim:.2f})")
        
        if context1['parents'] and context2['parents']:
            score += (parent_matches / max(len(context1['parents']), len(context2['parents']))) * 0.3
        
        return score, '; '.join(reasons)
        
    def find_matches_with_context(self, min_score: float = 0.1):
        """Find matches considering full family context"""
        logger.info("Finding matches with full family context...")
        
        matches = []
        processed = 0
        
        for file2_id, file2_individual in self.file2_individuals.items():
            processed += 1
            if processed % 1000 == 0:
                logger.info(f"Processed {processed}/{len(self.file2_individuals)} individuals...")
                
            # Get family context for file2 individual
            context2 = self.get_family_context(file2_individual, self.file2_families, self.file2_individuals)
            
            # Check for exact reference matches first
            for file1_id, file1_individual in self.file1_individuals.items():
                score = 0.0
                reasons = []
                
                # Perfect match: same Geni ID
                for geni_id in file2_individual['geni_refs']:
                    if geni_id in file1_individual['geni_refs']:
                        score = 1.0
                        reasons.append(f"Same Geni ID: {geni_id}")
                        break
                        
                # Perfect match: same Wikidata ID
                if score < 1.0:
                    for wiki_id in file2_individual['wikidata_refs']:
                        if wiki_id in file1_individual['wikidata_refs']:
                            score = 1.0
                            reasons.append(f"Same Wikidata ID: {wiki_id}")
                            break
                
                # Name similarity
                if score < 1.0:
                    best_name_score = 0.0
                    best_name_pair = ('', '')
                    for name1 in file1_individual['names']:
                        for name2 in file2_individual['names']:
                            name_score = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
                            if name_score > best_name_score:
                                best_name_score = name_score
                                best_name_pair = (name1, name2)
                    
                    if best_name_score > 0.6:  # Lowered threshold
                        score = best_name_score * 0.5  # Names are only part of the score
                        reasons.append(f"Name similarity: '{best_name_pair[0]}' ~ '{best_name_pair[1]}' ({best_name_score:.2f})")
                
                # Family context similarity
                if score > 0.1 or (context2['spouses'] or context2['children'] or context2['parents']):
                    context1 = self.get_family_context(file1_individual, self.file1_families, self.file1_individuals)
                    family_score, family_reasons = self.calculate_family_similarity(context1, context2)
                    
                    if family_score > 0:
                        score += family_score
                        if family_reasons:
                            reasons.append(family_reasons)
                
                # Record significant matches
                if score >= min_score:
                    matches.append({
                        'file1_id': file1_id,
                        'file1_individual': file1_individual,
                        'file1_context': self.get_family_context(file1_individual, self.file1_families, self.file1_individuals),
                        'file2_id': file2_id,
                        'file2_individual': file2_individual,
                        'file2_context': context2,
                        'score': score,
                        'reasons': '; '.join(reasons)
                    })
        
        # Sort by score descending
        matches.sort(key=lambda x: x['score'], reverse=True)
        logger.info(f"Found {len(matches)} potential matches")
        
        return matches
        
    def write_detailed_log(self, matches: List[Dict], output_file: str):
        """Write comprehensive match log for manual review"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Comprehensive GEDCOM Match Analysis\n\n")
            f.write(f"**File 1:** geni_plus_wikidata_cleaned.ged ({len(self.file1_individuals)} individuals)\n")
            f.write(f"**File 2:** gaiad_ftb_export_2.ged ({len(self.file2_individuals)} individuals)\n")
            f.write(f"**Potential matches found:** {len(matches)}\n\n")
            f.write("---\n\n")
            
            for i, match in enumerate(matches):
                f.write(f"## Match #{i+1} - Score: {match['score']:.3f}\n\n")
                f.write(f"**Reasons:** {match['reasons']}\n\n")
                
                # File 1 individual
                f.write(f"### File 1: {match['file1_id']}\n")
                f1_ind = match['file1_individual']
                f.write(f"- **Names:** {', '.join(f1_ind['names']) if f1_ind['names'] else 'None'}\n")
                f.write(f"- **Gender:** {f1_ind['gender']}\n")
                if f1_ind['geni_refs']:
                    f.write(f"- **Geni IDs:** {', '.join(f1_ind['geni_refs'])}\n")
                if f1_ind['wikidata_refs']:
                    f.write(f"- **Wikidata IDs:** {', '.join(f1_ind['wikidata_refs'])}\n")
                
                # File 1 family context
                f1_ctx = match['file1_context']
                if f1_ctx['spouses']:
                    f.write(f"- **Spouses:** {', '.join([f'{name} ({id})' for id, name in f1_ctx['spouses']])}\n")
                if f1_ctx['children']:
                    f.write(f"- **Children:** {', '.join([f'{name} ({id})' for id, name in f1_ctx['children']])}\n")
                if f1_ctx['parents']:
                    f.write(f"- **Parents:** {', '.join([f'{name} ({role}, {id})' for id, name, role in f1_ctx['parents']])}\n")
                if f1_ctx['siblings']:
                    f.write(f"- **Siblings:** {', '.join([f'{name} ({id})' for id, name in f1_ctx['siblings']])}\n")
                
                f.write("\n")
                
                # File 2 individual
                f.write(f"### File 2: {match['file2_id']}\n")
                f2_ind = match['file2_individual']
                f.write(f"- **Names:** {', '.join(f2_ind['names']) if f2_ind['names'] else 'None'}\n")
                f.write(f"- **Gender:** {f2_ind['gender']}\n")
                if f2_ind['geni_refs']:
                    f.write(f"- **Geni IDs:** {', '.join(f2_ind['geni_refs'])}\n")
                if f2_ind['wikidata_refs']:
                    f.write(f"- **Wikidata IDs:** {', '.join(f2_ind['wikidata_refs'])}\n")
                
                # File 2 family context
                f2_ctx = match['file2_context']
                if f2_ctx['spouses']:
                    f.write(f"- **Spouses:** {', '.join([f'{name} ({id})' for id, name in f2_ctx['spouses']])}\n")
                if f2_ctx['children']:
                    f.write(f"- **Children:** {', '.join([f'{name} ({id})' for id, name in f2_ctx['children']])}\n")
                if f2_ctx['parents']:
                    f.write(f"- **Parents:** {', '.join([f'{name} ({role}, {id})' for id, name, role in f2_ctx['parents']])}\n")
                if f2_ctx['siblings']:
                    f.write(f"- **Siblings:** {', '.join([f'{name} ({id})' for id, name in f2_ctx['siblings']])}\n")
                
                f.write("\n---\n\n")
                
        logger.info(f"Detailed match log written: {output_file}")

def main():
    matcher = ComprehensiveMatchLogger()
    
    # Parse both files
    matcher.parse_gedcom("new_gedcoms/geni_plus_wikidata_cleaned.ged", is_file1=True)
    matcher.parse_gedcom("new_gedcoms/gaiad_ftb_export_2.ged", is_file1=False)
    
    # Find matches with full context
    matches = matcher.find_matches_with_context(min_score=0.2)
    
    # Write detailed log
    matcher.write_detailed_log(matches, "comprehensive_match_analysis.md")
    
    print(f"Analysis complete! Found {len(matches)} potential matches.")
    print("Review the file 'comprehensive_match_analysis.md' for detailed analysis.")

if __name__ == "__main__":
    main()