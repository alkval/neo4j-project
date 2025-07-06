#!/usr/bin/env python3
"""
Large Scale Neo4j Test Data Generator
Optimized for millions of nodes with configurable scale.
"""

import sys
import argparse
from generate_test_data import Neo4jTestDataGenerator

# Pre-defined scale configurations
SCALE_CONFIGS = {
    'small': {
        'people': 10_000,
        'companies': 5_000,
        'ownership': 50_000,
        'board': 20_000,
        'partnerships': 10_000
    },
    'medium': {
        'people': 100_000,
        'companies': 50_000,
        'ownership': 500_000,
        'board': 200_000,
        'partnerships': 100_000
    },
    'large': {
        'people': 1_000_000,
        'companies': 500_000,
        'ownership': 3_000_000,
        'board': 800_000,
        'partnerships': 300_000
    },
    'xlarge': {
        'people': 5_000_000,
        'companies': 2_000_000,
        'ownership': 15_000_000,
        'board': 3_000_000,
        'partnerships': 1_000_000
    }
}

def main():
    parser = argparse.ArgumentParser(description='Generate large-scale test data for Neo4j')
    parser.add_argument('--scale', choices=['small', 'medium', 'large', 'xlarge'], 
                       default='large', help='Pre-defined scale configuration')
    parser.add_argument('--people', type=int, help='Number of people (overrides scale)')
    parser.add_argument('--companies', type=int, help='Number of companies (overrides scale)')
    parser.add_argument('--ownership', type=int, help='Number of ownership relationships (overrides scale)')
    parser.add_argument('--board', type=int, help='Number of board positions (overrides scale)')
    parser.add_argument('--partnerships', type=int, help='Number of partnerships (overrides scale)')
    parser.add_argument('--batch-size', type=int, default=10_000, help='Batch size for processing')
    
    args = parser.parse_args()
    
    # Get configuration
    config = SCALE_CONFIGS[args.scale].copy()
    
    # Override with custom values if provided
    if args.people: config['people'] = args.people
    if args.companies: config['companies'] = args.companies
    if args.ownership: config['ownership'] = args.ownership
    if args.board: config['board'] = args.board
    if args.partnerships: config['partnerships'] = args.partnerships
    
    print(f"🎯 Selected scale: {args.scale}")
    print(f"📊 Configuration:")
    print(f"   👥 People: {config['people']:,}")
    print(f"   🏢 Companies: {config['companies']:,}")
    print(f"   🤝 Ownership relationships: {config['ownership']:,}")
    print(f"   👔 Board positions: {config['board']:,}")
    print(f"   🤝 Partnerships: {config['partnerships']:,}")
    print(f"   📦 Batch size: {args.batch_size:,}")
    print()
    
    # Calculate estimated time and storage
    total_nodes = config['people'] + config['companies']
    total_relationships = config['ownership'] + config['board'] + config['partnerships']
    estimated_time = (total_nodes + total_relationships) / 50_000  # Rough estimate: 50k items per minute
    estimated_storage = (total_nodes * 0.5 + total_relationships * 0.3) / 1000  # Rough estimate in GB
    
    print(f"⏱️  Estimated time: {estimated_time:.1f} minutes")
    print(f"💾 Estimated storage: {estimated_storage:.1f} GB")
    print()
    
    # Confirm before starting large operations
    if total_nodes > 100_000:
        response = input("⚠️  This will create a large dataset. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    
    # Update the generator class with new configuration
    import generate_test_data as gtd
    gtd.NUM_PEOPLE = config['people']
    gtd.NUM_COMPANIES = config['companies'] 
    gtd.NUM_OWNERSHIP_RELATIONSHIPS = config['ownership']
    gtd.NUM_BOARD_POSITIONS = config['board']
    gtd.NUM_PARTNERSHIPS = config['partnerships']
    gtd.BATCH_SIZE = args.batch_size
    
    try:
        print("🔌 Testing Neo4j connection...")
        generator = Neo4jTestDataGenerator(gtd.NEO4J_URI, gtd.NEO4J_USER, gtd.NEO4J_PASSWORD)
        
        # Test the connection
        with generator.driver.session() as session:
            session.run("RETURN 1")
        print("✅ Connected to Neo4j successfully!")
        
        # Generate data
        generator.generate_all_data()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Neo4j is running: docker-compose up -d")
        print("2. Wait for Neo4j to start (large configs need more time)")
        print("3. Check that your system has enough memory")
        print("4. Consider using a smaller scale first")
        sys.exit(1)
    
    finally:
        generator.close()

if __name__ == "__main__":
    main()
