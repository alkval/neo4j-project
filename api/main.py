#!/usr/bin/env python3
"""
FastAPI Backend for Ownership Network Visualization
Provides REST API endpoints for searching entities and retrieving ownership subgraphs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import logging
import os
from neo4j import GraphDatabase
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ownership Network API",
    description="API for searching and visualizing corporate ownership networks",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Neo4j connection
class Neo4jConnection:
    def __init__(self, 
                 uri: str = None, 
                 user: str = None, 
                 password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "ownership123")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        logger.info(f"Connected to Neo4j at {self.uri}")
    
    def close(self):
        self.driver.close()

# Global connection
db = Neo4jConnection()

# Pydantic models
class EntitySearchResult(BaseModel):
    id: str
    name: str
    type: str

class OwnershipNode(BaseModel):
    id: str
    name: str
    type: str
    level: int

class OwnershipEdge(BaseModel):
    source: str
    target: str
    percentage: float
    voting_rights: Optional[float] = None

class OwnershipNetwork(BaseModel):
    nodes: List[OwnershipNode]
    edges: List[OwnershipEdge]
    query_time: float
    total_nodes: int
    total_edges: int

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Ownership Network API is running", "status": "healthy"}

@app.get("/search/entities", response_model=List[EntitySearchResult])
async def search_entities(
    q: str = Query(..., min_length=2, description="Search term for entity name", alias="query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """
    Search for entities by name (fuzzy search)
    """
    try:
        cypher_query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($search_term)
        RETURN e.id as id, e.name as name, e.type as type
        ORDER BY 
            CASE WHEN toLower(e.name) STARTS WITH toLower($search_term) THEN 0 ELSE 1 END,
            size(e.name),
            e.name
        LIMIT $limit
        """
        
        with db.driver.session() as session:
            result = session.run(cypher_query, search_term=q, limit=limit)
            entities = [
                EntitySearchResult(
                    id=record["id"],
                    name=record["name"],
                    type=record["type"] or "Unknown"
                )
                for record in result
            ]
        
        logger.info(f"Found {len(entities)} entities for query: {q}")
        return entities
        
    except Exception as e:
        logger.error(f"Error searching entities: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/ownership/network", response_model=OwnershipNetwork)
async def get_ownership_network(
    entity_id: str = Query(..., description="Entity ID to analyze"),
    max_hops: int = Query(3, ge=1, le=8, description="Maximum number of ownership hops"),
    min_percentage: float = Query(0.1, ge=0.0, le=100.0, description="Minimum ownership percentage threshold")
):
    """
    Get ownership network for a specific entity
    """
    try:
        start_time = time.time()
        
        # Use the working query from ownership_mapper.py
        cypher_query = f"""
        MATCH (target:Entity {{id: $entity_id}})
        CALL {{
            WITH target
            MATCH path = (target)<-[:OWNS*1..{max_hops}]-(owner:Entity)
            WITH path, owner, length(path) as level,
                 reduce(control = 1.0, r in relationships(path) | 
                        control * (coalesce(r.percentage, 0.0)/100.0)) as effective_control
            WHERE effective_control >= ($min_percentage/100.0)
            RETURN owner, level, effective_control, path
            ORDER BY level, effective_control DESC
        }}
        RETURN target.id as company_id,
               target.name as company_name,
               level,
               owner.id as owner_id,
               owner.name as owner_name,
               owner.type as owner_type,
               effective_control,
               [n in nodes(path) | {{id: n.id, name: n.name, type: n.type}}] as path_nodes,
               [r in relationships(path) | {{percentage: r.percentage, voting_rights: r.voting_rights}}] as path_relationships
        ORDER BY level, effective_control DESC
        """
        
        with db.driver.session() as session:
            result = session.run(
                cypher_query, 
                entity_id=entity_id, 
                min_percentage=min_percentage
            )
            
            ownership_data = [dict(record) for record in result]
        
        # Process the data to create nodes and edges
        nodes_dict = {}
        edges = []
        
        # Add target node
        if ownership_data:
            target_data = ownership_data[0]
            nodes_dict[entity_id] = OwnershipNode(
                id=entity_id,
                name=target_data['company_name'],
                type="Corporation",
                level=0
            )
        
        # Process ownership relationships
        for record in ownership_data:
            owner_id = record['owner_id']
            owner_name = record['owner_name']
            owner_type = record['owner_type']
            level = record['level']
            
            # Add owner node if not already added
            if owner_id not in nodes_dict:
                nodes_dict[owner_id] = OwnershipNode(
                    id=owner_id,
                    name=owner_name,
                    type=owner_type or "Unknown",
                    level=level
                )
            
            # Add edges from path
            path_nodes = record['path_nodes']
            path_relationships = record['path_relationships']
            
            for i in range(len(path_nodes) - 1):
                source_node = path_nodes[i]
                target_node = path_nodes[i + 1]
                relationship = path_relationships[i] if i < len(path_relationships) else {}
                
                # Add nodes if missing
                if source_node['id'] not in nodes_dict:
                    nodes_dict[source_node['id']] = OwnershipNode(
                        id=source_node['id'],
                        name=source_node['name'],
                        type=source_node['type'] or "Unknown",
                        level=level - i
                    )
                
                if target_node['id'] not in nodes_dict:
                    nodes_dict[target_node['id']] = OwnershipNode(
                        id=target_node['id'],
                        name=target_node['name'],
                        type=target_node['type'] or "Unknown",
                        level=level - i - 1
                    )
                
                # Add edge
                percentage = relationship.get('percentage', 0)
                if percentage and percentage >= min_percentage:
                    edge = OwnershipEdge(
                        source=source_node['id'],
                        target=target_node['id'],
                        percentage=percentage,
                        voting_rights=relationship.get('voting_rights')
                    )
                    edges.append(edge)
        
        query_time = time.time() - start_time
        nodes = list(nodes_dict.values())
        
        # Remove duplicate edges
        seen_edges = set()
        unique_edges = []
        for edge in edges:
            edge_key = (edge.source, edge.target)
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                unique_edges.append(edge)
        
        network = OwnershipNetwork(
            nodes=nodes,
            edges=unique_edges,
            query_time=query_time,
            total_nodes=len(nodes),
            total_edges=len(unique_edges)
        )
        
        logger.info(f"Generated ownership network for {entity_id}: {len(nodes)} nodes, {len(unique_edges)} edges")
        return network
        
    except Exception as e:
        logger.error(f"Error generating ownership network: {e}")
        raise HTTPException(status_code=500, detail=f"Network generation failed: {str(e)}")

@app.get("/entity/{entity_id}")
async def get_entity_details(entity_id: str):
    """
    Get detailed information about a specific entity
    """
    try:
        cypher_query = """
        MATCH (e:Entity {id: $entity_id})
        OPTIONAL MATCH (e)-[owns:OWNS]->(owned:Entity)
        OPTIONAL MATCH (owner:Entity)-[owned_by:OWNS]->(e)
        RETURN 
            e.id as id,
            e.name as name,
            e.type as type,
            e.jurisdiction as jurisdiction,
            e.status as status,
            count(DISTINCT owns) as direct_subsidiaries,
            count(DISTINCT owned_by) as direct_owners
        """
        
        with db.driver.session() as session:
            result = session.run(cypher_query, entity_id=entity_id)
            record = result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail="Entity not found")
            
            return {
                "id": record["id"],
                "name": record["name"],
                "type": record["type"],
                "jurisdiction": record["jurisdiction"],
                "status": record["status"],
                "direct_subsidiaries": record["direct_subsidiaries"],
                "direct_owners": record["direct_owners"]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entity details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get entity details: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connection on shutdown"""
    db.close()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
