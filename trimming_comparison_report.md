# Gaiad GEDCOM Trimming Comparison Report

## Original File Analysis
**Source**: `merged_attempt_cleaned.ged`
- **Total individuals**: 62,294
- **File size**: 97.3 MB (4.0M lines)
- **Time periods**:
  - Medieval High (1000-1200): 6,095 individuals (62.3%)
  - Medieval Late (1200-1500): 2,885 individuals (29.5%)
  - Early Modern (1500-1800): 775 individuals (7.9%)

## Trimming Strategy Results

### 1200 CE Cutoff
**File**: `gaiad_trimmed_1200.ged`
- **Individuals kept**: 58,627
- **Individuals removed**: 3,667
- **File size reduction**: 6.9% → 90.6 MB
- **Strategy**: Keep pre-1200 CE + all GENI identifiers

### 1100 CE Cutoff  
**File**: `gaiad_trimmed_1100.ged`
- **Individuals kept**: 55,402
- **Individuals removed**: 6,892
- **File size reduction**: 13.6% → 84.0 MB
- **Strategy**: Keep pre-1100 CE + all GENI identifiers

### 1000 CE Cutoff
**File**: `gaiad_trimmed_1000.ged`
- **Individuals kept**: 52,613
- **Individuals removed**: 9,681
- **File size reduction**: 20.2% → 77.6 MB
- **Strategy**: Keep pre-1000 CE + all GENI identifiers

## Comparison Summary

| Cutoff Year | Individuals Kept | Reduction % | File Size | Individuals Removed |
|-------------|------------------|-------------|-----------|-------------------|
| **Original** | 62,294 | 0% | 97.3 MB | 0 |
| **1200 CE** | 58,627 | 6.9% | 90.6 MB | 3,667 |
| **1100 CE** | 55,402 | 13.6% | 84.0 MB | 6,892 |
| **1000 CE** | 52,613 | 20.2% | 77.6 MB | 9,681 |

## Key Preservation Principles

All trimmed files preserve:
- ✅ **All pre-cutoff antiquity** (essential for Gaiad mythology)
- ✅ **All GENI-identified individuals** (stable, priority identifiers)
- ✅ **Family relationships** for kept individuals
- ✅ **Core genealogical structure**

## Recommendations

### For Maximum Antiquity Focus
- **1000 CE cutoff**: 20% reduction, focuses on early medieval and ancient lineages
- Best for emphasizing mythological→historical transition

### For Balanced Approach  
- **1100 CE cutoff**: 13.6% reduction, includes High Medieval period
- Preserves Crusades era and early medieval dynasties

### For Conservative Trimming
- **1200 CE cutoff**: 6.9% reduction, minimal impact
- Keeps most medieval content while removing later excess

## File Status
All three trimmed files are now available in:
`C:\Users\Immanuelle\Documents\Github\Gaiad-Genealogy\new_gedcoms\`

- `gaiad_trimmed_1000.ged` (52K individuals, 77.6 MB)
- `gaiad_trimmed_1100.ged` (55K individuals, 84.0 MB) 
- `gaiad_trimmed_1200.ged` (58K individuals, 90.6 MB)

## Next Steps
1. **Test file functionality** in your genealogy software
2. **Verify essential lineages** are preserved
3. **Choose optimal cutoff** based on your Gaiad project needs
4. **Backup chosen file** as new working copy