#!/bin/bash
# Script to initialize D1 database schema

set -e

DB_NAME="${1:-gaado-db-local}"
USE_LOCAL="${2:-true}"

# Detect wrangler command
if command -v wrangler &> /dev/null; then
    WRANGLER_CMD="wrangler"
elif command -v npx &> /dev/null; then
    WRANGLER_CMD="npx wrangler"
else
    echo "❌ Error: wrangler not found. Install it with: npm install -g wrangler"
    exit 1
fi

if [ "$USE_LOCAL" = "true" ] || [ "$USE_LOCAL" = "local" ]; then
    echo "📦 Initializing LOCAL D1 database schema: $DB_NAME"
    echo ""
    $WRANGLER_CMD d1 execute "$DB_NAME" --local --file=database/schema.sql
    echo ""
    echo "✅ Schema initialized successfully!"
else
    echo "📦 Initializing PRODUCTION D1 database schema: $DB_NAME"
    echo ""
    $WRANGLER_CMD d1 execute "$DB_NAME" --file=database/schema.sql
    echo ""
    echo "✅ Schema initialized successfully!"
fi

echo ""
echo "Database is ready to use!"

