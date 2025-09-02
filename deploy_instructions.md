# Railway Deployment Instructions

## Quick Setup Commands

After authenticating with `railway login`, run these commands:

```bash
# 1. Initialize Railway project
railway login

# 2. Create new project
railway init

# 3. Deploy the application
railway up
```

## Manual Deployment Steps

### 1. Authenticate with Railway
```bash
railway login
```
- This opens your browser for GitHub authentication
- Grant Railway access to your repositories

### 2. Initialize Project
```bash
railway init
```
- Select "Deploy from the current directory"
- Choose a project name (e.g., "vectorized-cpt-web")

### 3. Deploy
```bash
railway up
```
- Railway will automatically detect the Dockerfile
- Build and deploy the application
- Generate a public URL

## Expected Deployment Process

1. **Build Phase** (2-3 minutes)
   - Docker container build
   - Python dependencies installation
   - Application code copying

2. **Setup Phase** (30 seconds)
   - Database creation
   - Team and API key generation
   - System initialization

3. **Deploy Phase** (30 seconds)
   - Service startup
   - Health check validation
   - Public URL activation

## After Deployment

Your app will be available at: `https://[your-project-name].railway.app`

### Generated API Keys

The system automatically creates:
- **Admin API Key**: Full access (displayed in logs)
- **Sample Team Keys**: Basic, Premium, Enterprise tiers

### Testing the Deployment

1. Visit your Railway URL
2. Use the web dashboard to test API functionality
3. Configure API keys in the interface
4. Test medical note processing

## Environment Variables (Auto-Configured)

- `PORT`: Set by Railway
- `PYTHONPATH`: /app
- `DATABASE_PATH`: /app/api_keys.db
- `VECTORIZED_CPT_API_KEY`: Auto-generated during setup

## Troubleshooting

### View Logs
```bash
railway logs
```

### Redeploy
```bash
railway up --detach
```

### Check Service Status
```bash
railway status
```

## Security Note

The admin API key is displayed once during initial deployment. Save it securely for team management functions.