# Running Scripts Status and Restart Documentation

**Created:** 2025-08-15 05:06 UTC  
**Purpose:** Document all 5 currently running scripts for potential restart with proper resumption points

## Script Status Summary

### 1. bash_7: master_relationships_final.py
- **Status:** RUNNING (but experiencing API failures)
- **Purpose:** Add family relationships for all families in master GEDCOM
- **Current Progress:** Processing family @F45621@ (around family 45,621)
- **Issues:** All API calls succeeding now (recovered from earlier JSON decode errors)
- **Success Pattern:** Currently adding spouse and parent-child relationships successfully
- **Restart Point:** Script processes all families, no specific restart needed - rerun from beginning
- **Last Success:** Family @F45621@ relationships added successfully

### 2. bash_13: database_reviewer_from_start.py  
- **Status:** RUNNING (no output captured - silent processing)
- **Purpose:** Review database entities Q1-Q160000
- **Current Progress:** Unknown (no recent output)
- **Issues:** No visible output in recent checks
- **Restart Point:** Rerun from Q1 (or check for checkpoint mechanism in script)

### 3. bash_14: quick_refn_fixer.py
- **Status:** RUNNING (working well)
- **Purpose:** Add REFN properties to individuals from various mapping sources
- **Current Progress:** Processing @I44839@ -> Q109176 (around individual 44,839)
- **Issues:** None - processing geni: REFNs successfully
- **Success Pattern:** Adding REFN properties from geni mapping data
- **Restart Point:** Script processes all mappings, no specific restart needed - rerun from beginning

### 4. bash_21: duplicate_properties_remover.py
- **Status:** RUNNING (working very well)
- **Purpose:** Remove duplicate properties from Q1-Q160000
- **Current Progress:** [2000/160000] entities processed
- **Performance:** 1385 entities with duplicates found, 7060 duplicates removed, only 11 errors
- **Issues:** None - excellent performance
- **Success Pattern:** Systematically removing duplicate claims (P39, P3, P46, P47, P48, P20, P42, etc.)
- **Restart Point:** Modify script to start from Q2001 (last processed was Q2000)

### 5. bash_22: japanese_individuals_repair.py
- **Status:** RUNNING (mostly working, some language errors)
- **Purpose:** Add Sex, Wikidata ID, URL, and multilingual labels/descriptions for Japanese individuals
- **Current Progress:** [5435] Processing @I3344@ -> Q9892 (individual 5,435 of ~24,158)
- **Issues:** Some language code errors ("mul" not recognized, label=description conflicts)
- **Success Pattern:** Adding Sex (P11), Wikidata ID (P44), URL (P45), and importing multilingual data
- **Restart Point:** Script processes all Japanese mappings, no specific restart needed - rerun from beginning

## API Performance Analysis

**Current Load:** 5 scripts running concurrently causing some stress
**Performance Issues:**
- bash_7: Recovered from JSON decode errors, now working
- bash_13: No visible output (potential stall)
- bash_14: Working perfectly
- bash_21: Working perfectly (best performer)
- bash_22: Working well with minor language errors

## Restart Commands

### bash_7 (Master Relationships)
```bash
"C:\Users\Immanuelle\AppData\Local\Programs\Python\Python313\python.exe" gedcom_tools/master_relationships_final.py
```

### bash_13 (Database Reviewer)
```bash
"C:\Users\Immanuelle\AppData\Local\Programs\Python\Python313\python.exe" gedcom_tools/database_reviewer_from_start.py
```

### bash_14 (Quick REFN Fixer)
```bash
"C:\Users\Immanuelle\AppData\Local\Programs\Python\Python313\python.exe" gedcom_tools/quick_refn_fixer.py
```

### bash_21 (Duplicate Properties Remover - MODIFY TO START AT Q2001)
```bash
# NEED TO MODIFY: Change start_qid = 2001 in script before restart
"C:\Users\Immanuelle\AppData\Local\Programs\Python\Python313\python.exe" gedcom_tools/duplicate_properties_remover.py
```

### bash_22 (Japanese Individuals Repair)
```bash
"C:\Users\Immanuelle\AppData\Local\Programs\Python\Python313\python.exe" gedcom_tools/japanese_individuals_repair.py
```

## Recommended Action Plan

1. **Keep bash_22 running** (Japanese repair - user specifically requested)
2. **Kill bash_13** (silent/stalled database reviewer)
3. **Kill bash_7** (master relationships - can restart later)
4. **Kill bash_14** (quick REFN fixer - can restart later)
5. **Kill bash_21** (duplicate remover - but modify to resume from Q2001)

## Priority Order for Restart (when API load reduced)
1. **bash_21** (duplicate_properties_remover.py) - modify to start from Q2001
2. **bash_14** (quick_refn_fixer.py) - excellent performance
3. **bash_7** (master_relationships_final.py) - critical for relationships
4. **bash_13** (database_reviewer_from_start.py) - utility script

## File Modifications Needed Before Restart

### duplicate_properties_remover.py
Change line ~164:
```python
# FROM:
start_qid = 1
# TO:
start_qid = 2001
```

This will resume duplicate removal from where it left off (Q2001) instead of starting over.