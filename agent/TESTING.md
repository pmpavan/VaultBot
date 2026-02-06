# VaultBot Classifier Worker - Testing Guide

## Quick Start

### Activate Virtual Environment
```bash
cd agent
source venv/bin/activate  # On Mac/Linux
```

### Run Tests

**Test Classification Logic Only (No Database):**
```bash
./venv/bin/python3 test_worker_local.py --mode logic --type youtube
```

**Test End-to-End (With Database):**
```bash
./venv/bin/python3 test_worker_local.py --mode e2e --type youtube
```

**Run Full Test Suite:**
```bash
./venv/bin/python3 test_worker_local.py
```

## Supported Test Types

- `youtube` - YouTube video links
- `instagram` - Instagram posts/reels
- `udemy` - Udemy course links
- `coursera` - Coursera learning paths
- `image` - Image attachments
- `video` - Video attachments
- `text` - Plain text messages

## Running the Worker

### One-Time Execution
```bash
./venv/bin/python3 src/worker.py
```

### As a Background Service
```bash
nohup ./venv/bin/python3 src/worker.py > worker.log 2>&1 &
```

## Environment Variables Required

Create `.env` file in the `agent/` directory:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890
```

## Test Results

✅ All classification tests passing:
- YouTube link detection
- Instagram link detection  
- Udemy link detection
- Image media detection
- Video media detection
- Platform identification working correctly
