#!/bin/bash

# Neo4j Data Management Script
# Helps with backing up, restoring, and syncing Neo4j data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
BACKUP_DIR="$SCRIPT_DIR/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if containers are running
check_containers() {
    if docker-compose ps | grep -q "Up"; then
        return 0
    else
        return 1
    fi
}

# Create backup
backup_data() {
    print_status "Creating backup..."
    
    if [ ! -d "$DATA_DIR" ]; then
        print_error "No data directory found!"
        exit 1
    fi
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Create timestamped backup
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_name="neo4j_backup_$timestamp"
    backup_path="$BACKUP_DIR/$backup_name"
    
    # Stop containers if running
    if check_containers; then
        print_status "Stopping containers..."
        docker-compose down
        containers_were_running=true
    fi
    
    # Create backup
    cp -r "$DATA_DIR" "$backup_path"
    print_success "Backup created: $backup_path"
    
    # Restart containers if they were running
    if [ "$containers_were_running" = true ]; then
        print_status "Restarting containers..."
        docker-compose up -d
    fi
}

# Restore from backup
restore_data() {
    if [ -z "$1" ]; then
        print_error "Please specify backup name"
        echo "Available backups:"
        ls -la "$BACKUP_DIR" 2>/dev/null | grep neo4j_backup || echo "No backups found"
        exit 1
    fi
    
    backup_path="$BACKUP_DIR/$1"
    
    if [ ! -d "$backup_path" ]; then
        print_error "Backup not found: $backup_path"
        exit 1
    fi
    
    print_warning "This will replace current data with backup: $1"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cancelled"
        exit 0
    fi
    
    # Stop containers
    if check_containers; then
        print_status "Stopping containers..."
        docker-compose down
    fi
    
    # Remove current data and restore backup
    rm -rf "$DATA_DIR"
    cp -r "$backup_path" "$DATA_DIR"
    print_success "Data restored from backup: $1"
    
    # Start containers
    print_status "Starting containers..."
    docker-compose up -d
}

# Export data to Neo4j dump
export_data() {
    if ! check_containers; then
        print_error "Containers are not running. Start them first with: docker-compose up -d"
        exit 1
    fi
    
    print_status "Exporting data to dump file..."
    
    # Create exports directory
    mkdir -p "$SCRIPT_DIR/exports"
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    dump_file="neo4j_export_$timestamp.dump"
    dump_path="$SCRIPT_DIR/exports/$dump_file"
    
    # Export using neo4j-admin dump
    docker exec neo4j-ownership neo4j-admin database dump neo4j --to-path=/var/lib/neo4j/import
    docker cp neo4j-ownership:/var/lib/neo4j/import/neo4j.dump "$dump_path"
    
    print_success "Data exported to: $dump_path"
    print_status "You can transfer this file to other machines"
}

# Import data from Neo4j dump
import_data() {
    if [ -z "$1" ]; then
        print_error "Please specify dump file path"
        echo "Available exports:"
        ls -la "$SCRIPT_DIR/exports" 2>/dev/null | grep .dump || echo "No exports found"
        exit 1
    fi
    
    dump_file="$1"
    
    if [ ! -f "$dump_file" ]; then
        print_error "Dump file not found: $dump_file"
        exit 1
    fi
    
    print_warning "This will replace ALL current data with imported data"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cancelled"
        exit 0
    fi
    
    # Stop containers
    if check_containers; then
        print_status "Stopping containers..."
        docker-compose down
    fi
    
    # Clear current data
    rm -rf "$DATA_DIR"/*
    
    # Start containers with fresh data
    print_status "Starting containers..."
    docker-compose up -d
    
    # Wait for Neo4j to start
    print_status "Waiting for Neo4j to start..."
    sleep 15
    
    # Copy dump file to container and import
    docker cp "$dump_file" neo4j-ownership:/var/lib/neo4j/import/import.dump
    docker exec neo4j-ownership neo4j-admin database load neo4j --from-path=/var/lib/neo4j/import --overwrite-destination
    
    # Restart to apply imported data
    print_status "Restarting containers to apply imported data..."
    docker-compose restart neo4j
    
    print_success "Data imported successfully!"
}

# Fresh start - clear all data
fresh_start() {
    print_warning "This will delete ALL data and start with a fresh database"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cancelled"
        exit 0
    fi
    
    # Stop containers
    if check_containers; then
        print_status "Stopping containers..."
        docker-compose down
    fi
    
    # Clear data
    rm -rf "$DATA_DIR"/*
    mkdir -p "$DATA_DIR"
    
    # Start containers
    print_status "Starting containers with fresh database..."
    docker-compose up -d
    
    print_success "Fresh database started!"
}

# Show help
show_help() {
    echo "Neo4j Data Management Script"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  backup                    Create a backup of current data"
    echo "  restore <backup_name>     Restore data from backup"
    echo "  export                    Export data to .dump file (for transfer)"
    echo "  import <dump_file>        Import data from .dump file"
    echo "  fresh                     Start with fresh/empty database"
    echo "  help                      Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 backup"
    echo "  $0 restore neo4j_backup_20250706_120000"
    echo "  $0 export"
    echo "  $0 import exports/neo4j_export_20250706_120000.dump"
    echo "  $0 fresh"
}

# Main script logic
case "$1" in
    backup)
        backup_data
        ;;
    restore)
        restore_data "$2"
        ;;
    export)
        export_data
        ;;
    import)
        import_data "$2"
        ;;
    fresh)
        fresh_start
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
