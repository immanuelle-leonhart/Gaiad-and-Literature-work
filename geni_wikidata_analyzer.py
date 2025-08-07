#!/usr/bin/env python3
"""
Geni/Wikidata GEDCOM Analyzer and Cleaner
Analyzes reference coverage and removes unnecessary sources while preserving critical data
"""

import re
import logging
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeniWikidataAnalyzer:
    def __init__(self):
        self.individuals = {}  # individual_id -> individual_data
        self.families = {}     # family_id -> family_data
        self.sources = {}      # source_id -> source_data
        
        # Statistics
        self.stats = {
            'total_individuals': 0,
            'with_geni_refn': 0,
            'with_geni_note': 0,
            'with_wikidata_note': 0,
            'with_any_reference': 0,
            'missing_references': 0,
            'source_citations_removed': 0
        }
        
        self.missing_refs = []  # List of individuals without references
        
    def parse_gedcom(self, filename: str):
        """Parse GEDCOM file and analyze reference coverage"""
        current_record = None
        current_id = None
        current_level = 0
        
        logger.info(f"Parsing GEDCOM file: {filename}")
        
        with open(filename, 'r', encoding='utf-8-sig', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip()
                if not line:
                    continue
                    
                # Parse GEDCOM line
                parts = line.split(' ', 2)
                if len(parts) < 2:
                    continue
                
                try:
                    level = int(parts[0])
                except ValueError:
                    continue
                    
                tag = parts[1] if not parts[1].startswith('@') else (parts[2] if len(parts) > 2 else '')
                value = parts[2] if len(parts) > 2 and not parts[1].startswith('@') else ''
                
                # Handle record start
                if level == 0:
                    if parts[1].startswith('@') and len(parts) > 2:
                        current_id = parts[1][1:-1]  # Remove @ symbols
                        current_level = 0
                        
                        if parts[2] == 'INDI':
                            current_record = {
                                'id': current_id,
                                'names': [],
                                'refns': [],
                                'notes': [],
                                'geni_refns': [],
                                'geni_notes': [],
                                'wikidata_notes': [],
                                'sources': []
                            }
                            self.individuals[current_id] = current_record
                        elif parts[2] == 'FAM':
                            current_record = {'id': current_id}
                            self.families[current_id] = current_record
                        elif parts[2] == 'SOUR':
                            current_record = {'id': current_id}
                            self.sources[current_id] = current_record
                        else:
                            current_record = None
                    continue
                    
                if current_record is None or current_id not in self.individuals:
                    continue
                    
                # Process individual records
                individual = self.individuals[current_id]
                
                if level == 1:
                    if tag == 'NAME':
                        individual['names'].append(value)
                    elif tag == 'REFN':
                        individual['refns'].append(value)
                        if value.startswith('geni:'):
                            individual['geni_refns'].append(value)
                    elif tag == 'NOTE':
                        individual['notes'].append(value)
                        if 'geni.com' in value.lower():
                            individual['geni_notes'].append(value)
                        if 'wikidata.org' in value.lower():
                            individual['wikidata_notes'].append(value)
                    elif tag == 'SOUR':
                        individual['sources'].append(value)
                elif level == 2:
                    if tag == 'CONT' and individual['notes']:
                        # Continuation of last note
                        individual['notes'][-1] += ' ' + value
                        if 'geni.com' in value.lower():
                            if individual['notes'][-1] not in individual['geni_notes']:
                                individual['geni_notes'].append(individual['notes'][-1])
                        if 'wikidata.org' in value.lower():
                            if individual['notes'][-1] not in individual['wikidata_notes']:
                                individual['wikidata_notes'].append(individual['notes'][-1])
                                
        logger.info(f"Parsed {len(self.individuals)} individuals")
        
    def analyze_references(self):
        """Analyze reference coverage across all individuals"""
        logger.info("Analyzing reference coverage...")
        
        self.stats['total_individuals'] = len(self.individuals)
        
        for individual_id, individual in self.individuals.items():
            has_geni_refn = len(individual['geni_refns']) > 0
            has_geni_note = len(individual['geni_notes']) > 0
            has_wikidata_note = len(individual['wikidata_notes']) > 0
            
            if has_geni_refn:
                self.stats['with_geni_refn'] += 1
            if has_geni_note:
                self.stats['with_geni_note'] += 1
            if has_wikidata_note:
                self.stats['with_wikidata_note'] += 1
                
            has_any_ref = has_geni_refn or has_geni_note or has_wikidata_note
            if has_any_ref:
                self.stats['with_any_reference'] += 1
            else:
                self.stats['missing_references'] += 1
                self.missing_refs.append({
                    'id': individual_id,
                    'names': individual['names']
                })
                
        # Log statistics
        logger.info("=== REFERENCE COVERAGE ANALYSIS ===")
        logger.info(f"Total individuals: {self.stats['total_individuals']:,}")
        logger.info(f"With Geni REFN: {self.stats['with_geni_refn']:,} ({self.stats['with_geni_refn']/self.stats['total_individuals']*100:.1f}%)")
        logger.info(f"With Geni in notes: {self.stats['with_geni_note']:,} ({self.stats['with_geni_note']/self.stats['total_individuals']*100:.1f}%)")
        logger.info(f"With Wikidata in notes: {self.stats['with_wikidata_note']:,} ({self.stats['with_wikidata_note']/self.stats['total_individuals']*100:.1f}%)")
        logger.info(f"With ANY reference: {self.stats['with_any_reference']:,} ({self.stats['with_any_reference']/self.stats['total_individuals']*100:.1f}%)")
        logger.info(f"Missing references: {self.stats['missing_references']:,} ({self.stats['missing_references']/self.stats['total_individuals']*100:.1f}%)")
        
        if self.missing_refs:
            logger.warning(f"\n=== INDIVIDUALS WITHOUT REFERENCES ({len(self.missing_refs)} found) ===")
            for i, missing in enumerate(self.missing_refs[:20]):  # Show first 20
                names = ', '.join(missing['names']) if missing['names'] else 'NO NAME'
                logger.warning(f"  {missing['id']}: {names}")
            if len(self.missing_refs) > 20:
                logger.warning(f"  ... and {len(self.missing_refs) - 20} more")
                
    def extract_clean_references(self, individual: Dict) -> Tuple[List[str], List[str]]:
        """Extract clean Geni and Wikidata references from an individual"""
        geni_refs = []
        wikidata_refs = []
        
        # Get Geni references from REFN
        for refn in individual['geni_refns']:
            if refn.startswith('geni:'):
                geni_id = refn.replace('geni:', '')
                geni_refs.append(geni_id)
        
        # Get Geni references from notes
        for note in individual['geni_notes']:
            geni_matches = re.findall(r'geni\.com/people/[^/\s]+/(\d+)', note)
            geni_refs.extend(geni_matches)
            
        # Get Wikidata references from notes
        for note in individual['wikidata_notes']:
            wikidata_matches = re.findall(r'wikidata\.org/wiki/(Q\d+)', note)
            wikidata_refs.extend(wikidata_matches)
            
        # Remove duplicates while preserving order
        seen = set()
        clean_geni = []
        for ref in geni_refs:
            if ref not in seen:
                clean_geni.append(ref)
                seen.add(ref)
                
        seen = set()
        clean_wikidata = []
        for ref in wikidata_refs:
            if ref not in seen:
                clean_wikidata.append(ref)
                seen.add(ref)
                
        return clean_geni, clean_wikidata
        
    def write_cleaned_gedcom(self, input_filename: str, output_filename: str):
        """Write cleaned GEDCOM without source citations but preserving references"""
        logger.info(f"Writing cleaned GEDCOM: {output_filename}")
        
        source_citations_removed = 0
        
        with open(input_filename, 'r', encoding='utf-8-sig', errors='ignore') as infile, \
             open(output_filename, 'w', encoding='utf-8') as outfile:
             
            skip_source_block = False
            current_individual_id = None
            
            for line_num, line in enumerate(infile, 1):
                line = line.rstrip()
                if not line:
                    continue
                    
                # Parse GEDCOM line
                parts = line.split(' ', 2)
                if len(parts) < 2:
                    outfile.write(line + '\n')
                    continue
                
                try:
                    level = int(parts[0])
                except ValueError:
                    outfile.write(line + '\n')
                    continue
                    
                tag = parts[1] if not parts[1].startswith('@') else (parts[2] if len(parts) > 2 else '')
                
                # Track current individual
                if level == 0 and parts[1].startswith('@') and len(parts) > 2:
                    if parts[2] == 'INDI':
                        current_individual_id = parts[1][1:-1]
                    else:
                        current_individual_id = None
                    skip_source_block = False
                    
                # Skip source citations but preserve the line structure
                if tag == 'SOUR' and current_individual_id:
                    # This is a source citation - skip it and subsequent lines
                    skip_source_block = True
                    source_citations_removed += 1
                    continue
                    
                # Skip lines that are part of a source citation block
                if skip_source_block and level > 1:
                    continue
                else:
                    skip_source_block = False
                    
                # Keep all other lines
                outfile.write(line + '\n')
                
        logger.info(f"Removed {source_citations_removed:,} source citations")
        self.stats['source_citations_removed'] = source_citations_removed
        
    def write_reference_report(self, output_filename: str):
        """Write detailed reference report"""
        logger.info(f"Writing reference report: {output_filename}")
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write("# Geni/Wikidata Reference Analysis Report\n\n")
            f.write(f"**Generated:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total individuals:** {self.stats['total_individuals']:,}\n")
            f.write(f"- **With Geni REFN:** {self.stats['with_geni_refn']:,} ({self.stats['with_geni_refn']/self.stats['total_individuals']*100:.1f}%)\n")
            f.write(f"- **With Geni in notes:** {self.stats['with_geni_note']:,} ({self.stats['with_geni_note']/self.stats['total_individuals']*100:.1f}%)\n")
            f.write(f"- **With Wikidata in notes:** {self.stats['with_wikidata_note']:,} ({self.stats['with_wikidata_note']/self.stats['total_individuals']*100:.1f}%)\n")
            f.write(f"- **With ANY reference:** {self.stats['with_any_reference']:,} ({self.stats['with_any_reference']/self.stats['total_individuals']*100:.1f}%)\n")
            f.write(f"- **Missing references:** {self.stats['missing_references']:,} ({self.stats['missing_references']/self.stats['total_individuals']*100:.1f}%)\n")
            f.write(f"- **Source citations removed:** {self.stats.get('source_citations_removed', 0):,}\n\n")
            
            if self.missing_refs:
                f.write(f"## Individuals Without References ({len(self.missing_refs)} total)\n\n")
                for missing in self.missing_refs:
                    names = ', '.join(missing['names']) if missing['names'] else 'NO NAME'
                    f.write(f"- **{missing['id']}:** {names}\n")
                f.write("\n")
                
            f.write("## Sample Reference Extractions\n\n")
            count = 0
            for individual_id, individual in self.individuals.items():
                if count >= 20:  # Show first 20 examples
                    break
                    
                geni_refs, wikidata_refs = self.extract_clean_references(individual)
                if geni_refs or wikidata_refs:
                    names = ', '.join(individual['names']) if individual['names'] else 'NO NAME'
                    f.write(f"### {individual_id}: {names}\n")
                    if geni_refs:
                        f.write(f"- **Geni IDs:** {', '.join(geni_refs)}\n")
                    if wikidata_refs:
                        f.write(f"- **Wikidata IDs:** {', '.join(wikidata_refs)}\n")
                    f.write("\n")
                    count += 1

def main():
    input_file = "new_gedcoms/geni_plus_wikidata_after_merge.ged"
    cleaned_file = "new_gedcoms/geni_plus_wikidata_cleaned.ged"
    report_file = "new_gedcoms/reference_analysis_report.md"
    
    analyzer = GeniWikidataAnalyzer()
    analyzer.parse_gedcom(input_file)
    analyzer.analyze_references()
    analyzer.write_cleaned_gedcom(input_file, cleaned_file)
    analyzer.write_reference_report(report_file)
    
    logger.info("Analysis and cleaning completed!")
    
if __name__ == "__main__":
    main()