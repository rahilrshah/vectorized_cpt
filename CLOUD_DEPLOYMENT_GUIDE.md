# 🚀 Cloud Deployment & Usage Guide

## Step 1: Deploy to Google Cloud Run

### Prerequisites
```bash
# Make sure you're authenticated with Google Cloud
gcloud auth login
gcloud auth application-default login
```

### Deploy the System
```bash
# Run the deployment script
./deploy_cloud_run.sh
```

This will:
- Deploy all 5 services to Google Cloud Run
- Generate public HTTPS URLs for each service
- Configure the API Gateway to connect to cloud services
- Create a `cloud_urls.txt` file with all your service URLs

## Step 2: Access Your Cloud Application

After deployment, you'll get URLs like:
- **Web Interface**: https://web-interface-[hash]-uc.a.run.app
- **API Gateway**: https://api-gateway-[hash]-uc.a.run.app

## Step 3: Configure API Key

1. **Visit your Web Interface URL**
2. **Click "Configure API Key"**
3. **Create a new API key** (the system will generate one for you)
4. **Test the connection** (should show "✅ API Connected")

## Step 4: Test All Features

### 🔄 Complete Workflow Tab
1. Enter a medical note like:
   ```
   Patient underwent bilateral total knee arthroplasty with computer-assisted navigation. 
   General anesthesia was administered. Post-operative pain management included epidural catheter.
   ```
2. Click "🚀 Run Complete Workflow"
3. Watch the step-by-step processing:
   - AI extracts procedures
   - Vector search finds CPT codes
   - Comprehensive analysis adds anesthesia/modifiers

### 🧪 Service Testing Tab
- **Medical Text Processing**: Test AI extraction individually
- **CPT Search**: Test vector similarity search
- **Comprehensive Coding**: Test anesthesia/modifier detection

### 📄 PDF Processing Tab
- Upload medical PDFs
- System extracts text and processes through complete workflow

### 📊 Health Dashboard Tab
- Monitor all service health in real-time
- View service endpoints and status

### 📈 Usage Analytics Tab
- Track API usage vs rate limits
- View success rates and performance metrics

## Step 5: Direct API Usage

Once you have an API key, you can use the APIs directly:

```bash
# Complete workflow
curl -X POST "https://api-gateway-[hash]-uc.a.run.app/api/v1/process" \
     -H "Authorization: Bearer vcp_your_api_key_here" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Patient underwent arthroscopic knee surgery...",
       "max_results": 20
     }'

# Individual services
curl -X POST "https://api-gateway-[hash]-uc.a.run.app/api/v1/medical/extract" \
     -H "Authorization: Bearer vcp_your_api_key_here" \
     -H "Content-Type: application/json" \
     -d '{"text": "Patient underwent surgery..."}'
```

## Benefits of Cloud Deployment

✅ **No localhost issues** - Works from any browser  
✅ **HTTPS by default** - Secure connections  
✅ **Auto-scaling** - Handles multiple users  
✅ **Global access** - Available 24/7 worldwide  
✅ **Cost-effective** - Pay only for usage  
✅ **Same API functionality** - Full feature preservation  

## Monitoring & Management

- **Service Health**: Visit `/health` on any service
- **API Documentation**: Visit `/docs` on the API Gateway
- **Usage Statistics**: Monitor via the web interface
- **Logs**: View in Google Cloud Console

## Cost Optimization

- Services auto-scale to zero when not in use
- Only pay for actual requests processed
- Free tier covers significant usage
- Monitor costs in Google Cloud Console