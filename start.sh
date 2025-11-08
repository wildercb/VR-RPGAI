#!/bin/bash

echo "RPGAI Character Agent System - Startup"
echo "======================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "✓ .env created. Please edit it with your settings."
    echo ""
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if local Ollama is running (required for Mem0)
if grep -q "DEFAULT_LLM_PROVIDER=ollama" .env; then
    echo "Checking local Ollama..."
    if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "ERROR: Ollama is not running on localhost:11434"
        echo "Please install and start Ollama: https://ollama.com/download"
        echo "Or change DEFAULT_LLM_PROVIDER in .env to use OpenRouter instead"
        exit 1
    fi
    echo "✓ Ollama is running"

    # Check and pull required embedding model for Mem0
    echo "Checking for embedding model (nomic-embed-text)..."
    if ! ollama list | grep -q "nomic-embed-text"; then
        echo "Pulling embedding model for memory system..."
        ollama pull nomic-embed-text:latest
    else
        echo "✓ Embedding model already installed"
    fi
fi

echo ""
echo "Starting services..."
echo ""
echo "======================================"
echo "✓ RPGAI is starting!"
echo ""
echo "Web UI: http://localhost:4020"
echo "API Documentation: http://localhost:4020/docs"
echo "Health Check: http://localhost:4020/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo "======================================"
echo ""

docker-compose up
