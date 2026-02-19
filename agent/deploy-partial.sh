#!/bin/bash
set -e

# Configuration
PROJECT_ID="vaultbot-486713"
REGION="us-central1"
SERVICE_NAME_IMAGE="vaultbot-image-worker"
SERVICE_NAME_ARTICLE="vaultbot-article-worker"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 VaultBot Partial Deployment (Image & Article)${NC}"
echo ""

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
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},OPENROUTER_API_KEY=${OPENROUTER_API_KEY},PROXY_PROVIDER=${PROXY_PROVIDER},PROXY_USERNAME=${PROXY_USERNAME},PROXY_PASSWORD=${PROXY_PASSWORD},PROXY_HOST=${PROXY_HOST},PROXY_PORT=${PROXY_PORT},YOUTUBE_API_KEY=${YOUTUBE_API_KEY}" \
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
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL},SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY},TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID},TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN},TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER},OPENROUTER_API_KEY=${OPENROUTER_API_KEY},PROXY_PROVIDER=${PROXY_PROVIDER},PROXY_USERNAME=${PROXY_USERNAME},PROXY_PASSWORD=${PROXY_PASSWORD},PROXY_HOST=${PROXY_HOST},PROXY_PORT=${PROXY_PORT},YOUTUBE_API_KEY=${YOUTUBE_API_KEY}"

echo -e "${GREEN}▶️  Starting Article Worker Job...${NC}"
gcloud run jobs execute $SERVICE_NAME_ARTICLE --region $REGION

echo ""
echo -e "${GREEN}✅ Partial Deployment complete!${NC}"
