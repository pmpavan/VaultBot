# VaultBot Classifier Worker - Service Setup Guide

## Option 1: macOS LaunchAgent (Recommended for Mac)

This will run the worker automatically on login and restart it if it crashes.

### Setup Steps:

1. **Copy the plist file to LaunchAgents:**
```bash
cp com.vaultbot.classifier.plist ~/Library/LaunchAgents/
```

2. **Load the service:**
```bash
launchctl load ~/Library/LaunchAgents/com.vaultbot.classifier.plist
```

3. **Start the service:**
```bash
launchctl start com.vaultbot.classifier
```

### Managing the Service:

**Check status:**
```bash
launchctl list | grep vaultbot
```

**View logs:**
```bash
tail -f logs/worker.log
tail -f logs/worker.error.log
```

**Stop the service:**
```bash
launchctl stop com.vaultbot.classifier
```

**Restart the service:**
```bash
launchctl stop com.vaultbot.classifier
launchctl start com.vaultbot.classifier
```

**Unload (disable) the service:**
```bash
launchctl unload ~/Library/LaunchAgents/com.vaultbot.classifier.plist
```

---

## Option 2: Simple Background Process

For quick testing or temporary use:

```bash
cd /Users/apple/P1/Projects/Web/VaultBot/agent
nohup ./start_worker.sh > logs/worker.log 2>&1 &
```

**Check if running:**
```bash
ps aux | grep worker.py
```

**Stop the process:**
```bash
pkill -f "worker.py"
```

---

## Option 3: Using `screen` (Terminal Session)

Useful for development/debugging:

```bash
# Start a screen session
screen -S vaultbot-worker

# Inside screen, run the worker
cd /Users/apple/P1/Projects/Web/VaultBot/agent
./start_worker.sh

# Detach from screen: Press Ctrl+A, then D

# Reattach to screen
screen -r vaultbot-worker

# Kill the screen session
screen -X -S vaultbot-worker quit
```

---

## Environment Configuration

Make sure your `.env` file in the `agent/` directory has:

```env
SUPABASE_URL=https://ixdoczhvuvqpqzcjgrcj.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-actual-service-role-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890
```

---

## Troubleshooting

**Worker not starting:**
1. Check logs: `tail -f logs/worker.error.log`
2. Verify environment variables are set correctly
3. Test manually: `./start_worker.sh`

**Worker crashes:**
1. Check error logs for Python exceptions
2. Verify database connection (Supabase credentials)
3. Check if there are pending jobs causing errors

**No jobs being processed:**
1. Verify jobs exist with `status='pending'` in database
2. Check worker is actually running: `ps aux | grep worker.py`
3. Look for errors in logs

---

## Production Deployment

For production, consider:

1. **Use a process manager** like `supervisord` or `systemd` (on Linux)
2. **Set up monitoring** and alerting for worker health
3. **Configure log rotation** to prevent disk space issues
4. **Use a proper secrets manager** instead of `.env` files
5. **Deploy on a server** (not your local machine)

---

## Quick Start (Recommended)

```bash
# 1. Create logs directory
mkdir -p logs

# 2. Copy and load LaunchAgent
cp com.vaultbot.classifier.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.vaultbot.classifier.plist

# 3. Start the service
launchctl start com.vaultbot.classifier

# 4. Verify it's running
launchctl list | grep vaultbot
tail -f logs/worker.log
```
