# Environment Setup Guide

## Local Development

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Get your Twilio credentials:**
   - Go to [Twilio Console](https://console.twilio.com/)
   - Copy your Account SID and Auth Token
   - Paste them into `.env`

3. **Get your Supabase credentials:**
   - Go to [Supabase Dashboard](https://app.supabase.com/project/_/settings/api)
   - Copy your Project URL and Service Role Key
   - Paste them into `.env`

4. **Your `.env` file should look like:**
   ```env
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

## Supabase Edge Functions Deployment

### Option 1: Via Supabase CLI

```bash
# Set secrets
supabase secrets set TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
supabase secrets set TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Verify secrets
supabase secrets list
```

### Option 2: Via Supabase Dashboard

1. Go to your project: `https://app.supabase.com/project/_/settings/functions`
2. Click "Edge Function Secrets"
3. Add each secret:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`

**Note:** `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are automatically available in Edge Functions.

## Testing Locally

```bash
# Run the edge function locally
supabase functions serve webhook-handler --env-file .env

# Test with curl
curl -X POST http://localhost:54321/functions/v1/webhook-handler \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Twilio-Signature: test_signature" \
  -d "From=whatsapp:+1234567890&Body=Hello&To=whatsapp:+0987654321"
```

## Security Notes

- ⚠️ **Never commit `.env` files to git**
- ✅ The `.gitignore` file is configured to exclude `.env` files
- ✅ Always use `.env.example` as a template (without real credentials)
- ✅ Rotate your Twilio Auth Token if it's ever exposed
