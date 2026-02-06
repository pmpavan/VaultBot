# Deployment Status & Next Steps

## ✅ Completed

1. **Database Migration** - Successfully applied `20260130_create_jobs_table.sql`
   - Created `jobs` table with all required fields
   - Applied to remote database: `ixdoczhvuvqpqzcjgrcj`

2. **Edge Function Deployment** - Successfully deployed `webhook-handler`
   - Deployed to: `https://ixdoczhvuvqpqzcjgrcj.supabase.co/functions/v1/webhook-handler`
   - Dashboard: https://supabase.com/dashboard/project/ixdoczhvuvqpqzcjgrcj/functions

## ⚠️ Required: Configure Twilio Secrets

Your Edge Function needs Twilio credentials to work. You have two options:

### Option 1: Via Supabase CLI (Recommended)

```bash
# Set your Twilio Account SID
supabase secrets set TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Set your Twilio Auth Token
supabase secrets set TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Verify secrets were set
supabase secrets list
```

### Option 2: Via Supabase Dashboard

1. Go to: https://supabase.com/dashboard/project/ixdoczhvuvqpqzcjgrcj/settings/functions
2. Click "Edge Function Secrets"
3. Add these secrets:
   - `TWILIO_ACCOUNT_SID` = Your Twilio Account SID
   - `TWILIO_AUTH_TOKEN` = Your Twilio Auth Token

**Get your Twilio credentials from:** https://console.twilio.com/

## 📋 Final Steps

### 1. Configure Twilio Webhook

Once secrets are set, configure your Twilio WhatsApp webhook:

1. Go to: https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox
2. Set the webhook URL to:
   ```
   https://ixdoczhvuvqpqzcjgrcj.supabase.co/functions/v1/webhook-handler
   ```
3. Set HTTP Method to: `POST`
4. Save configuration

### 2. Test the Webhook

Send a test message to your Twilio WhatsApp number:

**Test Case 1: DM Message (should be queued)**
```
Hello VaultBot!
```

**Test Case 2: Group Message without tag (should be ignored)**
```
Just chatting in the group
```

**Test Case 3: Group Message with tag (should be queued)**
```
@VaultBot save this message
```

### 3. Monitor Logs

View Edge Function logs in real-time:

```bash
supabase functions logs webhook-handler
```

Or via Dashboard:
https://supabase.com/dashboard/project/ixdoczhvuvqpqzcjgrcj/logs/edge-functions

### 4. Verify Database Inserts

Check that jobs are being created:

```sql
SELECT * FROM jobs ORDER BY created_at DESC LIMIT 10;
```

Run this in: https://supabase.com/dashboard/project/ixdoczhvuvqpqzcjgrcj/editor

## 🔍 Troubleshooting

### Webhook returns 403 Forbidden
- Check that Twilio signature validation is working
- Verify `TWILIO_AUTH_TOKEN` is set correctly in Edge Function secrets

### Webhook returns 200 but no job created
- Check Edge Function logs for errors
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are available (they should be automatic)
- Check database permissions

### Group messages not being filtered
- Verify the webhook payload includes `GroupSid` field
- Check logs to see detected `sourceType`
- May need to adjust group detection heuristic based on actual Twilio payload format

## 📊 Current Status

- ✅ Database: Ready
- ✅ Edge Function: Deployed
- ⚠️  Twilio Secrets: **Need to be configured**
- ⏳ Twilio Webhook: Not configured yet
- ⏳ Testing: Pending

**Next Action:** Configure Twilio secrets using one of the methods above.
