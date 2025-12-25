#!/bin/bash
# Script for proper server startup

set -e

# Change to project directory
cd "$(dirname "$0")"

# Use system Python3
PYTHON="python3"
PIP="python3 -m pip"

# Function to check if module is installed
check_module() {
    $PYTHON -c "import $1" 2>/dev/null
}

# Check all critical dependencies
MISSING_DEPS=false

echo "🔍 Checking dependencies..."

# Check main modules
if ! check_module fastapi; then
    echo "   ❌ fastapi is not installed"
    MISSING_DEPS=true
fi

if ! check_module google.genai; then
    echo "   ❌ google-genai is not installed"
    MISSING_DEPS=true
fi

if ! check_module uvicorn; then
    echo "   ❌ uvicorn is not installed"
    MISSING_DEPS=true
fi

if ! check_module chromadb; then
    echo "   ❌ chromadb is not installed"
    MISSING_DEPS=true
fi

if ! check_module sentence_transformers; then
    echo "   ❌ sentence-transformers is not installed"
    MISSING_DEPS=true
fi

# If there are missing dependencies, install all from requirements.txt
if [ "$MISSING_DEPS" = true ]; then
    echo ""
    echo "📦 Installing missing dependencies from requirements.txt..."
    $PIP install --user -r requirements.txt
    echo "✅ Dependencies installed!"
    echo ""
else
    echo "✅ All dependencies are installed"
    echo ""
fi

# Start the server
echo "🚀 Starting server..."
echo "   Server will be available at: http://localhost:8000"
echo "   Swagger UI: http://localhost:8000/docs"
echo ""
$PYTHON -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

