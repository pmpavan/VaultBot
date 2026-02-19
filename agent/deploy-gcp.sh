#!/bin/bash
set -e

# Configuration
PROJECT_ID="vaultbot-486713"  # TODO: Replace with your GCP project ID
REGION="us-central1"
SERVICE_NAME_CLASSIFIER="vaultbot-classifier-worker"
SERVICE_NAME_VIDEO="vaultbot-video-worker"
SERVICE_NAME_SCRAPER="vaultbot-scraper-worker"
SERVICE_NAME_IMAGE="vaultbot-image-worker"
SERVICE_NAME_ARTICLE="vaultbot-article-worker"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 VaultBot Workers - Google Cloud Run Deployment${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first:"
    echo "   https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if PROJECT_ID is set
if [ "$PROJECT_ID" == "your-gcp-project-id" ]; then
    echo "❌ Please set your GCP PROJECT_ID in this script"
    exit 1
fi

# Source .env from parent directory
if [ -f ../.env ]; then
    echo "Sourcing .env from parent directory..."
    set -o allexport
    source ../.env
    set +o allexport
else
    echo "⚠️  .env file not found at ../.env! Proceeding with current environment..."
fi

# Set the project
echo -e "${GREEN}📋 Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${GREEN}🔧 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Build and deploy Classifier Worker
echo ""
echo -e "${GREEN}🏗️  Building and pushing Classifier Worker to GCR...${NC}"
cat > cloudbuild-classifier.yaml <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'Dockerfile.classifier', '-t', 'gcr.io/$PROJECT_ID/$SERVICE_NAME_CLASSIFIER', '.']
images:
- 'gcr.io/$PROJECT_ID/$SERVICE_NAME_CLASSIFIER'
timeout: 1200s
EOF

gcloud builds submit --config=cloudbuild-classifier.yaml --timeout=20m .

echo -e "${GREEN}🚀 Deploying Classifier Worker as Cloud Run Job...${NC}"
gcloud run jobs create $SERVICE_NAME_CLASSIFIER \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_CLASSIFIER \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER}" \
    || gcloud run jobs update $SERVICE_NAME_CLASSIFIER \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_CLASSIFIER \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER}"

echo -e "${GREEN}▶️  Starting Classifier Worker Job...${NC}"
gcloud run jobs execute $SERVICE_NAME_CLASSIFIER --region $REGION

# Build and deploy Video Worker
echo ""
echo -e "${GREEN}🏗️  Building and pushing Video Worker to GCR...${NC}"
cat > cloudbuild-video.yaml <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'Dockerfile.video', '-t', 'gcr.io/$PROJECT_ID/$SERVICE_NAME_VIDEO', '.']
images:
- 'gcr.io/$PROJECT_ID/$SERVICE_NAME_VIDEO'
timeout: 1200s
EOF

gcloud builds submit --config=cloudbuild-video.yaml --timeout=20m .

echo -e "${GREEN}🚀 Deploying Video Worker as Cloud Run Job...${NC}"
gcloud run jobs create $SERVICE_NAME_VIDEO \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_VIDEO \
    --region $REGION \
    --memory 1Gi \
    --cpu 2 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},OPENROUTER_API_KEY=${OPENROUTER_API_KEY},YOUTUBE_API_KEY=${YOUTUBE_API_KEY},SUMMARIZER_MODEL=${SUMMARIZER_MODEL}" \
    || gcloud run jobs update $SERVICE_NAME_VIDEO \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_VIDEO \
    --region $REGION \
    --memory 1Gi \
    --cpu 2 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},OPENROUTER_API_KEY=${OPENROUTER_API_KEY},YOUTUBE_API_KEY=${YOUTUBE_API_KEY}"

echo -e "${GREEN}▶️  Starting Video Worker Job...${NC}"
gcloud run jobs execute $SERVICE_NAME_VIDEO --region $REGION

# Build and deploy Scraper Worker
echo ""
echo -e "${GREEN}🏗️  Building and pushing Scraper Worker to GCR...${NC}"
cat > cloudbuild-scraper.yaml <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'Dockerfile.scraper', '-t', 'gcr.io/$PROJECT_ID/$SERVICE_NAME_SCRAPER', '.']
images:
- 'gcr.io/$PROJECT_ID/$SERVICE_NAME_SCRAPER'
timeout: 1200s
EOF

gcloud builds submit --config=cloudbuild-scraper.yaml --timeout=20m .

echo -e "${GREEN}🚀 Deploying Scraper Worker as Cloud Run Job...${NC}"
gcloud run jobs create $SERVICE_NAME_SCRAPER \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_SCRAPER \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},YOUTUBE_API_KEY=${YOUTUBE_API_KEY},SUMMARIZER_MODEL=${SUMMARIZER_MODEL}" \
    || gcloud run jobs update $SERVICE_NAME_SCRAPER \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_SCRAPER \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},YOUTUBE_API_KEY=${YOUTUBE_API_KEY}"

echo -e "${GREEN}▶️  Starting Scraper Worker Job...${NC}"
gcloud run jobs execute $SERVICE_NAME_SCRAPER --region $REGION

# Build and deploy Image Worker
echo ""
echo -e "${GREEN}🏗️  Building and pushing Image Worker to GCR...${NC}"
cat > cloudbuild-image.yaml <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-f', 'Dockerfile.image', '-t', 'gcr.io/$PROJECT_ID/$SERVICE_NAME_IMAGE', '.']
images:
- 'gcr.io/$PROJECT_ID/$SERVICE_NAME_IMAGE'
timeout: 1200s
EOF

gcloud builds submit --config=cloudbuild-image.yaml --timeout=20m .

echo -e "${GREEN}🚀 Deploying Image Worker as Cloud Run Job...${NC}"
gcloud run jobs create $SERVICE_NAME_IMAGE \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_IMAGE \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},OPENROUTER_API_KEY=${OPENROUTER_API_KEY},PROXY_PROVIDER=${PROXY_PROVIDER},PROXY_USERNAME=${PROXY_USERNAME},PROXY_PASSWORD=${PROXY_PASSWORD},PROXY_HOST=${PROXY_HOST},PROXY_PORT=${PROXY_PORT},YOUTUBE_API_KEY=${YOUTUBE_API_KEY},SUMMARIZER_MODEL=${SUMMARIZER_MODEL}" \
    || gcloud run jobs update $SERVICE_NAME_IMAGE \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_IMAGE \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},OPENROUTER_API_KEY=${OPENROUTER_API_KEY},PROXY_PROVIDER=${PROXY_PROVIDER},PROXY_USERNAME=${PROXY_USERNAME},PROXY_PASSWORD=${PROXY_PASSWORD},PROXY_HOST=${PROXY_HOST},PROXY_PORT=${PROXY_PORT},YOUTUBE_API_KEY=${YOUTUBE_API_KEY}" 

echo -e "${GREEN}▶️  Starting Image Worker Job...${NC}"
gcloud run jobs execute $SERVICE_NAME_IMAGE --region $REGION

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
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},OPENROUTER_API_KEY=${OPENROUTER_API_KEY},PROXY_PROVIDER=${PROXY_PROVIDER},PROXY_USERNAME=${PROXY_USERNAME},PROXY_PASSWORD=${PROXY_PASSWORD},PROXY_HOST=${PROXY_HOST},PROXY_PORT=${PROXY_PORT},YOUTUBE_API_KEY=${YOUTUBE_API_KEY}" \
    || gcloud run jobs update $SERVICE_NAME_ARTICLE \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_ARTICLE \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --max-retries 0 \
    --task-timeout 86400s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},OPENROUTER_API_KEY=${OPENROUTER_API_KEY},PROXY_PROVIDER=${PROXY_PROVIDER},PROXY_USERNAME=${PROXY_USERNAME},PROXY_PASSWORD=${PROXY_PASSWORD},PROXY_HOST=${PROXY_HOST},PROXY_PORT=${PROXY_PORT},YOUTUBE_API_KEY=${YOUTUBE_API_KEY},SUMMARIZER_MODEL=${SUMMARIZER_MODEL}"

echo -e "${GREEN}▶️  Starting Article Worker Job...${NC}"
gcloud run jobs execute $SERVICE_NAME_ARTICLE --region $REGION

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📊 Service status (view logs):"
echo "   gcloud run jobs executions list --job=$SERVICE_NAME_CLASSIFIER --region=$REGION"
echo "   gcloud run jobs executions list --job=$SERVICE_NAME_VIDEO --region=$REGION"
echo "   gcloud run jobs executions list --job=$SERVICE_NAME_SCRAPER --region=$REGION"
echo "   gcloud run jobs executions list --job=$SERVICE_NAME_IMAGE --region=$REGION"
echo "   gcloud run jobs executions list --job=$SERVICE_NAME_ARTICLE --region=$REGION"
echo ""

