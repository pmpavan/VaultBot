#!/bin/bash
set -e

# Configuration
PROJECT_ID="vaultbot-486713"  # TODO: Replace with your GCP project ID
REGION="us-central1"
SERVICE_NAME_CLASSIFIER="vaultbot-classifier-worker"
SERVICE_NAME_VIDEO="vaultbot-video-worker"

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
    --task-timeout 3600s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL}" \
    --set-env-vars "SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}" \
    --set-env-vars "TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}" \
    --set-env-vars "TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}" \
    --set-env-vars "TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER}" \
    || gcloud run jobs update $SERVICE_NAME_CLASSIFIER \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_CLASSIFIER \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --max-retries 0 \
    --task-timeout 3600s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL}" \
    --set-env-vars "SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}" \
    --set-env-vars "TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}" \
    --set-env-vars "TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}" \
    --set-env-vars "TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER}"

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
    --task-timeout 3600s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL}" \
    --set-env-vars "SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}" \
    --set-env-vars "TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}" \
    --set-env-vars "TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}" \
    --set-env-vars "TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER}" \
    --set-env-vars "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}" \
    || gcloud run jobs update $SERVICE_NAME_VIDEO \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME_VIDEO \
    --region $REGION \
    --memory 1Gi \
    --cpu 2 \
    --max-retries 0 \
    --task-timeout 3600s \
    --set-env-vars "SUPABASE_URL=${SUPABASE_URL}" \
    --set-env-vars "SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}" \
    --set-env-vars "TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}" \
    --set-env-vars "TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}" \
    --set-env-vars "TWILIO_PHONE_NUMBER=${TWILIO_PHONE_NUMBER}" \
    --set-env-vars "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"

echo -e "${GREEN}▶️  Starting Video Worker Job...${NC}"
gcloud run jobs execute $SERVICE_NAME_VIDEO --region $REGION

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "📊 Service URLs:"
echo "   Classifier Worker: https://$SERVICE_NAME_CLASSIFIER-<hash>-$REGION.run.app"
echo "   Video Worker: https://$SERVICE_NAME_VIDEO-<hash>-$REGION.run.app"
echo ""
echo "🔍 View logs:"
echo "   gcloud run logs read --service=$SERVICE_NAME_CLASSIFIER --region=$REGION"
echo "   gcloud run logs read --service=$SERVICE_NAME_VIDEO --region=$REGION"
