#!/bin/bash
set -e
PROJECT_ID="vaultbot-486713"
REGION="us-central1"
SERVICE_NAME="vaultbot-video-worker"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Source .env from parent directory
if [ -f ../.env ]; then
    echo "Sourcing .env from parent directory..."
    set -o allexport
    source ../.env
    set +o allexport
else
    echo ".env file not found at ../.env!"
    exit 1
fi

echo "Deploying Video Worker Job: $SERVICE_NAME using image $IMAGE"

gcloud run jobs create $SERVICE_NAME \
    --image $IMAGE \
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
    || gcloud run jobs update $SERVICE_NAME \
    --image $IMAGE \
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
    --set-env-vars "SUMMARIZER_MODEL=${SUMMARIZER_MODEL}"

echo "Starting Video Worker Job..."
gcloud run jobs execute $SERVICE_NAME --region $REGION
echo "Deployment initiated."
