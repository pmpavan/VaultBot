#!/bin/bash
# Quick script to export YouTube cookies and deploy scraper worker

set -e

echo "🍪 YouTube Cookies Export & Deployment"
echo "========================================"
echo ""

# Check if yt-dlp is installed
if ! command -v yt-dlp &> /dev/null; then
    echo "❌ yt-dlp not found. Installing..."
    pip3 install yt-dlp
fi

# Export cookies from Chrome
echo "📥 Exporting cookies from Chrome..."
yt-dlp --cookies-from-browser chrome --cookies agent/cookies.txt https://www.youtube.com/watch?v=dQw4w9WgXcQ 2>&1 | grep -v "Downloading webpage" || true

if [ -f "agent/cookies.txt" ]; then
    echo "✅ Cookies exported to agent/cookies.txt"
    echo ""
    
    # Update Dockerfile.scraper to include cookies
    echo "📝 Updating Dockerfile.scraper..."
    if ! grep -q "COPY cookies.txt" agent/Dockerfile.scraper; then
        echo "" >> agent/Dockerfile.scraper
        echo "# Copy YouTube cookies for bot detection bypass" >> agent/Dockerfile.scraper
        echo "COPY cookies.txt /app/cookies.txt" >> agent/Dockerfile.scraper
        echo "✅ Dockerfile.scraper updated"
    else
        echo "ℹ️  Dockerfile.scraper already has cookies copy command"
    fi
    
    echo ""
    echo "🚀 Ready to deploy!"
    echo ""
    echo "Run: cd agent && ./deploy-scraper.sh"
    echo ""
else
    echo "❌ Failed to export cookies"
    echo ""
    echo "Manual steps:"
    echo "1. Install browser extension: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
    echo "2. Go to YouTube and sign in"
    echo "3. Click extension → Export"
    echo "4. Save as agent/cookies.txt"
    echo "5. Run: cd agent && ./deploy-scraper.sh"
fi
