#!/bin/bash

# Script to clean auto-generated lines from neo4j.conf
# These lines are automatically added by Neo4j Enterprise Edition during container startup

CONFIG_FILE="./conf/neo4j.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Config file not found: $CONFIG_FILE"
    exit 1
fi

echo "🧹 Cleaning auto-generated lines from neo4j.conf..."

# Remove lines that Neo4j auto-generates (advertised addresses)
sed -i '' '/server\.discovery\.advertised_address=/d' "$CONFIG_FILE"
sed -i '' '/server\.cluster\.advertised_address=/d' "$CONFIG_FILE"
sed -i '' '/server\.cluster\.raft\.advertised_address=/d' "$CONFIG_FILE"
sed -i '' '/server\.routing\.advertised_address=/d' "$CONFIG_FILE"

# Remove duplicate/incorrect settings
sed -i '' '/server\.cluster\.system\.database\.mode=/d' "$CONFIG_FILE"
sed -i '' '/server\.cluster\.discovery\.enabled=/d' "$CONFIG_FILE"
sed -i '' '/initial\.server\.mode\.constraint=/d' "$CONFIG_FILE"

# Remove empty lines at the end
sed -i '' -e :a -e '/^\s*$/N' -e '$!ba' -e 's/\n*$//' "$CONFIG_FILE"

echo "✅ Config file cleaned successfully!"
echo "ℹ️  Note: Using Neo4j Community Edition prevents these auto-generated lines."
