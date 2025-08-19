# Wikibase Backup Restoration Instructions

This backup contains a fully working local Wikibase instance with:
- **145,355 Items** (Q1 - Q160000+) with fixed namespaces
- **41 Properties** (P1-P60) properly imported 
- **Complete statements** working correctly
- **Entity imports enabled** for future use

## Backup Contents

- `wikibase-db-backup.tar.gz` - Complete database with all entities and data
- `wikibase-images-backup.tar.gz` - MediaWiki images/uploads volume
- `official-wikibase-compose.yml` - Docker Compose configuration
- `docker-compose.override.yml` - Elasticsearch memory fixes
- `localsettings_addition.php` - Entity import settings

## Restoration Steps

### 1. Stop any existing Wikibase containers
```bash
docker-compose -f official-wikibase-compose.yml down
```

### 2. Remove existing volumes (CAREFUL - this destroys current data)
```bash
docker volume rm gaiad-genealogy_gaiad-genealogy_db-data gaiad-genealogy_mediawiki-data
```

### 3. Restore database volume
```bash
docker volume create gaiad-genealogy_gaiad-genealogy_db-data
docker run --rm -v gaiad-genealogy_gaiad-genealogy_db-data:/data -v "${PWD}":/backup alpine sh -c "cd /data && tar -xzf /backup/wikibase-db-backup.tar.gz"
```

### 4. Restore images volume
```bash
docker volume create gaiad-genealogy_mediawiki-data
docker run --rm -v gaiad-genealogy_mediawiki-data:/data -v "${PWD}":/backup alpine sh -c "cd /data && tar -xzf /backup/wikibase-images-backup.tar.gz"
```

### 5. Start the restored Wikibase
```bash
docker-compose -f official-wikibase-compose.yml up -d
```

### 6. Wait for startup (about 30-60 seconds)
```bash
# Check when ready
curl -I http://localhost:8080
```

## Verification

Once restored, verify the system works:

1. **Check entities**: Visit http://localhost:8080/wiki/Item:Q1
2. **Check properties**: Visit http://localhost:8080/wiki/Property:P39  
3. **Check statements**: Q1000 should show proper "instance of" statements

## Notes

- The system has `allowEntityImport = true` enabled
- Elasticsearch is configured with proper memory settings
- All namespace issues have been fixed
- Properties and items display correctly with statements

## Backup Date
Created: August 19, 2025

## System State
- Items: 145,355 (all accessible via web interface)
- Properties: 41 (all working correctly)
- Database fixer: Completed Q18001-Q160000 range
- Entity statements: Fully functional