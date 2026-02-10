#!/bin/bash
# Restart Scraper Worker - Cancel old executions and start fresh
# Fixes issue where old workers without API keys might still be running

set -e

JOB_NAME="vaultbot-scraper-worker"
REGION="us-central1"
PROJECT="vaultbot-486713"

echo "🔄 Restarting Scraper Worker..."
echo "=============================="

# 1. List running executions
echo "🔍 Checking for running executions..."
EXECUTIONS=$(gcloud run jobs executions list --job=$JOB_NAME --region=$REGION --project=$PROJECT --format="value(name)" --filter="status.runningCount>0")

if [ -n "$EXECUTIONS" ]; then
    echo "⚠️  Found running executions:"
    echo "$EXECUTIONS"
    
    # 2. Cancel them
    for EXEC in $EXECUTIONS; do
        echo "🛑 Cancelling execution: $EXEC"
        gcloud run jobs executions cancel $EXEC --region=$REGION --project=$PROJECT --quiet
    done
    echo "✅ All old executions cancelled."
else
    echo "✅ No running executions found."
fi

# 3. Start new execution
echo ""
echo "🚀 Starting new execution..."
gcloud run jobs execute $JOB_NAME --region=$REGION --project=$PROJECT

echo ""
echo "✅ Scraper Worker restarted with fresh configuration!"
echo "👉 Now try sending a YouTube link to WhatsApp."
