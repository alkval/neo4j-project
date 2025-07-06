# Test Data Generation - Large Scale Support

This script can generate realistic fake data from thousands to **millions of nodes** for testing the ownership network database.

## 🚀 **Large Scale Generation**

### **Quick Start:**
```bash
# Generate millions of nodes (1M people, 500k companies, 3M relationships)
python3 generate_large_scale_data.py --scale large

# Or choose a pre-defined scale:
python3 generate_large_scale_data.py --scale small    # 10k people, 50k relationships  
python3 generate_large_scale_data.py --scale medium   # 100k people, 500k relationships
python3 generate_large_scale_data.py --scale xlarge   # 5M people, 15M relationships
```

### **Custom Scale:**
```bash
# Custom numbers
python3 generate_large_scale_data.py --people 2000000 --companies 1000000 --ownership 5000000
```

## **Scale Options:**

| Scale | People | Companies | Ownership Rels | Est. Time | Est. Storage |
|-------|--------|-----------|----------------|-----------|--------------|
| small | 10k | 5k | 50k | ~1 min | ~1 GB |
| medium | 100k | 50k | 500k | ~10 min | ~10 GB |
| large | 1M | 500k | 3M | ~60 min | ~50 GB |
| xlarge | 5M | 2M | 15M | ~300 min | ~250 GB |

## What it creates:

- **People** with realistic names, occupations, net worth, contact info
- **Companies** with industries, financials, headquarters info  
- **Ownership relationships** (people owning companies, companies owning other companies)
- **Board positions** (CEO, CTO, Directors, etc.)
- **Business partnerships** between companies
- **Family relationships** between people (sampled for performance)

## **Performance Optimizations:**

- ✅ **Batch Processing** - Processes in 10k batches for memory efficiency
- ✅ **Progress Tracking** - Real-time progress updates
- ✅ **Memory Optimized** - Uses Neo4j memory configuration for large datasets
- ✅ **Constraints & Indexes** - Automatically creates for better query performance
- ✅ **Timing Information** - Shows how long each step takes

## Usage:

```bash
# Make sure Neo4j is running with enough memory
docker-compose up -d

# For small/medium datasets
python3 generate_test_data.py

# For large-scale datasets (millions of nodes)
python3 generate_large_scale_data.py --scale large
```

## Sample queries to explore the data:

### **Large Dataset Queries**
```cypher
// Count nodes by type
MATCH (n) RETURN labels(n)[0] as type, count(n) as count ORDER BY count DESC

// Top ownership concentrations
MATCH (p:Person)-[r:OWNS]->(c:Company) 
RETURN p.name, sum(r.ownership_percentage) as total_ownership 
ORDER BY total_ownership DESC LIMIT 10

// Industry distribution
MATCH (c:Company) 
RETURN c.industry, count(*) as companies 
ORDER BY companies DESC LIMIT 10

// Complex ownership chains (indirect ownership)
MATCH (p:Person)-[:OWNS]->(c1:Company)-[:OWNS]->(c2:Company)
RETURN p.name as person, c1.name as intermediate_company, c2.name as final_company
LIMIT 10
```

### **Performance Testing Queries**
```cypher
// Test index performance - should be fast even with millions of nodes
MATCH (p:Person {name: "John Smith"}) RETURN p LIMIT 1

// Test relationship traversal performance
MATCH (p:Person)-[r:OWNS]->(c:Company) 
WHERE r.ownership_percentage > 20 
RETURN count(*) as large_stakes

// Complex aggregation on large dataset
MATCH (c:Company)<-[r:OWNS]-(owner) 
RETURN c.name, count(owner) as num_owners, avg(r.ownership_percentage) as avg_stake
ORDER BY num_owners DESC LIMIT 10
```

## **System Requirements for Large Scale:**

### **For 1M+ nodes:**
- **RAM**: 16GB+ recommended
- **Storage**: 50GB+ free space
- **CPU**: Multi-core recommended
- **Time**: 1-2 hours for full million-scale generation

### **Docker Configuration:**
The system automatically configures Neo4j with optimized memory settings:
- Page cache: 3GB
- Heap: 4GB  
- Transaction memory: 3GB

## **Customization:**

Edit the constants in the scripts to change:
- Number of people/companies/relationships
- Batch processing size
- Relationship types and properties
- Data generation parameters

## **Backup & Recovery:**

```bash
# Always backup before large operations
./manage_data.sh backup

# Export large datasets for transfer
./manage_data.sh export

# Fresh start if needed
./manage_data.sh fresh
```

## **Troubleshooting Large Scale:**

1. **Memory Issues**: Reduce batch size or scale
2. **Timeout**: Increase Docker memory limits
3. **Slow Performance**: Check system resources
4. **Connection Issues**: Wait longer for Neo4j startup with large configs

The large-scale generation is optimized for production-level testing with millions of nodes! 🚀
