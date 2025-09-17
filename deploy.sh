#!/bin/bash
# Deployment script for Hotel Booking API

set -e

echo "🚀 Starting Hotel Booking API deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    printf "${1}${2}${NC}\n"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_color $RED "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_color $RED "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Parse command line arguments
ENVIRONMENT=${1:-development}
BUILD_FRESH=${2:-false}

print_color $BLUE "📋 Deployment Configuration:"
print_color $BLUE "   Environment: $ENVIRONMENT"
print_color $BLUE "   Fresh Build: $BUILD_FRESH"

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    print_color $YELLOW "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    print_color $YELLOW "📝 Please edit .env file with your configuration before continuing."
    read -p "Press Enter to continue after editing .env file..."
fi

# Stop existing containers
print_color $YELLOW "🛑 Stopping existing containers..."
docker-compose down

# Remove old images if fresh build is requested
if [ "$BUILD_FRESH" = "true" ]; then
    print_color $YELLOW "🧹 Removing old images for fresh build..."
    docker-compose down --rmi all --volumes --remove-orphans
fi

# Build and start containers
print_color $BLUE "🔨 Building and starting containers..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
else
    docker-compose up --build -d
fi

# Wait for services to be ready
print_color $YELLOW "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
print_color $BLUE "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    print_color $GREEN "✅ PostgreSQL is ready"
else
    print_color $RED "❌ PostgreSQL is not responding"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_color $GREEN "✅ Redis is ready"
else
    print_color $RED "❌ Redis is not responding"
fi

# Check API
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_color $GREEN "✅ API is ready"
else
    print_color $RED "❌ API is not responding"
fi

# Initialize database
print_color $BLUE "🗄️  Initializing database..."
docker-compose exec api python -m app.db_init init

# Display service URLs
print_color $GREEN "🎉 Deployment completed successfully!"
print_color $GREEN "📊 Service URLs:"
print_color $GREEN "   API: http://localhost:8000"
print_color $GREEN "   API Docs: http://localhost:8000/docs"
print_color $GREEN "   Health Check: http://localhost:8000/health"

if [ "$ENVIRONMENT" != "production" ]; then
    print_color $GREEN "   Grafana: http://localhost:3000 (admin/admin)"
    print_color $GREEN "   Prometheus: http://localhost:9090"
fi

# Show logs
print_color $BLUE "📜 Showing recent logs..."
docker-compose logs --tail=20

print_color $GREEN "🚀 Hotel Booking API is now running!"
print_color $YELLOW "💡 Use 'docker-compose logs -f' to follow logs"
print_color $YELLOW "💡 Use 'docker-compose down' to stop all services"
