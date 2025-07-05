# Ownership Network Explorer

An interactive web application for exploring complex corporate ownership networks using Neo4j, FastAPI, and Streamlit.

## 🌟 Features

- **Interactive Search**: Search for companies and individuals by name
- **Dynamic Network Visualization**: Interactive ownership network graphs with Plotly
- **Configurable Analysis**: Adjust hop count (1-8 levels) and ownership percentage thresholds
- **Real-time Performance**: Sub-second query performance for complex ownership hierarchies
- **REST API**: FastAPI backend with comprehensive endpoints
- **Modern UI**: Clean, responsive Streamlit frontend

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Git (to clone the repository)

### Option 1: One-Command Startup (Recommended)
```bash
git clone <repository-url>
cd neo4j-project
./start_docker.sh
```

### Option 2: Manual Docker Startup
```bash
git clone <repository-url>
cd neo4j-project
docker-compose up --build -d
```

**Note**: The first startup will take a few minutes to download images and initialize the database.
```

#### 2. Start FastAPI Backend
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Start Streamlit Frontend
```bash
cd frontend
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

## 🌐 Application URLs

- **Frontend (Streamlit)**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000

## 📋 Usage Guide

### 1. Search for Entities
- Enter company or person name in the search box (minimum 2 characters)
- View search results with entity types and details

### 2. Configure Network Parameters
- **Max Hops**: Number of ownership levels to explore (1-8)
- **Min Ownership %**: Minimum ownership threshold (0-50%)

### 3. Generate Network Visualization
- Select an entity from search results
- Click "Generate Ownership Network"
- Explore the interactive network graph

### 4. Analyze Results
- Hover over nodes for detailed information
- View network statistics and performance metrics
- Export network data as tables

## 🏗️ Architecture

### Backend (FastAPI)
- **File**: `api/main.py`
- **Port**: 8000
- **Features**:
  - Entity search endpoint
  - Ownership network generation
  - Entity details retrieval
  - CORS enabled for frontend
  - Comprehensive error handling

### Frontend (Streamlit)
- **File**: `frontend/app.py`
- **Port**: 8501
- **Features**:
  - Interactive search interface
  - Network visualization with Plotly
  - Configurable parameters
  - Real-time API status
  - Data export capabilities

### Database (Neo4j)
- **Port**: 7474 (HTTP), 7687 (Bolt)
- **Features**:
  - 1.5M+ nodes and 3M+ relationships
  - Optimized ownership hierarchy queries
  - Sub-second performance for 8-level queries

## 🔧 API Endpoints

### Search Entities
```
GET /search/entities?query=<name>&limit=<num>
```

### Get Ownership Network
```
GET /ownership/network?entity_id=<id>&max_hops=<num>&min_percentage=<percent>
```

### Get Entity Details
```
GET /entity/<entity_id>
```

### Health Check
```
GET /
```

## 🧪 Performance Benchmarks

- **Query Time**: 0.005-0.15 seconds for 8-level ownership hierarchies
- **Network Size**: Up to 1000+ entities in complex ownership structures
- **Scalability**: Handles 1.5M+ nodes with consistent performance

## 📁 Project Structure

```
neo4j-project/
├── api/
│   ├── main.py              # FastAPI backend
│   └── requirements.txt     # API dependencies
├── frontend/
│   ├── app.py              # Streamlit frontend
│   └── requirements.txt     # Frontend dependencies
├── cypher/                  # Cypher queries
├── data/                    # Neo4j database files
├── import/                  # CSV import files
├── docker-compose.yml       # Neo4j container config
├── start_app.sh            # One-command startup
└── README.md               # This file
```

## 🛠️ Development

### Adding New Features
1. **Backend**: Add endpoints to `api/main.py`
2. **Frontend**: Add UI components to `frontend/app.py`
3. **Database**: Add Cypher queries to `cypher/` directory

### Testing
```bash
# Test API directly
curl http://localhost:8000/search/entities?query=test

# Test with Neo4j browser
# Open http://localhost:7474
```

## 🎯 Use Cases

- **Corporate Due Diligence**: Trace ownership chains and identify ultimate beneficial owners
- **Risk Assessment**: Analyze ownership concentration and circular ownership patterns
- **Regulatory Compliance**: Generate ownership reports for regulatory requirements
- **Investment Analysis**: Understand complex corporate structures before investments

## 📊 Example Queries

The application handles complex queries like:
- "Find all entities with >5% ownership in Company X"
- "Show 6-hop ownership chain for Industrial Group Y"
- "Identify circular ownership patterns in the network"

## 🔄 Data Updates

To update the ownership data:
1. Update CSV files in `import/` directory
2. Run import scripts in `cypher/` directory
3. Restart the application

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions and support:
- Create an issue in this repository
- Check the troubleshooting section
- Review Neo4j community forums

## 🐳 Docker Deployment

The application is fully containerized with Docker for easy deployment and scaling.

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        App Container                            │
│  ┌─────────────────┐           ┌─────────────────┐             │    ┌─────────────────┐
│  │   Frontend      │◄─────────►│       API       │             │◄──►│     Neo4j       │
│  │  (Streamlit)    │           │   (FastAPI)     │             │    │   (Database)    │
│  │   Port: 8501    │           │   Port: 8000    │             │    │   Port: 7687    │
│  └─────────────────┘           └─────────────────┘             │    └─────────────────┘
│           Managed by Supervisor                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Services
- **Neo4j Database**: Graph database with ownership data (separate container)
- **App Container**: Unified container containing both:
  - **FastAPI Backend**: REST API for data access and processing
  - **Streamlit Frontend**: Interactive web interface
  - **Supervisor**: Process manager for running both services

### Docker Commands
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f app
docker-compose logs -f neo4j

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up --build -d

# View service status
docker-compose ps
```
