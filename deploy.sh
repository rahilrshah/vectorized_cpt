#!/bin/bash
# Railway Deployment Script for Vectorized CPT

set -e

echo "🚂 Vectorized CPT - Railway Deployment Script"
echo "============================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check authentication
echo "🔐 Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "❌ Not authenticated with Railway"
    echo "📱 Please run: railway login"
    echo "   This will open your browser for GitHub authentication"
    exit 1
fi

echo "✅ Authenticated with Railway as: $(railway whoami)"

# Initialize project if not already done
echo "🏗️  Checking Railway project..."
if [ ! -f .railway.json ]; then
    echo "📋 Initializing new Railway project..."
    railway init
else
    echo "✅ Railway project already initialized"
fi

# Deploy the application
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Your application will be available at:"
railway domain

echo ""
echo "📋 Next steps:"
echo "1. Wait for the deployment to finish (2-3 minutes)"
echo "2. Visit your Railway URL"
echo "3. Check deployment logs: railway logs"
echo "4. Use the web interface to test functionality"
echo ""
echo "🔑 The admin API key will be displayed in the deployment logs"
echo "   Save it securely for team management functions"