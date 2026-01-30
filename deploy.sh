#!/bin/bash

# 🚀 Deploy Script for Clips Generator
# Usage: ./deploy.sh

set -e  # Exit on error

echo "🐳 Starting deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo -e "${YELLOW}📝 Please create .env file with your API keys:${NC}"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed!${NC}"
    echo "   Install: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed!${NC}"
    echo "   Install: apt install docker-compose -y"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites checked${NC}"

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down || true

# Build new image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker-compose build --no-cache

# Start containers
echo -e "${YELLOW}🚀 Starting containers...${NC}"
docker-compose up -d

# Wait for health check
echo -e "${YELLOW}⏳ Waiting for API to be ready...${NC}"
sleep 10

# Test health endpoint
if curl -f http://localhost:8000/health &> /dev/null; then
    echo -e "${GREEN}✅ API is healthy!${NC}"
    echo -e "${GREEN}🎉 Deployment successful!${NC}"
    echo ""
    echo "📊 Access your API at:"
    echo "   - Health: http://localhost:8000/health"
    echo "   - Docs: http://localhost:8000/docs"
    echo ""
    echo "📝 View logs with:"
    echo "   docker-compose logs -f api"
else
    echo -e "${RED}❌ API health check failed${NC}"
    echo "View logs with: docker-compose logs api"
    exit 1
fi
