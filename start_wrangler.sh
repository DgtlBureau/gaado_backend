#!/bin/bash
# Script for local development with Wrangler and D1 database

set -e

# Change to project directory
cd "$(dirname "$0")"

echo "🚀 Starting local development server with Wrangler..."
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler is not installed!"
    echo "   Install it with: npm install -g wrangler"
    echo "   Or use: uv tool install workers-py"
    exit 1
fi

# Check if Python dependencies are installed
echo "📦 Checking Python dependencies..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "   Installing dependencies from requirements.txt..."
    pip3 install -r cf-requirements.txt
    echo "   ✅ Dependencies installed!"
else
    echo "   ✅ Dependencies are installed"
fi
echo ""

echo "📝 Note: Make sure you have:"
echo "   1. Created a local D1 database: wrangler d1 create gaado-db-local"
echo "   2. Updated database_id in wrangler.toml"
echo "   3. Set environment variables (GEMINI_API_KEY, etc.)"
echo ""

# Start wrangler dev with local D1 database
# --local flag uses local D1 database instead of remote
# --port specifies the port (default is 8787)
wrangler dev --local --port 8787

