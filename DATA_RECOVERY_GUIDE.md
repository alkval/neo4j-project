# Neo4j Data Recovery & Sync Guide

## 🚨 Problem: Missing Nodes

**Why this happens:**
1. **Database corruption** - Config changes or unexpected shutdowns can corrupt Neo4j data
2. **Local data** - Docker volumes are machine-specific; data doesn't sync between computers
3. **Container resets** - Sometimes containers reset to fresh state

## 🔧 Solutions

### **Option 1: Try Recovery (if you have recent backups)**

```bash
# List available backups
./manage_data.sh restore

# Restore from a specific backup
./manage_data.sh restore neo4j_backup_20250706_120000
```

### **Option 2: Fresh Start + Re-import Data**

```bash
# Start with fresh database
./manage_data.sh fresh

# Import your data using your application's import scripts
# (You'll need to re-run whatever process you used to load data initially)
```

### **Option 3: Sync Between Machines**

#### **From Machine A (export data):**
```bash
# Export data to transferable file
./manage_data.sh export

# This creates: exports/neo4j_export_YYYYMMDD_HHMMSS.dump
# Transfer this file to your other machine (USB, cloud, etc.)
```

#### **On Machine B (import data):**
```bash
# Copy the .dump file to your project directory
# Then import it:
./manage_data.sh import path/to/neo4j_export_YYYYMMDD_HHMMSS.dump
```

## 🛡️ Prevention

### **1. Regular Backups**
```bash
# Create backup before major changes
./manage_data.sh backup

# Set up automated backups (add to cron):
# 0 2 * * * cd /path/to/your/project && ./manage_data.sh backup
```

### **2. Data Syncing Between Machines**

#### **Option A: Cloud Storage Sync**
1. Export data: `./manage_data.sh export`
2. Upload .dump file to Google Drive/Dropbox/etc.
3. Download on other machine and import

#### **Option B: Git LFS (for smaller datasets)**
```bash
# Install Git LFS
git lfs install

# Track dump files
git lfs track "*.dump"
git add .gitattributes

# Add exports to git
git add exports/
git commit -m "Add database export"
git push

# On other machine:
git pull
./manage_data.sh import exports/latest_export.dump
```

### **3. Database Health Monitoring**

```bash
# Check database status
docker exec neo4j-ownership cypher-shell -u neo4j -p ownership123 "CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store file sizes')"

# Check if database is accessible
docker exec neo4j-ownership cypher-shell -u neo4j -p ownership123 "MATCH (n) RETURN count(n) as total_nodes"
```

## 🔍 Troubleshooting

### **Database Won't Start**
```bash
# Check logs
docker logs neo4j-ownership

# Check if it's a permission issue
sudo chown -R $USER:$USER ./data

# Try fresh start
./manage_data.sh fresh
```

### **Data Corruption**
```bash
# Try restoring from backup
./manage_data.sh restore [backup_name]

# If no backups work, fresh start + re-import
./manage_data.sh fresh
```

### **Cross-Machine Sync Issues**
- **Problem**: Docker volumes are local to each machine
- **Solution**: Use export/import process for syncing
- **Automation**: Set up scripts to auto-export on one machine and import on others

## 📝 Best Practices

1. **Backup before changes**: Always backup before config changes
2. **Regular exports**: Export data weekly for transfer capability
3. **Document data sources**: Keep notes on how you originally loaded data
4. **Test recovery**: Periodically test backup/restore process
5. **Version control exports**: Keep recent exports in version control (Git LFS)

## 🚀 Quick Commands

```bash
# Emergency: Start fresh and working
./manage_data.sh fresh

# Create backup now
./manage_data.sh backup

# Export for transfer
./manage_data.sh export

# Check if database is working
docker exec neo4j-ownership cypher-shell -u neo4j -p ownership123 "MATCH (n) RETURN count(n)"
```
