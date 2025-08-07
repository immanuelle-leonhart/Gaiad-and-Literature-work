#!/usr/bin/env python3
"""
Interactive GEDCOM Merger with Manual Confirmation
Shows potential matches and lets user approve/reject each one
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
import re
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InteractiveMerger:
    def __init__(self):
        self.file1_individuals = {}  # id -> {names, refns, notes, content}
        self.file2_individuals = {}
        self.file1_families = {}
        self.file2_families = {}
        self.approved_merges = {}  # file2_id -> file1_id
        self.rejected_matches = set()  # (file1_id, file2_id) tuples
        
    def parse_gedcom(self, filename: str, is_file1: bool = True):
        """Parse GEDCOM file and extract individuals with key info"""
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
                        content_text = '\n'.join(current_content)
                        if current_record == 'INDI':
                            individuals[current_id] = self.extract_individual_info(content_text)
                        elif current_record == 'FAM':
                            families[current_id] = content_text
                    
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
                content_text = '\n'.join(current_content)
                if current_record == 'INDI':
                    individuals[current_id] = self.extract_individual_info(content_text)
                elif current_record == 'FAM':
                    families[current_id] = content_text
                    
        logger.info(f"Parsed {len(individuals)} individuals, {len(families)} families from {filename}")
        
    def extract_individual_info(self, content: str) -> Dict:
        """Extract key info from individual record"""
        info = {
            'names': [],
            'geni_refs': [],
            'wikidata_refs': [],
            'other_refs': [],
            'content': content
        }
        
        for line in content.split('\n'):
            if line.startswith('1 NAME '):
                name_value = line[7:].strip()
                info['names'].append(name_value)
            elif line.startswith('1 REFN '):
                refn_value = line[7:].strip()
                if refn_value.startswith('geni:'):
                    info['geni_refs'].append(refn_value.replace('geni:', ''))
                else:
                    info['other_refs'].append(refn_value)
            elif 'wikidata.org/wiki/' in line:
                wikidata_match = re.search(r'wikidata\.org/wiki/(Q\d+)', line)
                if wikidata_match:
                    info['wikidata_refs'].append(wikidata_match.group(1))
            elif 'geni.com/people' in line:
                geni_match = re.search(r'geni\.com/people/[^/\s]+/(\d+)', line)
                if geni_match:
                    info['geni_refs'].append(geni_match.group(1))
                    
        return info
        
    def find_potential_matches(self, file2_id: str) -> List[Tuple[str, str, float]]:
        """Find potential matches for a file2 individual in file1"""
        file2_info = self.file2_individuals[file2_id]
        matches = []
        
        for file1_id, file1_info in self.file1_individuals.items():
            # Skip if already rejected
            if (file1_id, file2_id) in self.rejected_matches:
                continue
                
            score = 0.0
            reason = ""
            
            # Perfect match: same Geni ID
            for geni_id in file2_info['geni_refs']:
                if geni_id in file1_info['geni_refs']:
                    score = 1.0
                    reason = f"Same Geni ID: {geni_id}"
                    break
                    
            # Perfect match: same Wikidata ID
            if score < 1.0:
                for wiki_id in file2_info['wikidata_refs']:
                    if wiki_id in file1_info['wikidata_refs']:
                        score = 1.0
                        reason = f"Same Wikidata ID: {wiki_id}"
                        break
                        
            # Name similarity
            if score < 1.0:
                best_name_score = 0.0
                for name1 in file1_info['names']:
                    for name2 in file2_info['names']:
                        name_score = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
                        if name_score > best_name_score:
                            best_name_score = name_score
                            if name_score >= 0.8:
                                score = name_score
                                reason = f"Similar names: '{name1}' ~ '{name2}' ({name_score:.2f})"
                                
            if score >= 0.8:  # Only show high-confidence matches
                matches.append((file1_id, reason, score))
                
        # Sort by score descending
        matches.sort(key=lambda x: x[2], reverse=True)
        return matches[:5]  # Top 5 matches
        
    def display_individual_info(self, individual_id: str, info: Dict, file_name: str):
        """Display individual information nicely"""
        print(f"\n--- {file_name}: {individual_id} ---")
        print("Names:", ', '.join(info['names']) if info['names'] else "None")
        if info['geni_refs']:
            print("Geni IDs:", ', '.join(info['geni_refs']))
        if info['wikidata_refs']:
            print("Wikidata IDs:", ', '.join(info['wikidata_refs']))
        if info['other_refs']:
            print("Other refs:", ', '.join(info['other_refs'][:3]))  # Show first 3
            
    def interactive_merge_session(self):
        """Run interactive merge session"""
        print("\n" + "="*80)
        print("INTERACTIVE GEDCOM MERGER")
        print("="*80)
        print(f"File 1: {len(self.file1_individuals)} individuals")
        print(f"File 2: {len(self.file2_individuals)} individuals")
        print("\nFor each individual in File 2, I'll show potential matches from File 1.")
        print("You can approve (y), reject (n), or skip (s) each match.")
        print("Press 'q' to quit, 'auto' to auto-approve perfect matches.")
        print("="*80)
        
        auto_approve = False
        processed = 0
        approved_count = 0
        
        for file2_id, file2_info in self.file2_individuals.items():
            processed += 1
            matches = self.find_potential_matches(file2_id)
            
            if not matches:
                continue  # No matches found
                
            # Auto-approve perfect matches if enabled
            if auto_approve and matches[0][2] == 1.0:
                self.approved_merges[file2_id] = matches[0][0]
                approved_count += 1
                print(f"[{processed}/{len(self.file2_individuals)}] AUTO-APPROVED: {matches[0][1]}")
                continue
                
            # Display the candidate and matches
            print(f"\n[{processed}/{len(self.file2_individuals)}] MATCHING CANDIDATE:")
            self.display_individual_info(file2_id, file2_info, "File 2 (Candidate)")
            
            print(f"\nFound {len(matches)} potential matches:")
            for i, (file1_id, reason, score) in enumerate(matches):
                print(f"\n  {i+1}. MATCH SCORE: {score:.2f} - {reason}")
                self.display_individual_info(file1_id, self.file1_individuals[file1_id], "File 1 (Target)")
                
            # Get user decision
            while True:
                choice = input(f"\nApprove match #{1 if matches else 0}? (y/n/s/q/auto): ").lower().strip()
                
                if choice == 'q':
                    print(f"\nQuitting. Processed {processed}/{len(self.file2_individuals)} individuals.")
                    print(f"Approved {approved_count} merges so far.")
                    return
                elif choice == 'auto':
                    auto_approve = True
                    print("Auto-approve mode enabled for perfect matches (score = 1.0)")
                    break
                elif choice == 'y' and matches:
                    self.approved_merges[file2_id] = matches[0][0]
                    approved_count += 1
                    print(f"✓ APPROVED merge: {file2_id} -> {matches[0][0]}")
                    break
                elif choice == 'n' and matches:
                    self.rejected_matches.add((matches[0][0], file2_id))
                    print(f"✗ REJECTED match: {file2_id} ≠ {matches[0][0]}")
                    break
                elif choice == 's':
                    print("⏭ SKIPPED")
                    break
                else:
                    print("Invalid choice. Use y/n/s/q/auto")
                    
        print(f"\n" + "="*80)
        print("MERGE SESSION COMPLETE")
        print(f"Processed: {processed}/{len(self.file2_individuals)} individuals")
        print(f"Approved merges: {approved_count}")
        print(f"Rejected matches: {len(self.rejected_matches)}")
        print("="*80)
        
    def write_merge_report(self, output_file: str):
        """Write detailed merge report"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Interactive Merge Report\n\n")
            f.write(f"**File 1 individuals:** {len(self.file1_individuals)}\n")
            f.write(f"**File 2 individuals:** {len(self.file2_individuals)}\n")
            f.write(f"**Approved merges:** {len(self.approved_merges)}\n")
            f.write(f"**Rejected matches:** {len(self.rejected_matches)}\n\n")
            
            f.write("## Approved Merges\n\n")
            for file2_id, file1_id in self.approved_merges.items():
                file2_names = ', '.join(self.file2_individuals[file2_id]['names'])
                file1_names = ', '.join(self.file1_individuals[file1_id]['names'])
                f.write(f"- **{file2_id}** ({file2_names}) → **{file1_id}** ({file1_names})\n")
                
            f.write("\n## Rejected Matches\n\n")
            for file1_id, file2_id in self.rejected_matches:
                file1_names = ', '.join(self.file1_individuals[file1_id]['names'])
                file2_names = ', '.join(self.file2_individuals[file2_id]['names'])
                f.write(f"- **{file1_id}** ({file1_names}) ≠ **{file2_id}** ({file2_names})\n")
                
        logger.info(f"Merge report written: {output_file}")

def main():
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python interactive_merger.py <file1.ged> <file2.ged>")
        print("Example: python interactive_merger.py geni_sample_1.ged ftb_sample_1.ged")
        sys.exit(1)
        
    file1 = sys.argv[1]
    file2 = sys.argv[2]
    
    merger = InteractiveMerger()
    merger.parse_gedcom(file1, is_file1=True)
    merger.parse_gedcom(file2, is_file1=False)
    
    merger.interactive_merge_session()
    
    # Write report
    report_file = f"merge_report_{file1.replace('.ged', '').replace('/', '_')}_{file2.replace('.ged', '').replace('/', '_')}.md"
    merger.write_merge_report(report_file)

if __name__ == "__main__":
    main()