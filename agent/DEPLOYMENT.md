# VaultBot Workers - Google Cloud Run Deployment Guide

## Overview

VaultBot uses **Cloud Run Jobs** for background processing:
- `vaultbot-classifier-worker`: Polls for new jobs and classifies content.
- `vaultbot-video-worker`: Processes video content.

## Twilio Trial Setup (Sandbox)

If you are on a Twilio Trial account, you cannot add custom WhatsApp Senders. You **MUST** use the Twilio Sandbox.

1. Go to [Twilio Console > Messaging > Try it out > Send a WhatsApp message](https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn).
2. Follow instructions to join the Sandbox (send a code to the sandbox number).
3. **Configure Callback URL:**
   - Go to [Sandbox Settings](https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox).
   - In "When a message comes in", enter your Supabase Function URL:
     `https://ixdoczhvuvqpqzcjgrcj.supabase.co/functions/v1/webhook-handler`
   - Set method to **POST**.
   - Click **Save**.

**Note:** For Trial accounts, you can only send messages to numbers that have joined your Sandbox.

## Prerequisites

1. **Google Cloud Project**
   - Create a GCP project at https://console.cloud.google.com
   - Note your Project ID

2. **Install gcloud CLI**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from:
   # https://cloud.google.com/sdk/docs/install
   ```

3. **Authenticate**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

4. **Environment Variables**
   Ensure your `.env` file (in project root) contains:
   ```env
   SUPABASE_URL=...
   SUPABASE_SERVICE_ROLE_KEY=...
   TWILIO_ACCOUNT_SID=...
   TWILIO_AUTH_TOKEN=...
   TWILIO_PHONE_NUMBER=+14155238886  # Default Sandbox Number
   OPENROUTER_API_KEY=...
   ```

## Deployment Steps

1. **Configure Project ID**
   Edit `agent/deploy-gcp.sh` and set `PROJECT_ID`.

2. **Deploy Workers**
   ```bash
   cd agent
   ./deploy-gcp.sh
   ```
   This script builds images using Cloud Build, creates Cloud Run Jobs, and deploys them.

## Managing Workers

Since these are **Cloud Run Jobs** configured to run effectively as continuous workers (long timeout, infinite loop), you manage them via `gcloud run jobs`.

### Check Status
```bash
# List executions
gcloud run jobs executions list --region us-central1

# View logs
gcloud run jobs logs read vaultbot-video-worker --region us-central1
```

### Stop/Restart
To restart a worker (e.g. after deployment), the deployment script automatically triggers a new execution.
To manually start:
```bash
gcloud run jobs execute vaultbot-video-worker --region us-central1
```

### Resource Configuration
- **Classifier**: 512Mi RAM, 1 CPU
- **Video Worker**: 1Gi RAM, 2 CPU
- **Timeout**: 3600s (1 hour) - The worker will exit and need to be restarted or set to longer timeout/parallelism. 
  *(Note: For true continuous operation, consider Cloud Run Services or a scheduler to re-trigger jobs).*

## Troubleshooting

- **Twilio Error 21211 (Invalid 'To' Phone Number)**: Ensure the recipient has joined your Sandbox.
- **Worker Crashes**: Check logs for memory issues or unhandled exceptions.
- **Supabase Connection**: Verify `SUPABASE_URL` and Key in `.env` match your project.
- **Cloud Build Errors**: Check `cloudbuild.yaml` in the deployment script logs.
