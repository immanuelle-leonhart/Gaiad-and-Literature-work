# POST-RESTART TASKS
## Local Wikibase Setup and Data Processing

### CURRENT STATUS
- **XML Export**: Running in background (bash_40) - **WAIT FOR THIS TO COMPLETE**
- **Goal**: Export remote Wikibase → Process locally → Import back
- **Why**: API processing is too slow (2+ days), local processing will be ~1 hour

### STEP 1: VERIFY XML EXPORT COMPLETION
```bash
# Check if export finished
"C:\Users\Immanuelle\AppData\Local\Programs\Python\Python313\python.exe" -c "
import subprocess
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
print('Python processes:', [line for line in result.stdout.split('\n') if 'python' in line.lower()])
"

# Check export files
ls -la evolutionism_export*.xml
```

### STEP 2: START LOCAL WIKIBASE INSTANCE
```bash
# Verify Docker is working after restart
docker --version

# Start Wikibase containers
cd local-wikibase
docker compose up -d

# Wait for containers to start (2-3 minutes)
docker compose ps

# Access points:
# - Wikibase: http://localhost:8181
# - QuickStatements: http://localhost:9191
# - Admin login: admin/admin123
```

### STEP 3: IMPORT XML INTO LOCAL WIKIBASE
```bash
# Copy XML files to Wikibase container
docker compose exec wikibase ls /var/www/html

# Import via maintenance script
docker compose exec wikibase php /var/www/html/maintenance/importDump.php --file-path=/path/to/evolutionism_export.xml

# OR use web interface:
# Go to http://localhost:8181/wiki/Special:Import
# Upload XML files through web interface
```

### STEP 4: RUN COMPREHENSIVE DATABASE FIXER ON LOCAL WIKIBASE
```bash
# Update comprehensive_database_fixer.py to point to localhost:8181
# Change: https://evolutionism.miraheze.org → http://localhost:8181

# Run the fixer on local instance
"C:\Users\Immanuelle\AppData\Local\Programs\Python\Python313\python.exe" gedcom_tools/comprehensive_database_fixer.py 1 160000 Immanuelle admin123
```

### STEP 5: EXPORT PROCESSED DATA
```bash
# Export from local Wikibase back to XML
docker compose exec wikibase php /var/www/html/maintenance/dumpBackup.php --current --output=file:/tmp/processed_export.xml

# Copy export out of container
docker compose cp wikibase:/tmp/processed_export.xml ./processed_evolutionism.xml
```

### STEP 6: IMPORT BACK TO REMOTE WIKIBASE
```bash
# Use MediaWiki import API or Special:Import page
# This will replace all entities with processed versions
```

## FILES CREATED
- `local-wikibase/docker-compose.yml` - Docker setup for local Wikibase
- `gedcom_tools/wiki_xml_exporter.py` - Export from remote (FAILED - too large)
- `gedcom_tools/simple_xml_export.py` - Alternative export via Special:Export
- `gedcom_tools/namespace_checker.py` - Check correct namespaces (860=items, 862=properties)

## CURRENT EXPORT STATUS
- **Running**: `simple_xml_export.py` in bash_40
- **Expected**: Multiple XML files (evolutionism_export_part_1.xml, etc.)
- **Size**: Should be ~100-500MB total for 145K entities

## TROUBLESHOOTING
If XML export fails:
1. Try smaller chunks (reduce chunk_size in simple_xml_export.py)
2. Use database dump approach instead
3. Contact Miraheze admins for direct database access

## BENEFITS OF THIS APPROACH
- ✅ **Fast local processing** (1 hour vs 2+ days)
- ✅ **Proper revision history** (each change creates new revision)
- ✅ **No API rate limits** locally
- ✅ **Atomic operations** (all changes succeed or fail together)
- ✅ **Preserves entity IDs** (Q1 stays Q1, not renumbered)

## NEXT SESSION CHECKLIST
1. [ ] Docker working after restart
2. [ ] XML export completed successfully  
3. [ ] Local Wikibase containers running
4. [ ] XML imported into local Wikibase
5. [ ] Database fixer runs successfully locally
6. [ ] Export back to XML
7. [ ] Import processed XML to remote Wikibase

**IMPORTANT**: Do NOT restart any processes until XML export (bash_40) completes!