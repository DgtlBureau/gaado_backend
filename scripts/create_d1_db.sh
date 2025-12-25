#!/bin/bash
# Script to create D1 database and update wrangler.toml

set -e

DB_NAME="${1:-gaado-db-local}"
ENV_TYPE="${2:-local}"  # local or production

# Detect wrangler command
if command -v wrangler &> /dev/null; then
    WRANGLER_CMD="wrangler"
elif command -v npx &> /dev/null; then
    WRANGLER_CMD="npx wrangler"
else
    echo "❌ Error: wrangler not found. Install it with: npm install -g wrangler"
    exit 1
fi

# Check if authenticated
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "⚠️  CLOUDFLARE_API_TOKEN not set"
    echo ""
    echo "You need to authenticate with Cloudflare first:"
    echo "  1. Run: $WRANGLER_CMD login"
    echo "     OR"
    echo "  2. Set CLOUDFLARE_API_TOKEN environment variable"
    echo "     Get token from: https://developers.cloudflare.com/fundamentals/api/get-started/create-token/"
    echo ""
    read -p "Do you want to run 'wrangler login' now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $WRANGLER_CMD login
    else
        echo "Please authenticate first, then run this script again."
        exit 1
    fi
fi

echo "🚀 Creating D1 database: $DB_NAME"
echo "Using: $WRANGLER_CMD"
echo ""

# Create database
echo "Creating database..."
DB_OUTPUT=$($WRANGLER_CMD d1 create "$DB_NAME" 2>&1)

echo "$DB_OUTPUT"
echo ""

# Extract database_id from output (compatible with macOS and Linux)
# Try multiple patterns
DB_ID=$(echo "$DB_OUTPUT" | grep -E 'database_id.*=' | sed -E 's/.*database_id.*=.*"([^"]+)".*/\1/' | head -1)

if [ -z "$DB_ID" ]; then
    # Try alternative pattern
    DB_ID=$(echo "$DB_OUTPUT" | grep -E 'id.*=' | sed -E 's/.*id.*=.*"([^"]+)".*/\1/' | head -1)
fi

if [ -z "$DB_ID" ]; then
    # Try UUID pattern
    DB_ID=$(echo "$DB_OUTPUT" | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)
fi

if [ -z "$DB_ID" ]; then
    echo "❌ Could not extract database_id from output"
    echo "Please manually copy the database_id from the output above"
    exit 1
fi

echo "✅ Database created successfully!"
echo "   Database ID: $DB_ID"
echo ""

# Update wrangler.toml
WRANGLER_FILE="wrangler.toml"

if [ "$ENV_TYPE" = "production" ]; then
    echo "📝 Updating production configuration in $WRANGLER_FILE..."
    
    # Check if production section exists
    if grep -q "\[env.production\]" "$WRANGLER_FILE"; then
        # Uncomment and update production d1_databases section
        # Use backup extension for macOS compatibility
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/# \[\[env.production.d1_databases\]\]/[[env.production.d1_databases]]/" "$WRANGLER_FILE"
            sed -i '' "s/# binding = \"DB\"/binding = \"DB\"/" "$WRANGLER_FILE"
            sed -i '' "s/# database_name = \"gaado-db\"/database_name = \"$DB_NAME\"/" "$WRANGLER_FILE"
            sed -i '' "s/# database_id = \".*\"/database_id = \"$DB_ID\"/" "$WRANGLER_FILE"
        else
            sed -i.bak "s/# \[\[env.production.d1_databases\]\]/[[env.production.d1_databases]]/" "$WRANGLER_FILE"
            sed -i.bak "s/# binding = \"DB\"/binding = \"DB\"/" "$WRANGLER_FILE"
            sed -i.bak "s/# database_name = \"gaado-db\"/database_name = \"$DB_NAME\"/" "$WRANGLER_FILE"
            sed -i.bak "s/# database_id = \".*\"/database_id = \"$DB_ID\"/" "$WRANGLER_FILE"
            rm -f "$WRANGLER_FILE.bak"
        fi
        echo "✅ Production configuration updated!"
    else
        echo "⚠️  Production section not found in $WRANGLER_FILE"
        echo "   Please manually add:"
        echo ""
        echo "[[env.production.d1_databases]]"
        echo "binding = \"DB\""
        echo "database_name = \"$DB_NAME\""
        echo "database_id = \"$DB_ID\""
    fi
else
    echo "📝 Updating local configuration in $WRANGLER_FILE..."
    
    # Uncomment and update local d1_databases section
    if grep -q "# \[\[d1_databases\]\]" "$WRANGLER_FILE"; then
        # Use backup extension for macOS compatibility
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/# \[\[d1_databases\]\]/[[d1_databases]]/" "$WRANGLER_FILE"
            sed -i '' "s/# binding = \"DB\"/binding = \"DB\"/" "$WRANGLER_FILE"
            sed -i '' "s/# database_name = \"gaado-db-local\"/database_name = \"$DB_NAME\"/" "$WRANGLER_FILE"
            sed -i '' "s/# database_id = \".*\"/database_id = \"$DB_ID\"/" "$WRANGLER_FILE"
        else
            sed -i.bak "s/# \[\[d1_databases\]\]/[[d1_databases]]/" "$WRANGLER_FILE"
            sed -i.bak "s/# binding = \"DB\"/binding = \"DB\"/" "$WRANGLER_FILE"
            sed -i.bak "s/# database_name = \"gaado-db-local\"/database_name = \"$DB_NAME\"/" "$WRANGLER_FILE"
            sed -i.bak "s/# database_id = \".*\"/database_id = \"$DB_ID\"/" "$WRANGLER_FILE"
            rm -f "$WRANGLER_FILE.bak"
        fi
        echo "✅ Local configuration updated!"
    else
        echo "⚠️  D1 databases section not found in $WRANGLER_FILE"
        echo "   Please manually add:"
        echo ""
        echo "[[d1_databases]]"
        echo "binding = \"DB\""
        echo "database_name = \"$DB_NAME\""
        echo "database_id = \"$DB_ID\""
    fi
fi

echo ""
echo "🎉 Done! Database ID has been added to $WRANGLER_FILE"
echo ""
echo "Next steps:"
echo "  1. Initialize schema: wrangler d1 execute $DB_NAME --local --file=database/schema.sql"
echo "  2. Start dev server: wrangler dev --local"
echo ""

