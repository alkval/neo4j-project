#!/bin/bash

# Quick validation script to test if the project works on a fresh machine

echo "🧪 Testing fresh deployment setup..."

# Test if required files exist
required_files=("docker-compose.yml" "Dockerfile" "api/main.py" "frontend/app.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All required files present"

# Test if directories exist
required_dirs=("data" "logs" "conf")
for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "❌ Missing required directory: $dir"
        exit 1
    fi
done

echo "✅ All required directories present"

# Test Docker Compose syntax
if docker-compose config > /dev/null 2>&1; then
    echo "✅ docker-compose.yml syntax is valid"
else
    echo "❌ docker-compose.yml has syntax errors"
    exit 1
fi

echo ""
echo "🚀 Project is ready for deployment!"
echo "To start the application, run: ./start_docker.sh"
echo "Or manually: docker-compose up --build -d"
