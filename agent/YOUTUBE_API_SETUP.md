# YouTube Data API Setup Guide

## Quick Start

### 1. Get YouTube API Key (Free)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **YouTube Data API v3**:
   - Navigate to "APIs & Services" → "Library"
   - Search for "YouTube Data API v3"
   - Click "Enable"
4. Create API Key:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the API key

### 2. Add to Environment

**Local (.env file):**
```bash
YOUTUBE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Cloud Run (Secret):**
```bash
# Create secret
gcloud secrets create youtube-api-key \
  --data-file=- <<< "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" \
  --project=vaultbot-486713

# Update deploy-scraper.sh to use secret
--set-env-vars="YOUTUBE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

### 3. Deploy

```bash
cd agent && ./deploy-scraper.sh
```

## How It Works

**Primary Method:** YouTube Data API
- ✅ No bot detection
- ✅ No proxy needed
- ✅ Official Google API
- ✅ Reliable metadata

**Fallback:** yt-dlp (if API fails or key missing)
- Uses cookies + direct connection (no proxy)
- Only used if API unavailable

## API Quota

**Free Tier:**
- 10,000 units/day
- Each video metadata request = 1 unit
- **~10,000 YouTube links per day for free**

**Cost if exceeded:**
- $0 for first 10,000 units
- Very cheap after that

## Testing

```bash
# Test locally
export YOUTUBE_API_KEY="your-key-here"
python3 scripts/test_scraper_integration.py
```

## Advantages Over Cookies

| Feature | YouTube API | Cookies + yt-dlp |
|---------|-------------|------------------|
| Bot Detection | ✅ None | ⚠️ Possible |
| Maintenance | ✅ Zero | ⚠️ Refresh every 6mo |
| Reliability | ✅ 99.9% | ⚠️ Can break |
| Quota | ✅ 10k/day free | ✅ Unlimited |
| Setup | ✅ 5 minutes | ⚠️ Manual export |

**Recommendation:** Use YouTube API for production reliability.
