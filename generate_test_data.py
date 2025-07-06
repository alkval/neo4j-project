#!/usr/bin/env python3
"""
Neo4j Test Data Generator
Creates realistic fake data for ownership relationships between people and companies.
"""

import random
import sys
from datetime import datetime, timedelta
from neo4j import GraphDatabase
from faker import Faker

# Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "ownership123"

# Data generation settings - Large scale
NUM_PEOPLE = 1_000_000        # 1 million people
NUM_COMPANIES = 500_000       # 500k companies  
NUM_OWNERSHIP_RELATIONSHIPS = 3_000_000  # 3 million relationships
NUM_BOARD_POSITIONS = 800_000  # 800k board positions
NUM_PARTNERSHIPS = 300_000     # 300k partnerships

# Batch processing settings for performance
BATCH_SIZE = 10_000  # Process in batches of 10k for memory efficiency

class Neo4jTestDataGenerator:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.fake = Faker()
        
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear all existing data"""
        with self.driver.session() as session:
            print("🗑️  Clearing existing data...")
            session.run("MATCH (n) DETACH DELETE n")
            print("✅ Database cleared")
    
    def create_constraints(self):
        """Create constraints and indexes for better performance"""
        with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT company_id IF NOT EXISTS FOR (c:Company) REQUIRE c.id IS UNIQUE",
                "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON p.name",
                "CREATE INDEX company_name IF NOT EXISTS FOR (c:Company) ON c.name"
            ]
            
            print("📊 Creating constraints and indexes...")
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    # Constraint might already exist
                    pass
            print("✅ Constraints and indexes created")
    
    def generate_people_batch(self, start_id, batch_size):
        """Generate a batch of fake people"""
        people = []
        
        for i in range(start_id, min(start_id + batch_size, NUM_PEOPLE)):
            person = {
                'id': f"person_{i+1}",
                'name': self.fake.name(),
                'email': self.fake.email(),
                'phone': self.fake.phone_number(),
                'date_of_birth': self.fake.date_of_birth(minimum_age=25, maximum_age=80).isoformat(),
                'nationality': self.fake.country(),
                'net_worth': random.randint(50000, 50000000),
                'occupation': random.choice([
                    'CEO', 'CTO', 'CFO', 'Director', 'Manager', 'Investor', 
                    'Entrepreneur', 'Consultant', 'Lawyer', 'Accountant',
                    'Engineer', 'Doctor', 'Professor', 'Banker'
                ]),
                'city': self.fake.city(),
                'country': self.fake.country()
            }
            people.append(person)
        
        return people
    
    def generate_companies_batch(self, start_id, batch_size):
        """Generate a batch of fake companies"""
        companies = []
        
        company_types = ['Technology', 'Finance', 'Healthcare', 'Energy', 'Retail', 
                        'Manufacturing', 'Real Estate', 'Media', 'Transportation', 'Education']
        
        for i in range(start_id, min(start_id + batch_size, NUM_COMPANIES)):
            company_type = random.choice(company_types)
            company = {
                'id': f"company_{i+1}",
                'name': self.fake.company(),
                'industry': company_type,
                'founded_year': random.randint(1950, 2023),
                'headquarters': f"{self.fake.city()}, {self.fake.country()}",
                'employee_count': random.randint(10, 10000),
                'revenue': random.randint(1000000, 1000000000),
                'market_cap': random.randint(5000000, 500000000),
                'stock_symbol': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=random.randint(3, 5))),
                'website': self.fake.url(),
                'description': f"A leading {company_type.lower()} company providing innovative solutions."
            }
            companies.append(company)
        
        return companies
    
    def insert_people_batched(self):
        """Insert people into Neo4j using batch processing"""
        print(f"� Generating and inserting {NUM_PEOPLE:,} people in batches of {BATCH_SIZE:,}...")
        
        total_inserted = 0
        for start_id in range(0, NUM_PEOPLE, BATCH_SIZE):
            people = self.generate_people_batch(start_id, BATCH_SIZE)
            
            with self.driver.session() as session:
                query = """
                UNWIND $people AS person
                CREATE (p:Person {
                    id: person.id,
                    name: person.name,
                    email: person.email,
                    phone: person.phone,
                    date_of_birth: date(person.date_of_birth),
                    nationality: person.nationality,
                    net_worth: person.net_worth,
                    occupation: person.occupation,
                    city: person.city,
                    country: person.country,
                    created_at: datetime()
                })
                """
                session.run(query, people=people)
            
            total_inserted += len(people)
            progress = (total_inserted / NUM_PEOPLE) * 100
            print(f"   📊 Progress: {total_inserted:,}/{NUM_PEOPLE:,} people ({progress:.1f}%)")
        
        print(f"✅ Inserted {total_inserted:,} people")
    
    def insert_companies_batched(self):
        """Insert companies into Neo4j using batch processing"""
        print(f"🏢 Generating and inserting {NUM_COMPANIES:,} companies in batches of {BATCH_SIZE:,}...")
        
        total_inserted = 0
        for start_id in range(0, NUM_COMPANIES, BATCH_SIZE):
            companies = self.generate_companies_batch(start_id, BATCH_SIZE)
            
            with self.driver.session() as session:
                query = """
                UNWIND $companies AS company
                CREATE (c:Company {
                    id: company.id,
                    name: company.name,
                    industry: company.industry,
                    founded_year: company.founded_year,
                    headquarters: company.headquarters,
                    employee_count: company.employee_count,
                    revenue: company.revenue,
                    market_cap: company.market_cap,
                    stock_symbol: company.stock_symbol,
                    website: company.website,
                    description: company.description,
                    created_at: datetime()
                })
                """
                session.run(query, companies=companies)
            
            total_inserted += len(companies)
            progress = (total_inserted / NUM_COMPANIES) * 100
            print(f"   📊 Progress: {total_inserted:,}/{NUM_COMPANIES:,} companies ({progress:.1f}%)")
        
        print(f"✅ Inserted {total_inserted:,} companies")
    
    def create_ownership_relationships_batched(self):
        """Create ownership relationships in batches"""
        print(f"🤝 Creating {NUM_OWNERSHIP_RELATIONSHIPS:,} ownership relationships in batches...")
        
        total_created = 0
        batch = []
        
        for i in range(NUM_OWNERSHIP_RELATIONSHIPS):
            # Random ownership relationship
            owner_type = random.choice(['person', 'company'])
            
            if owner_type == 'person':
                owner_id = f"person_{random.randint(1, NUM_PEOPLE)}"
            else:
                owner_id = f"company_{random.randint(1, NUM_COMPANIES)}"
            
            owned_id = f"company_{random.randint(1, NUM_COMPANIES)}"
            
            # Avoid self-ownership for companies
            if owner_id == owned_id:
                continue
            
            relationship = {
                'owner_id': owner_id,
                'owned_id': owned_id,
                'owner_type': owner_type,
                'ownership_percentage': round(random.uniform(0.1, 25.0), 2),
                'acquisition_date': self.fake.date_between(start_date='-10y', end_date='today').isoformat(),
                'acquisition_price': random.randint(10000, 10000000),
                'ownership_type': random.choice(['Direct', 'Indirect', 'Beneficial']),
                'voting_rights': random.choice([True, False])
            }
            batch.append(relationship)
            
            # Process batch when it reaches BATCH_SIZE
            if len(batch) >= BATCH_SIZE:
                self._insert_ownership_batch(batch)
                total_created += len(batch)
                progress = (total_created / NUM_OWNERSHIP_RELATIONSHIPS) * 100
                print(f"   📊 Progress: {total_created:,}/{NUM_OWNERSHIP_RELATIONSHIPS:,} relationships ({progress:.1f}%)")
                batch = []
        
        # Process remaining relationships
        if batch:
            self._insert_ownership_batch(batch)
            total_created += len(batch)
        
        print(f"✅ Created {total_created:,} ownership relationships")
    
    def _insert_ownership_batch(self, relationships):
        """Insert a batch of ownership relationships"""
        with self.driver.session() as session:
            # Split into person->company and company->company relationships
            person_rels = [r for r in relationships if r['owner_type'] == 'person']
            company_rels = [r for r in relationships if r['owner_type'] == 'company']
            
            if person_rels:
                query = """
                UNWIND $relationships AS rel
                MATCH (owner:Person {id: rel.owner_id})
                MATCH (owned:Company {id: rel.owned_id})
                CREATE (owner)-[r:OWNS {
                    ownership_percentage: rel.ownership_percentage,
                    acquisition_date: date(rel.acquisition_date),
                    acquisition_price: rel.acquisition_price,
                    ownership_type: rel.ownership_type,
                    voting_rights: rel.voting_rights,
                    created_at: datetime()
                }]->(owned)
                """
                session.run(query, relationships=person_rels)
            
            if company_rels:
                query = """
                UNWIND $relationships AS rel
                MATCH (owner:Company {id: rel.owner_id})
                MATCH (owned:Company {id: rel.owned_id})
                CREATE (owner)-[r:OWNS {
                    ownership_percentage: rel.ownership_percentage,
                    acquisition_date: date(rel.acquisition_date),
                    acquisition_price: rel.acquisition_price,
                    ownership_type: rel.ownership_type,
                    voting_rights: rel.voting_rights,
                    created_at: datetime()
                }]->(owned)
                """
                session.run(query, relationships=company_rels)
    
    def create_board_positions_batched(self):
        """Create board member relationships in batches"""
        print(f"👔 Creating {NUM_BOARD_POSITIONS:,} board positions in batches...")
        
        positions = ['Chairman', 'CEO', 'CTO', 'CFO', 'COO', 'Director', 'Independent Director']
        total_created = 0
        batch = []
        
        for i in range(NUM_BOARD_POSITIONS):
            person_id = f"person_{random.randint(1, NUM_PEOPLE)}"
            company_id = f"company_{random.randint(1, NUM_COMPANIES)}"
            position = random.choice(positions)
            
            board_position = {
                'person_id': person_id,
                'company_id': company_id,
                'position': position,
                'start_date': self.fake.date_between(start_date='-5y', end_date='today').isoformat(),
                'salary': random.randint(100000, 2000000),
                'equity_compensation': round(random.uniform(0.1, 5.0), 2)
            }
            batch.append(board_position)
            
            # Process batch when it reaches BATCH_SIZE
            if len(batch) >= BATCH_SIZE:
                self._insert_board_batch(batch)
                total_created += len(batch)
                progress = (total_created / NUM_BOARD_POSITIONS) * 100
                print(f"   📊 Progress: {total_created:,}/{NUM_BOARD_POSITIONS:,} positions ({progress:.1f}%)")
                batch = []
        
        # Process remaining positions
        if batch:
            self._insert_board_batch(batch)
            total_created += len(batch)
        
        print(f"✅ Created {total_created:,} board positions")
    
    def _insert_board_batch(self, positions):
        """Insert a batch of board positions"""
        with self.driver.session() as session:
            query = """
            UNWIND $positions AS pos
            MATCH (p:Person {id: pos.person_id})
            MATCH (c:Company {id: pos.company_id})
            MERGE (p)-[r:BOARD_MEMBER {
                position: pos.position,
                start_date: date(pos.start_date),
                salary: pos.salary,
                equity_compensation: pos.equity_compensation,
                created_at: datetime()
            }]->(c)
            """
            session.run(query, positions=positions)
    
    def create_partnerships_batched(self):
        """Create partnerships between companies in batches"""
        print(f"🤝 Creating {NUM_PARTNERSHIPS:,} partnerships in batches...")
        
        partnership_types = ['Joint Venture', 'Strategic Alliance', 'Supplier Agreement', 
                            'Distribution Partnership', 'Technology Partnership']
        total_created = 0
        batch = []
        
        for i in range(NUM_PARTNERSHIPS):
            company1_id = f"company_{random.randint(1, NUM_COMPANIES)}"
            company2_id = f"company_{random.randint(1, NUM_COMPANIES)}"
            
            if company1_id == company2_id:
                continue
            
            partnership = {
                'company1_id': company1_id,
                'company2_id': company2_id,
                'partnership_type': random.choice(partnership_types),
                'start_date': self.fake.date_between(start_date='-3y', end_date='today').isoformat(),
                'contract_value': random.randint(50000, 5000000),
                'description': f"{random.choice(partnership_types)} agreement for mutual business benefit"
            }
            batch.append(partnership)
            
            # Process batch when it reaches BATCH_SIZE
            if len(batch) >= BATCH_SIZE:
                self._insert_partnership_batch(batch)
                total_created += len(batch)
                progress = (total_created / NUM_PARTNERSHIPS) * 100
                print(f"   📊 Progress: {total_created:,}/{NUM_PARTNERSHIPS:,} partnerships ({progress:.1f}%)")
                batch = []
        
        # Process remaining partnerships
        if batch:
            self._insert_partnership_batch(batch)
            total_created += len(batch)
        
        print(f"✅ Created {total_created:,} partnerships")
    
    def _insert_partnership_batch(self, partnerships):
        """Insert a batch of partnerships"""
        with self.driver.session() as session:
            query = """
            UNWIND $partnerships AS part
            MATCH (c1:Company {id: part.company1_id})
            MATCH (c2:Company {id: part.company2_id})
            MERGE (c1)-[r:PARTNER {
                partnership_type: part.partnership_type,
                start_date: date(part.start_date),
                contract_value: part.contract_value,
                description: part.description,
                created_at: datetime()
            }]->(c2)
            """
            session.run(query, partnerships=partnerships)
    
    def create_family_relationships_light(self):
        """Create a lighter set of family relationships for large scale"""
        print("👨‍👩‍👧‍👦 Creating family relationships (sampling for performance)...")
        
        # For million-scale, only create family relationships for a sample
        family_sample_size = min(50000, NUM_PEOPLE // 20)  # 5% of people or 50k max
        family_count = 0
        batch = []
        
        for i in range(0, family_sample_size, random.randint(2, 5)):
            family_size = random.randint(2, 4)
            family_members = []
            
            for j in range(family_size):
                if i + j < NUM_PEOPLE:
                    family_members.append(f"person_{random.randint(1, NUM_PEOPLE)}")
            
            # Create relationships within the family
            for idx, member1 in enumerate(family_members):
                for member2 in family_members[idx + 1:]:
                    relationship_type = random.choice(['Spouse', 'Parent', 'Child', 'Sibling'])
                    
                    family_rel = {
                        'person1_id': member1,
                        'person2_id': member2,
                        'relationship_type': relationship_type
                    }
                    batch.append(family_rel)
                    
                    # Process batch when needed
                    if len(batch) >= 1000:  # Smaller batches for family rels
                        self._insert_family_batch(batch)
                        family_count += len(batch)
                        batch = []
        
        # Process remaining relationships
        if batch:
            self._insert_family_batch(batch)
            family_count += len(batch)
        
        print(f"✅ Created {family_count:,} family relationships")
    
    def _insert_family_batch(self, relationships):
        """Insert a batch of family relationships"""
        with self.driver.session() as session:
            query = """
            UNWIND $relationships AS rel
            MATCH (p1:Person {id: rel.person1_id})
            MATCH (p2:Person {id: rel.person2_id})
            CREATE (p1)-[r:FAMILY {
                relationship_type: rel.relationship_type,
                created_at: datetime()
            }]->(p2)
            """
            session.run(query, relationships=relationships)
    
    def print_summary(self):
        """Print database summary"""
        print("\n📊 Database Summary:")
        
        with self.driver.session() as session:
            # Count nodes
            people_count = session.run("MATCH (p:Person) RETURN count(p) as count").single()["count"]
            companies_count = session.run("MATCH (c:Company) RETURN count(c) as count").single()["count"]
            
            # Count relationships
            ownership_count = session.run("MATCH ()-[r:OWNS]->() RETURN count(r) as count").single()["count"]
            board_count = session.run("MATCH ()-[r:BOARD_MEMBER]->() RETURN count(r) as count").single()["count"]
            partnership_count = session.run("MATCH ()-[r:PARTNER]->() RETURN count(r) as count").single()["count"]
            family_count = session.run("MATCH ()-[r:FAMILY]->() RETURN count(r) as count").single()["count"]
            
            print(f"👥 People: {people_count}")
            print(f"🏢 Companies: {companies_count}")
            print(f"🤝 Ownership relationships: {ownership_count}")
            print(f"👔 Board positions: {board_count}")
            print(f"🤝 Partnerships: {partnership_count}")
            print(f"👨‍👩‍👧‍👦 Family relationships: {family_count}")
            
            # Sample queries
            print("\n🔍 Sample data:")
            
            # Richest people
            result = session.run("""
                MATCH (p:Person) 
                RETURN p.name, p.net_worth 
                ORDER BY p.net_worth DESC 
                LIMIT 3
            """)
            print("\n💰 Richest people:")
            for record in result:
                print(f"   {record['p.name']}: ${record['p.net_worth']:,}")
            
            # Largest companies
            result = session.run("""
                MATCH (c:Company) 
                RETURN c.name, c.market_cap, c.industry
                ORDER BY c.market_cap DESC 
                LIMIT 3
            """)
            print("\n🏢 Largest companies:")
            for record in result:
                print(f"   {record['c.name']} ({record['c.industry']}): ${record['c.market_cap']:,}")
    
    def generate_all_data(self):
        """Generate all test data with performance optimizations for large scale"""
        import time
        
        start_time = time.time()
        print("🚀 Starting LARGE SCALE test data generation...")
        print(f"📊 Target: {NUM_PEOPLE:,} people, {NUM_COMPANIES:,} companies, {NUM_OWNERSHIP_RELATIONSHIPS:,} relationships")
        print(f"⚙️  Using batch size: {BATCH_SIZE:,}")
        print()
        
        # Clear existing data
        self.clear_database()
        
        # Create constraints
        self.create_constraints()
        
        # Generate and insert data in batches
        step_start = time.time()
        self.insert_people_batched()
        print(f"⏱️  People generation took {time.time() - step_start:.1f} seconds")
        print()
        
        step_start = time.time()
        self.insert_companies_batched()
        print(f"⏱️  Companies generation took {time.time() - step_start:.1f} seconds")
        print()
        
        # Create relationships in batches
        step_start = time.time()
        self.create_ownership_relationships_batched()
        print(f"⏱️  Ownership relationships took {time.time() - step_start:.1f} seconds")
        print()
        
        step_start = time.time()
        self.create_board_positions_batched()
        print(f"⏱️  Board positions took {time.time() - step_start:.1f} seconds")
        print()
        
        step_start = time.time()
        self.create_partnerships_batched()
        print(f"⏱️  Partnerships took {time.time() - step_start:.1f} seconds")
        print()
        
        step_start = time.time()
        self.create_family_relationships_light()
        print(f"⏱️  Family relationships took {time.time() - step_start:.1f} seconds")
        print()
        
        # Print summary
        self.print_summary()
        
        total_time = time.time() - start_time
        print(f"\n⏱️  TOTAL GENERATION TIME: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"✅ LARGE SCALE test data generation completed successfully!")
        print("🔍 You can now explore the data in Neo4j Browser at http://localhost:7474")
        print("\n💡 Try these sample queries for large datasets:")
        print("   MATCH (p:Person)-[r:OWNS]->(c:Company) RETURN p, r, c LIMIT 50")
        print("   MATCH (p:Person) RETURN p.occupation, count(*) ORDER BY count(*) DESC LIMIT 10")
        print("   MATCH (c:Company) RETURN c.industry, count(*) ORDER BY count(*) DESC LIMIT 10")
        print("   MATCH (p:Person)-[r:OWNS]->(c:Company) RETURN p.name, sum(r.ownership_percentage) as total_ownership ORDER BY total_ownership DESC LIMIT 10")


def main():
    """Main function"""
    try:
        # Test connection first
        print("🔌 Testing Neo4j connection...")
        generator = Neo4jTestDataGenerator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
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
        print("2. Wait a few seconds for Neo4j to start")
        print("3. Check connection settings in the script")
        sys.exit(1)
    
    finally:
        generator.close()


if __name__ == "__main__":
    main()
