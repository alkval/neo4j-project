#!/bin/bash

# Docker-based Ownership Network Application Startup Script

echo "🕸️ Starting Ownership Network Application with Docker..."

# Ensure required directories exist
echo "Creating required directories..."
mkdir -p data logs

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# Build and start all services
echo "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check Neo4j
echo "Checking Neo4j status..."
until curl -s http://localhost:7474 > /dev/null; do
    echo "Waiting for Neo4j to be ready..."
    sleep 5
done
echo "✅ Neo4j is ready"

# Check API
echo "Checking API status..."
until curl -s http://localhost:8000/ > /dev/null; do
    echo "Waiting for API to be ready..."
    sleep 5
done
echo "✅ API is ready"

# Check Frontend
echo "Checking Frontend status..."
until curl -s http://localhost:8501/_stcore/health > /dev/null; do
    echo "Waiting for Frontend to be ready..."
    sleep 5
done
echo "✅ Frontend is ready"

echo ""
echo "🚀 Ownership Network Application is now running!"
echo ""
echo "📊 Services:"
echo "   • Neo4j Browser: http://localhost:7474"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Frontend Application: http://localhost:8501"
echo ""
echo "📋 To view logs:"
echo "   • All services: docker-compose logs -f"
echo "   • App container: docker-compose logs -f app"
echo "   • Neo4j only: docker-compose logs -f neo4j"
echo ""
echo "🛑 To stop: docker-compose down"
echo ""
echo "Application ready! Open http://localhost:8501 in your browser."
