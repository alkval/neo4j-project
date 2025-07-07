import pandas as pd
from pathlib import Path

def process_owners_csv(input_file: str, output_dir: Path) -> tuple:
    chunk_size = 10000
    person_chunks = []
    company_chunks = []
    
    for chunk in pd.read_csv(input_file, chunksize=chunk_size):
        persons_chunk = chunk[chunk['is_person'] == True].copy()
        companies_chunk = chunk[chunk['is_company'] == True].copy()
        
        if not persons_chunk.empty:
            person_chunks.append(persons_chunk)
        if not companies_chunk.empty:
            company_chunks.append(companies_chunk)
    
    if person_chunks:
        persons_df = pd.concat(person_chunks, ignore_index=True)
    else:
        persons_df = pd.DataFrame()
        
    if company_chunks:
        companies_df = pd.concat(company_chunks, ignore_index=True)
    else:
        companies_df = pd.DataFrame()
    
    if not persons_df.empty:
        persons_neo4j = persons_df[[
            'id', 'owner_name', 'birth_year', 'postal_code', 
            'postal_city', 'country_code', 'record_year'
        ]].copy()
        
        persons_neo4j.rename(columns={
            'id': 'person_id',
            'owner_name': 'name',
            'birth_year': 'birth_year',
            'postal_code': 'postal_code',
            'postal_city': 'city',
            'country_code': 'country',
            'record_year': 'record_year'
        }, inplace=True)
        
        persons_neo4j['node_type'] = 'Person'
        persons_file = output_dir / 'person_nodes.csv'
        persons_neo4j.to_csv(persons_file, index=False)
    
    if not companies_df.empty:
        companies_neo4j = companies_df[[
            'id', 'owner_name', 'organisation_number', 'postal_code',
            'postal_city', 'country_code', 'record_year'
        ]].copy()
        
        companies_neo4j.rename(columns={
            'id': 'company_id',
            'owner_name': 'name',
            'organisation_number': 'org_number',
            'postal_code': 'postal_code',
            'postal_city': 'city',
            'country_code': 'country',
            'record_year': 'record_year'
        }, inplace=True)
        
        companies_neo4j['node_type'] = 'Company'
        companies_neo4j['source'] = 'owners'
        
        return persons_neo4j if not persons_df.empty else pd.DataFrame(), companies_neo4j, len(persons_df), len(companies_df)
    
    return persons_neo4j if not persons_df.empty else pd.DataFrame(), pd.DataFrame(), len(persons_df), len(companies_df)

def process_stocks_csv(input_file: str) -> pd.DataFrame:
    stocks_df = pd.read_csv(input_file)
    
    companies_neo4j = stocks_df[[
        'id', 'organisation_number', 'company_name', 'total_shares',
        'outstanding_shares', 'share_classes', 'isins', 'record_year'
    ]].copy()
    
    companies_neo4j.rename(columns={
        'id': 'company_id',
        'organisation_number': 'org_number',
        'company_name': 'name',
        'total_shares': 'total_shares',
        'outstanding_shares': 'outstanding_shares',
        'share_classes': 'share_classes',
        'isins': 'isins',
        'record_year': 'record_year'
    }, inplace=True)
    
    companies_neo4j['node_type'] = 'Company'
    companies_neo4j['source'] = 'stocks'
    
    return companies_neo4j

def merge_companies(companies_from_owners: pd.DataFrame, companies_from_stocks: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    if companies_from_owners.empty:
        merged_companies = companies_from_stocks
    elif companies_from_stocks.empty:
        merged_companies = companies_from_owners
    else:
        # Create a proper merge that avoids duplicates but preserves all ID mappings
        merged_companies = pd.concat([companies_from_owners, companies_from_stocks], ignore_index=True)
        
        with_org_num = merged_companies[merged_companies['org_number'].notna()].copy()
        without_org_num = merged_companies[merged_companies['org_number'].isna()]
        
        if not with_org_num.empty:
            # For companies with org_number, create one merged record per org_number
            # but keep track of all IDs that reference this company
            final_companies = []
            id_mappings = []  # Track which IDs map to which final company
            
            for org_num, group in with_org_num.groupby('org_number'):
                if len(group) > 1:
                    # Multiple records with same org_number - merge them properly
                    owners_record = group[group['source'] == 'owners']
                    stocks_record = group[group['source'] == 'stocks']
                    
                    if not owners_record.empty and not stocks_record.empty:
                        # Use stocks record as primary (it has more company data)
                        # but preserve owners ID for relationship mapping
                        primary_record = stocks_record.iloc[0].copy()
                        owners_data = owners_record.iloc[0]
                        
                        # Create ID mapping entries
                        id_mappings.append({
                            'original_id': owners_data['company_id'],
                            'mapped_to_id': primary_record['company_id'],
                            'source': 'owners_to_stocks'
                        })
                        
                        # Enrich with any missing data from owners
                        if pd.isna(primary_record['postal_code']) and pd.notna(owners_data['postal_code']):
                            primary_record['postal_code'] = owners_data['postal_code']
                        if pd.isna(primary_record['city']) and pd.notna(owners_data['city']):
                            primary_record['city'] = owners_data['city']
                        if pd.isna(primary_record['country']) and pd.notna(owners_data['country']):
                            primary_record['country'] = owners_data['country']
                        
                        # Mark as merged from both sources
                        primary_record['source'] = 'merged'
                        
                        final_companies.append(primary_record)
                    else:
                        # Keep all records if we can't merge
                        final_companies.extend(group.to_dict('records'))
                else:
                    # Single record, keep as is
                    final_companies.append(group.iloc[0])
            
            with_org_num = pd.DataFrame(final_companies)
            
            # Save ID mappings for relationship processing
            if id_mappings:
                mappings_df = pd.DataFrame(id_mappings)
                mappings_file = output_dir / 'company_id_mappings.csv'
                mappings_df.to_csv(mappings_file, index=False)
                print(f"Saved {len(mappings_df)} ID mappings to {mappings_file}")
        
        merged_companies = pd.concat([with_org_num, without_org_num], ignore_index=True)
    
    companies_file = output_dir / 'company_nodes.csv'
    merged_companies.to_csv(companies_file, index=False)
    
    return merged_companies

def main():
    current_dir = Path.cwd()
    owners_file = current_dir / 'owners.csv'
    stocks_file = current_dir / 'stocks.csv'
    
    if not owners_file.exists() or not stocks_file.exists():
        print("Error: owners.csv or stocks.csv not found")
        return
    
    persons_df, companies_from_owners, persons_count, companies_count = process_owners_csv(
        str(owners_file), current_dir
    )
    
    companies_from_stocks = process_stocks_csv(str(stocks_file))
    merged_companies = merge_companies(companies_from_owners, companies_from_stocks, current_dir)
    
    print(f"Generated:")
    print(f"  person_nodes.csv: {persons_count:,} records")
    print(f"  company_nodes.csv: {len(merged_companies):,} records")

if __name__ == "__main__":
    main()
