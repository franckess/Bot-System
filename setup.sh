#!/bin/bash

# # Ensure Docker socket is available
# if [ ! -S /var/run/docker.sock ]; then
#   echo "Docker socket not found at /var/run/docker.sock. Please ensure Docker is running."
#   exit 1
# fi

# Stop and remove all Docker Compose services
echo "Stopping and removing all Docker Compose services..."
docker-compose down

# Stop all running containers
echo "Stopping all running containers..."
docker stop $(docker ps -q)

# Remove all containers
echo "Removing all containers..."
docker rm $(docker ps -a -q)

# Remove all images
echo "Removing all images..."
docker rmi $(docker images -q)

# Build new Docker images
echo "Building new Docker images..."
docker-compose build

# Deploy new Docker containers
echo "Deploying new Docker containers..."
docker-compose up -d

echo "Docker containers have been built and deployed successfully."