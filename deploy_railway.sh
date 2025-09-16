#!/bin/bash

echo "🚂 Railway Deployment Script for MVP IAM Backend"
echo "================================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

echo "🔐 Logging into Railway..."
railway login

echo "🚀 Initializing Railway project..."
railway init

echo "🐘 Adding PostgreSQL database..."
railway add postgresql

echo "⚙️  Setting environment variables..."
railway variables set DEMO_API_TOKEN="demo-token-12345"
railway variables set ALLOWED_ORIGINS="http://localhost:3000,http://localhost:3001,http://localhost:5173,https://ion-app-rose.vercel.app,https://app.privion.tech"
railway variables set DEBUG="false"
railway variables set APP_NAME="MVP IAM Backend"

echo "📦 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment initiated! Your backend will be available shortly."
echo ""
echo "🔧 After deployment completes, run these commands to set up the database:"
echo "   railway shell"
echo "   alembic upgrade head"
echo "   python seed_db.py"
echo "   exit"
echo ""
echo "📱 Your API will be available at the URL shown above"
echo "📖 API Docs: https://your-project.railway.app/docs"
echo "❤️  Health Check: https://your-project.railway.app/health"
echo ""
echo "🎉 Happy coding!"
