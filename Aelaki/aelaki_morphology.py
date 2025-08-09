#!/usr/bin/env python3
"""
Aelaki Morphological Processor
Basic implementation of the four core morphological operations on triconsonantal roots
"""

import re
from typing import Tuple, Optional

class AelakiMorphology:
    """Handles basic Aelaki morphological transformations"""
    
    # Vowel mappings for umlaut (fronting)
    UMLAUT_MAP = {
        'a': 'æ',
        'o': 'œ', 
        'u': 'ü',
        'i': 'i',  # already front
        'e': 'e',  # already front
        'æ': 'æ',  # already front
        'œ': 'œ',  # already front
        'ü': 'ü'   # already front
    }
    
    def __init__(self):
        pass
    
    def parse_root(self, word: str) -> Optional[Tuple[str, str, str, str, str]]:
        """
        Parse a triconsonantal root in the form C₁V₁C₂V₂C₃
        Returns (C1, V1, C2, V2, C3) or None if invalid
        """
        # Pattern for triconsonantal root: consonant-vowel-consonant-vowel-consonant
        pattern = r'^([bcdfghjklmnpqrstvwxyz])([aeiouæœü])([bcdfghjklmnpqrstvwxyz])([aeiouæœü])([bcdfghjklmnpqrstvwxyz])$'
        match = re.match(pattern, word.lower())
        
        if match:
            return match.groups()
        return None
    
    def base_form(self, c1: str, v1: str, c2: str, v2: str, c3: str) -> str:
        """Return the base form (no change needed, just reconstruction)"""
        return f"{c1}{v1}{c2}{v2}{c3}"
    
    def reduplicate(self, c1: str, v1: str, c2: str, v2: str, c3: str) -> str:
        """Apply reduplication: C₁V₁C₂V₂C₃ → C₁V₁C₂C₂V₂C₃"""
        return f"{c1}{v1}{c2}{c2}{v2}{c3}"
    
    def umlaut(self, c1: str, v1: str, c2: str, v2: str, c3: str) -> str:
        """Apply umlaut (fronting): front both vowels"""
        front_v1 = self.UMLAUT_MAP.get(v1, v1)
        front_v2 = self.UMLAUT_MAP.get(v2, v2)
        return f"{c1}{front_v1}{c2}{front_v2}{c3}"
    
    def zero_infix(self, c1: str, v1: str, c2: str, v2: str, c3: str) -> str:
        """Apply zero infix: C₁V₁C₂V₂C₃ → C₁V₁fC₂V₂C₃"""
        return f"{c1}{v1}f{c2}{v2}{c3}"
    
    def generate_all_forms(self, root: str) -> dict:
        """Generate all four basic forms from a root"""
        parsed = self.parse_root(root)
        if not parsed:
            return {"error": f"Invalid triconsonantal root: {root}"}
        
        c1, v1, c2, v2, c3 = parsed
        
        return {
            "base": self.base_form(c1, v1, c2, v2, c3),
            "reduplication": self.reduplicate(c1, v1, c2, v2, c3), 
            "umlaut": self.umlaut(c1, v1, c2, v2, c3),
            "zero_infix": self.zero_infix(c1, v1, c2, v2, c3)
        }


def main():
    """Test the morphological processor with documented examples"""
    morph = AelakiMorphology()
    
    # Test cases from documentation
    test_roots = [
        "dapaz",  # shoot at
        "goran"   # bright
    ]
    
    print("Aelaki Morphological Processor Test")
    print("=" * 40)
    
    for root in test_roots:
        print(f"\nRoot: {root}")
        forms = morph.generate_all_forms(root)
        
        if "error" in forms:
            print(f"Error: {forms['error']}")
            continue
            
        print(f"  Base:         {forms['base']}")
        print(f"  Reduplication: {forms['reduplication']}")
        print(f"  Umlaut:       {forms['umlaut']}")
        print(f"  Zero-infix:   {forms['zero_infix']}")
        
        # Show meanings based on documentation
        if root == "dapaz":
            print("  Meanings:")
            print(f"    {forms['base']}: shot at (once, success not implied)")
            print(f"    {forms['reduplication']}: shooting at (ongoing)")
            print(f"    {forms['umlaut']}: shot (single hit achieved)")
            print(f"    {forms['zero_infix']}: did not shoot / no shots fired")
        elif root == "goran":
            print("  Meanings:")
            print(f"    {forms['base']}: bright")
            print(f"    {forms['reduplication']}: brighter")
            print(f"    {forms['umlaut']}: brightest")
            print(f"    {forms['zero_infix']}: not bright / dull")

if __name__ == "__main__":
    main()