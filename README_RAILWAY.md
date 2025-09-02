# Railway Deployment Guide

## Quick Deploy to Railway

### Option 1: One-Click Deploy
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/aAbCtS)

### Option 2: Manual Deploy

1. **Fork this repository**
2. **Connect to Railway:**
   - Go to [railway.app](https://railway.app)
   - Sign up/Login with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your forked repository

3. **Environment Variables (Optional):**
   - `VECTORIZED_CPT_API_KEY`: Will be auto-generated on first run
   - `PORT`: Automatically set by Railway
   - `API_GATEWAY_URL`: Automatically configured

4. **Deploy:**
   - Railway will automatically build and deploy
   - Your app will be available at `https://your-app-name.railway.app`

## Features Available

- **Medical Note Processing**: Complete CPT coding workflow
- **API Testing Dashboard**: Test individual services
- **Team Management**: Multi-tier access control
- **Usage Analytics**: Track API usage and performance
- **PDF Processing**: Upload and process medical PDFs

## API Keys

The system auto-generates API keys on first deployment:
- **Admin Key**: Full access to all features
- **Sample Keys**: Basic, Premium, and Enterprise tier examples

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup teams and keys
python setup_railway.py

# Start web server
uvicorn web_server_api:app --reload --port 8080
```

## System Architecture

- **Web Interface**: FastAPI serving static HTML dashboard
- **API Gateway**: Team-based authentication and routing
- **Billing System**: Core medical coding logic
- **Database**: SQLite for API keys and usage tracking

## Configuration

All configuration is handled automatically. The system:
1. Creates SQLite database on first run
2. Generates admin and sample API keys
3. Configures team tiers and permissions
4. Starts web interface

Access your deployed app and start testing with the auto-generated API keys!