#!/usr/bin/env python3
"""
Streamlit Frontend for Ownership Network Visualization
Interactive web interface for searching entities and visualizing ownership networks
"""

import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
import networkx as nx
import time
import os
from typing import Dict, List, Any

# Configure Streamlit page
st.set_page_config(
    page_title="Ownership Network Explorer",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .search-container {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def search_entities(query: str, limit: int = 20) -> List[Dict]:
    """Search for entities via API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/search/entities",
            params={"query": query, "limit": limit},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Search failed: {str(e)}")
        return []

def get_ownership_network(entity_id: str, max_hops: int, min_percentage: float) -> Dict:
    """Get ownership network via API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/ownership/network",
            params={
                "entity_id": entity_id,
                "max_hops": max_hops,
                "min_percentage": min_percentage
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Network retrieval failed: {str(e)}")
        return {}

def get_entity_details(entity_id: str) -> Dict:
    """Get entity details via API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/entity/{entity_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Entity details retrieval failed: {str(e)}")
        return {}

def create_network_visualization(network_data: Dict) -> go.Figure:
    """Create interactive network visualization using Plotly"""
    if not network_data or not network_data.get('nodes'):
        return go.Figure()
    
    # Create NetworkX graph for layout calculation
    G = nx.DiGraph()
    
    # Add nodes
    node_info = {}
    for node in network_data['nodes']:
        G.add_node(node['id'])
        node_info[node['id']] = node
    
    # Add edges
    for edge in network_data['edges']:
        G.add_edge(edge['source'], edge['target'], weight=edge['percentage'])
    
    # Calculate layout
    try:
        pos = nx.spring_layout(G, k=3, iterations=50)
    except:
        pos = nx.random_layout(G)
    
    # Prepare node traces
    node_trace = go.Scatter(
        x=[],
        y=[],
        mode='markers+text',
        hoverinfo='text',
        text=[],
        hovertext=[],
        textposition="middle center",
        marker=dict(
            size=[],
            color=[],
            colorscale='viridis',
            line=dict(width=2, color='white'),
            colorbar=dict(
                title="Ownership Level",
                xanchor="left",
                titleside="right"
            )
        )
    )
    
    # Color mapping for entity types
    type_colors = {
        'Corporation': '#1f77b4',
        'Person': '#ff7f0e',
        'Foundation': '#2ca02c',
        'Holding': '#d62728',
        'Partnership': '#9467bd',
        'Trust': '#8c564b',
        'Government': '#e377c2',
        'Unknown': '#7f7f7f'
    }
    
    # Add nodes to trace
    for node_id in G.nodes():
        if node_id in pos:
            x, y = pos[node_id]
            node_trace['x'] += (x,)
            node_trace['y'] += (y,)
            
            node = node_info[node_id]
            node_trace['text'] += (node['name'][:20] + '...' if len(node['name']) > 20 else node['name'],)
            node_trace['marker']['size'] += (30 if node['level'] == 0 else 20,)
            node_trace['marker']['color'] += (node['level'],)
            
            # Hover info
            hover_text = f"<b>{node['name']}</b><br>"
            hover_text += f"Type: {node['type']}<br>"
            hover_text += f"Level: {node['level']}<br>"
            hover_text += f"ID: {node_id}"
            node_trace['hovertext'] += (hover_text,)
    
    # Prepare edge traces
    edge_traces = []
    for edge in network_data['edges']:
        if edge['source'] in pos and edge['target'] in pos:
            x0, y0 = pos[edge['source']]
            x1, y1 = pos[edge['target']]
            
            # Edge line
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(
                    width=max(1, edge['percentage'] / 10),
                    color='rgba(125, 125, 125, 0.5)'
                ),
                hoverinfo='none',
                showlegend=False
            )
            edge_traces.append(edge_trace)
            
            # Edge label (percentage)
            mid_x, mid_y = (x0 + x1) / 2, (y0 + y1) / 2
            edge_label = go.Scatter(
                x=[mid_x],
                y=[mid_y],
                mode='text',
                text=[f"{edge['percentage']:.1f}%"],
                textfont=dict(size=10, color='red'),
                hoverinfo='none',
                showlegend=False
            )
            edge_traces.append(edge_label)
    
    # Create figure
    fig = go.Figure(data=[node_trace] + edge_traces)
    
    fig.update_layout(
        title=f"Ownership Network Visualization",
        titlefont_size=16,
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20,l=5,r=5,t=40),
        annotations=[ dict(
            text="Hover over nodes for details. Node size indicates importance.",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.005, y=-0.002,
            xanchor='left', yanchor='bottom',
            font=dict(color='#888888', size=12)
        )],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    
    return fig

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🕸️ Ownership Network Explorer</h1>', unsafe_allow_html=True)
    
    # Sidebar for search and controls
    with st.sidebar:
        st.header("🔍 Search & Configure")
        
        # Search section
        st.subheader("Entity Search")
        search_query = st.text_input(
            "Search for company or person:",
            placeholder="Enter name to search...",
            help="Search by entity name (minimum 2 characters)"
        )
        
        # Configuration section
        st.subheader("Network Parameters")
        max_hops = st.slider(
            "Maximum Hops",
            min_value=1,
            max_value=8,
            value=3,
            help="How many levels of ownership to explore"
        )
        
        min_percentage = st.slider(
            "Minimum Ownership %",
            min_value=0.0,
            max_value=50.0,
            value=1.0,
            step=0.1,
            help="Minimum ownership percentage threshold"
        )
        
        # API Status
        st.subheader("🔧 API Status")
        try:
            response = requests.get(f"{API_BASE_URL}/", timeout=5)
            if response.status_code == 200:
                st.success("✅ API Connected")
            else:
                st.error("❌ API Error")
        except:
            st.error("❌ API Unavailable")
    
    # Main content area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🏢 Search Results")
        
        if search_query and len(search_query) >= 2:
            with st.spinner("Searching entities..."):
                entities = search_entities(search_query, limit=20)
            
            if entities:
                st.success(f"Found {len(entities)} entities")
                
                # Create selection list
                entity_options = {
                    f"{entity['name']} ({entity['type']})": entity['id'] 
                    for entity in entities
                }
                
                selected_entity_display = st.selectbox(
                    "Select an entity:",
                    options=list(entity_options.keys()),
                    key="entity_selector"
                )
                
                if selected_entity_display:
                    selected_entity_id = entity_options[selected_entity_display]
                    
                    # Show entity details
                    with st.expander("📋 Entity Details", expanded=True):
                        entity_details = get_entity_details(selected_entity_id)
                        if entity_details:
                            st.write(f"**Name:** {entity_details.get('name', 'N/A')}")
                            st.write(f"**Type:** {entity_details.get('type', 'N/A')}")
                            st.write(f"**Jurisdiction:** {entity_details.get('jurisdiction', 'N/A')}")
                            st.write(f"**Status:** {entity_details.get('status', 'N/A')}")
                            st.write(f"**Direct Owners:** {entity_details.get('direct_owners', 0)}")
                            st.write(f"**Direct Subsidiaries:** {entity_details.get('direct_subsidiaries', 0)}")
                    
                    # Generate network button
                    if st.button("🕸️ Generate Ownership Network", type="primary"):
                        st.session_state.generate_network = True
                        st.session_state.selected_entity = selected_entity_id
            else:
                st.info("No entities found. Try a different search term.")
        else:
            st.info("Enter at least 2 characters to search")
    
    with col2:
        st.subheader("🌐 Network Visualization")
        
        # Generate network if requested
        if getattr(st.session_state, 'generate_network', False) and hasattr(st.session_state, 'selected_entity'):
            entity_id = st.session_state.selected_entity
            
            with st.spinner("Generating ownership network..."):
                network_data = get_ownership_network(entity_id, max_hops, min_percentage)
            
            if network_data:
                # Display metrics
                col2a, col2b, col2c, col2d = st.columns(4)
                
                with col2a:
                    st.metric("Nodes", network_data.get('total_nodes', 0))
                with col2b:
                    st.metric("Relationships", network_data.get('total_edges', 0))
                with col2c:
                    st.metric("Query Time", f"{network_data.get('query_time', 0):.3f}s")
                with col2d:
                    st.metric("Max Hops", max_hops)
                
                # Create and display visualization
                fig = create_network_visualization(network_data)
                st.plotly_chart(fig, use_container_width=True)
                
                # Network data table
                with st.expander("📊 Network Data", expanded=False):
                    if network_data.get('nodes'):
                        st.subheader("Entities")
                        nodes_df = pd.DataFrame(network_data['nodes'])
                        st.dataframe(nodes_df, use_container_width=True)
                    
                    if network_data.get('edges'):
                        st.subheader("Ownership Relationships")
                        edges_df = pd.DataFrame(network_data['edges'])
                        st.dataframe(edges_df, use_container_width=True)
                
                # Reset flag
                st.session_state.generate_network = False
            else:
                st.error("Failed to generate network. Please try again.")
        else:
            st.info("Search for an entity and click 'Generate Ownership Network' to visualize ownership relationships.")

if __name__ == "__main__":
    main()
