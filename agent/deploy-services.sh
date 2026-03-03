#!/bin/bash
set -e

# Configuration
PROJECT_ID="vaultbot-486713"
REGION="us-central1"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 VaultBot Worker Fleet - Google Cloud Run Service Deployment${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
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
    echo "⚠️  .env file not found at ../.env! Ensure variables are set in current shell."
fi

# Set the project
echo -e "${GREEN}📋 Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com

# Common environment variables
COMMON_ENV="SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},OPENROUTER_API_KEY=${OPENROUTER_API_KEY},WORKER_SECRET=${WORKER_SECRET}"

deploy_service() {
    local NAME=$1
    local DOCKERFILE=$2
    local IMAGE="gcr.io/$PROJECT_ID/vaultbot-$NAME-service"
    local EXTRA_ENV=$3

    echo -e "${GREEN}🏗️  Building and Deploying $NAME...${NC}"
    
    # Build
    gcloud builds submit --tag "$IMAGE" --dockerfile "$DOCKERFILE" .

    # Deploy as Service
    gcloud run deploy "vaultbot-$NAME-service" \
        --image "$IMAGE" \
        --region "$REGION" \
        --platform managed \
        --allow-unauthenticated \
        --memory 512Mi \
        --cpu 1 \
        --min-instances 0 \
        --max-instances 10 \
        --concurrency 80 \
        --set-env-vars "$COMMON_ENV,$EXTRA_ENV"
}

# Deploy each service
deploy_service "classifier" "Dockerfile.classifier" ""
deploy_service "scraper" "Dockerfile.scraper" "PROXY_PROVIDER=${PROXY_PROVIDER},PROXY_USERNAME=${PROXY_USERNAME},PROXY_PASSWORD=${PROXY_PASSWORD},PROXY_HOST=${PROXY_HOST},PROXY_PORT=${PROXY_PORT},YOUTUBE_API_KEY=${YOUTUBE_API_KEY},SUMMARIZER_MODEL=${SUMMARIZER_MODEL}"
deploy_service "article" "Dockerfile.article" "SUMMARIZER_MODEL=${SUMMARIZER_MODEL}"
deploy_service "image" "Dockerfile.image" "SUMMARIZER_MODEL=${SUMMARIZER_MODEL}"
deploy_service "video" "Dockerfile.video" "SUMMARIZER_MODEL=${SUMMARIZER_MODEL}"

echo ""
echo -e "${GREEN}✅ All Worker Services Deployed Successfully!${NC}"
echo -e "${YELLOW}🔗 URLs can be found in the GCP Console or via 'gcloud run services list'${NC}"
echo ""
