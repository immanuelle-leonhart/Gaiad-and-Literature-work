# Source GEDCOM Files Documentation

## File Structure Overview

This directory contains the source genealogical data files that form the foundation of the Gaiad genealogy project.

## Master Combined File

### `master_combined.ged`
The primary combined genealogy file that merges data from multiple sources:

**Component Sources:**
- **`recovered_gaiad.ged`**: Old recovered Gaiad genealogical data extracted from Family Tree Builder (FTB) files
- **`geni_plus_wikidata_after_merge.ged`**: Combined genealogical data from two major sources:
  - **Geni.com**: Collaborative genealogy platform data
  - **Wikidata**: Structured genealogical information from Wikipedia/Wikidata

**File Purpose:**
This master file represents the comprehensive genealogical dataset before any trimming or filtering operations. It contains the full scope of genealogical relationships spanning from ancient/mythological figures through modern historical persons.

## Individual Source Files

### `recovered_gaiad.ged`
- **Source**: Family Tree Builder (FTB) export
- **Content**: Historical Gaiad project genealogical data that was previously stored in FTB format
- **Purpose**: Preserves legacy genealogical work and connections

### `geni_plus_wikidata_after_merge.ged` 
- **Source**: Combined Geni.com and Wikidata genealogy
- **Content**: Collaborative genealogy data with cross-referenced identifiers
- **Notable Features**: 
  - Contains extensive Jewish genealogy from Geni (particularly 1500s+ records)
  - Includes Wikidata Q-IDs for notable historical figures
  - Preserves records without Wikidata links (considered "notable enough to keep")

### `aster.ged`
- **Source**: Aster-specific genealogical subset
- **Content**: Focused genealogical data related to specific lineages or individuals
- **Purpose**: Specialized subset for particular genealogical research

## Data Processing Notes

- **File Sizes**: These are large files (multi-million lines) not meant for direct text editing
- **Processing**: Use dedicated Python tools in `gedcom_tools/` directory for any manipulation
- **Preservation Rule**: Records from Geni without Wikidata links are considered notable and should be preserved during trimming operations
- **Quality**: Files have undergone date standardization and cleaning processes

## Workflow Integration

These source files serve as input for:
1. Date standardization processes
2. Trimming operations (creating time-period specific subsets)
3. Analysis and validation scripts
4. Export to various genealogy software formats

**⚠️ WARNING**: Do not directly modify these files. Use the specialized tools in `gedcom_tools/` directory for any processing operations.