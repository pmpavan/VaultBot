# YouTube Cookies Setup Guide

## Why Cookies Are Needed

YouTube detects yt-dlp as a bot and blocks requests with:
```
ERROR: Sign in to confirm you're not a bot
```

Cookies from an authenticated browser session bypass this detection.

## How to Export Cookies

### Option 1: Using Browser Extension (Recommended)

1. **Install Extension:**
   - Chrome: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Export Cookies:**
   - Open YouTube in your browser
   - Sign in to your Google account
   - Click the extension icon
   - Click "Export" or "Download"
   - Save as `cookies.txt`

### Option 2: Using yt-dlp (Alternative)

```bash
# Export cookies from Chrome
yt-dlp --cookies-from-browser chrome --cookies cookies.txt https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Export cookies from Firefox
yt-dlp --cookies-from-browser firefox --cookies cookies.txt https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Deployment to Cloud Run

### Local Testing

1. Place `cookies.txt` in project root
2. Update `.env`:
   ```
   YOUTUBE_COOKIES_FILE=./cookies.txt
   ```
3. Test locally:
   ```bash
   python3 scripts/test_scraper_integration.py
   ```

### Production Deployment

**Option A: Mount as Secret (Recommended)**

1. Create secret in Google Cloud:
   ```bash
   gcloud secrets create youtube-cookies \
     --data-file=cookies.txt \
     --project=vaultbot-486713
   ```

2. Update `deploy-scraper.sh` to mount secret:
   ```bash
   --set-secrets=/app/cookies.txt=youtube-cookies:latest
   ```

**Option B: Bake into Docker Image (Simple)**

1. Copy cookies.txt to agent directory
2. Update `Dockerfile.scraper`:
   ```dockerfile
   COPY cookies.txt /app/cookies.txt
   ```
3. Add to `.dockerignore` exception:
   ```
   !cookies.txt
   ```

## Cookie Expiration

- **Lifespan:** ~6 months (Google session cookies)
- **Refresh:** Re-export when you see bot detection errors
- **Monitoring:** Check Cloud Run logs for "No cookies file found" warnings

## Security Notes

- ⚠️ **Never commit cookies.txt to git** (already in .gitignore)
- ⚠️ Cookies contain authentication tokens - treat as secrets
- ✅ Use Google Cloud Secrets Manager for production
- ✅ Rotate cookies periodically

## Troubleshooting

**Still getting bot detection?**
1. Verify cookies.txt format (Netscape HTTP Cookie File)
2. Check cookies are from youtube.com domain
3. Ensure cookies haven't expired
4. Try re-exporting from a fresh browser session

**Cookies not loading?**
- Check file path in logs: `Using cookies from /app/cookies.txt`
- Verify file exists in container: `docker exec <container> ls -la /app/cookies.txt`
