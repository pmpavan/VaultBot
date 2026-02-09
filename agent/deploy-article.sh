#!/bin/bash
set -e

# Configuration
PROJECT_ID="vaultbot-486713"
REGION="us-central1"
SERVICE_NAME_ARTICLE="vaultbot-article-worker"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 VaultBot Article Worker - Google Cloud Run Deployment${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Source .env from parent directory
if [ -f ../.env ]; then
    echo "Sourcing .env from parent directory..."
    set -o allexport
    source ../.env
    set +o allexport
else
    echo "⚠️  .env file not found at ../.env! Proceeding with current environment..."
fi

# Check for required proxy variables
if [ -z "$PROXY_HOST" ] || [ -z "$PROXY_PORT" ]; then
    echo -e "${YELLOW}⚠️  WARNING: Proxy configuration incomplete or missing in environment!${NC}"
    echo "   The Article Worker will run without a proxy, which may lead to blocking."
    echo "   Ensure PROXY_HOST, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD are set in ../.env"
    # We do not exit 1 here to allow deployment if user intends no proxy, 
    # but the log warning confirms why it's missing.
    echo "   Continuing in 5 seconds..."
    sleep 5
else
    echo -e "${GREEN}✅ Proxy configuration found: $PROXY_HOST:$PROXY_PORT${NC}"
fi

# Set the project
echo -e "${GREEN}📋 Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs (idempotent)
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Build and deploy Article Worker
echo ""
echo -e "${GREEN}🏗️  Building and pushing Article Worker to GCR...${NC}"
cat > cloudbuild-article.yaml <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'Dockerfile.article', '-t', 'gcr.io/$PROJECT_ID/$SERVICE_NAME_ARTICLE', '.']
images:
- 'gcr.io/$PROJECT_ID/$SERVICE_NAME_ARTICLE'
timeout: 1200s
EOF

gcloud builds submit --config=cloudbuild-article.yaml --timeout=20m .

echo -e "${GREEN}🚀 Deploying Article Worker as Cloud Run Job...${NC}"
gcloud run jobs create $SERVICE_NAME_ARTICLE \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_ARTICLE \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},PROXY_PROVIDER=${PROXY_PROVIDER},PROXY_USERNAME=${PROXY_USERNAME},PROXY_PASSWORD=${PROXY_PASSWORD},PROXY_HOST=${PROXY_HOST},PROXY_PORT=${PROXY_PORT}" \
    || gcloud run jobs update $SERVICE_NAME_ARTICLE \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_ARTICLE \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},PROXY_PROVIDER=${PROXY_PROVIDER},PROXY_USERNAME=${PROXY_USERNAME},PROXY_PASSWORD=${PROXY_PASSWORD},PROXY_HOST=${PROXY_HOST},PROXY_PORT=${PROXY_PORT}"

echo -e "${GREEN}▶️  Starting Article Worker Job...${NC}"
gcloud run jobs execute $SERVICE_NAME_ARTICLE --region $REGION

echo ""
echo -e "${GREEN}✅ Article Worker Deployment complete!${NC}"
echo ""
