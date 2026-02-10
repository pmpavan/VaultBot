# VaultBot

> Your WhatsApp Memory Prosthetic - A privacy-first smart assistant that remembers everything you save.

VaultBot is an intelligent WhatsApp bot that captures, processes, and retrieves links, videos, and images from your conversations. Designed with privacy at its core, it passively monitors DMs and only acts in groups when explicitly tagged.

## 🎯 Features

### ✅ Epic 1: The Digital Vault (Complete)
- **WhatsApp Integration**: Twilio-powered webhook ingestion
- **Privacy Gate**: DM passive capture, Group explicit tagging only
- **Job Queue System**: Asynchronous processing with atomic claiming 
- **Auto User Profiles**: Automatic creation on first interaction
- **Dead Letter Queue**: Failed job debugging and retry

### ✅ Epic 2: The Analyst (In Progress - 5/9 Stories)
- **Vision API Integration**: OpenRouter (GPT-4o/Claude) for image/video analysis
- **Universal Link Scraper**: Instagram, TikTok, YouTube, blogs, articles
- **YouTube Dual Strategy**: YouTube Data API (primary) + yt-dlp (fallback)
- **Video Processing**: Frame extraction and AI analysis
- **Image Processing**: Social media image metadata extraction
- **Article Parsing**: Text extraction from blogs and news sites
- **Deduplication**: URL-hash based deduplication system

### 🚧 Epic 3: Search & Recall (Not Started)
- Semantic search with pgvector
- Natural language queries via `/search` command
- Dynamic card generation for previews
- WhatsApp visual responses

### 🚧 Epic 4: Shared Memories (Not Started)
- Group context awareness
- Source attribution ("Saved by [Name]")
- Lazy group membership learning
- Privacy controls (`/pause`, `/resume`)

## 🏗️ Architecture

```
WhatsApp User → Twilio API → Supabase Edge Function (webhook-handler)
                                            ↓
                                      jobs table (Postgres)
                                            ↓ (polling every 5s)
              ┌─────────────────────────────┴──────────────────────────────┐
              ↓                    ↓                 ↓           ↓          ↓
       Classifier Worker    Scraper Worker   Video Worker  Image Worker  Article Worker
       (Cloud Run Job)      (Cloud Run Job)  (Cloud Run)   (Cloud Run)   (Cloud Run)
              ↓                    ↓                 ↓           ↓          ↓
       Updates content_type   Uses yt-dlp      Vision API   Vision API   Text extraction
              ↓                    ↓
                            link_metadata + user_saved_links (deduplication)
```

**Key Components:**
- **Ingestion**: Supabase Edge Functions (TypeScript/Deno)
- **Processing**: 5 specialized Python workers on Cloud Run Jobs
- **Database**: Supabase Postgres with pgvector extension
- **External APIs**: OpenRouter Vision, YouTube Data API, Proxy services

## 📋 Prerequisites

- **Python 3.9+**
- **Supabase Account**: [supabase.com](https://supabase.com)
- **Twilio Account**: WhatsApp Business API or Sandbox
- **Google Cloud Account**: For Cloud Run deployment
- **OpenRouter API Key**: For Vision API access
- **Proxy Service** (optional): For social media scraping (e.g., BrightData, Oxylabs)

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/VaultBot.git
cd VaultBot
```

### 2. Setup Supabase

```bash
# Initialize Supabase (if not already done)
supabase init
supabase start

# Apply migrations
supabase db push

# Deploy webhook handler
cd supabase/functions
supabase functions deploy webhook-handler
```

### 3. Configure Environment Variables

Create `.env` file in `agent/` directory:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=whatsapp:+14155238886

# OpenRouter (Vision API)
OPENROUTER_API_KEY=your-openrouter-key

# Optional: Proxy Configuration
PROXY_PROVIDER=brightdata  # or oxylabs
PROXY_USERNAME=your-proxy-username
PROXY_PASSWORD=your-proxy-password
PROXY_HOST=proxy.provider.com
PROXY_PORT=22225

# Optional: YouTube API
YOUTUBE_API_KEY=your-youtube-api-key

# Worker Configuration
YTDLP_TIMEOUT=30
```

### 4. Deploy Workers to Cloud Run

```bash
cd agent

# Deploy all workers
./deploy-gcp.sh

# Or deploy individually
./deploy-classifier.sh
./deploy-scraper.sh
./deploy-video.sh
./deploy-image.sh
./deploy-article.sh
```

### 5. Configure Twilio Webhook

In Twilio Console:
1. Navigate to WhatsApp Sandbox Settings (or your WhatsApp number)
2. Set **"When a message comes in"** to: `https://your-project.supabase.co/functions/v1/webhook-handler`
3. Save configuration

### 6. Test the Bot

Send a message to your Twilio WhatsApp number:
- **DM**: Just send any link or image
- **Group**: Tag the bot like `@VaultBot https://youtube.com/watch?v=...`

## 🔧 Workers

### Classifier Worker (`worker.py`)
- **Purpose**: Determines content type (link, video, image, article, text)
- **Trigger**: Polls for `status='pending' AND content_type IS NULL`
- **Output**: Updates `content_type` and `platform` fields

### Scraper Worker (`scraper_worker.py`)
- **Purpose**: Extracts metadata from social media links
- **Supports**: Instagram, TikTok, YouTube, blogs, articles
- **Strategy**: Dual-mode (YouTube API + yt-dlp fallback)
- **Output**: Populates `link_metadata` and `user_saved_links` tables

### Video Worker (`video_worker.py`)
- **Purpose**: Analyzes native WhatsApp video uploads
- **Process**: Frame extraction → Vision API analysis
- **Output**: Structured metadata (title, description, tags)

### Image Worker (`image_worker.py`)
- **Purpose**: Analyzes social media images
- **Process**: Vision API analysis of image posts
- **Output**: Image metadata and descriptions

### Article Worker (`article_worker.py`)
- **Purpose**: Extracts text from blog posts and news articles
- **Process**: HTML parsing + OpenGraph metadata extraction
- **Output**: Article title, author, published date, full text

## 🛠️ Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r agent/requirements.txt

# Run tests
pytest agent/tests/
```

### Running Workers Locally

```bash
cd agent

# Classifier worker
python -m src.worker

# Scraper worker
python -m src.scraper_worker

# Video worker
python -m src.video_worker
```

### Environment Variables Reference

See [SERVICE_SETUP.md](agent/SERVICE_SETUP.md) for detailed environment variable documentation.

## 📚 Documentation

- **[Product Requirements (PRD)](_bmad-output/planning-artifacts/prd.md)**: Feature specs and success criteria
- **[Architecture](_bmad-output/planning-artifacts/architecture.md)**: Technical design and database schema
- **[Epics & Stories](_bmad-output/planning-artifacts/epics.md)**: Detailed implementation breakdown
- **[Sprint Status](_bmad-output/implementation-artifacts/sprint-status.yaml)**: Current development progress
- **[Deployment Guide](agent/DEPLOYMENT.md)**: Cloud Run deployment instructions

## 🐛 Troubleshooting

### Common Issues

**Worker not processing jobs:**
- Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_job" --limit 50`
- Verify environment variables are set correctly
- Ensure Supabase connection is established

**Twilio webhook timeouts:**
- Edge function should return 200 OK within 2 seconds
- Check Supabase function logs in dashboard
- Verify signature validation is working

**Scraper failures:**
- Check proxy configuration if scraping social media
- YouTube API quota may be exhausted (falls back to yt-dlp)
- Review Dead Letter Queue (`dlq_jobs` table) for error details

**Database connection issues:**
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
- Check Supabase project not paused
- Ensure pgBouncer connection pooling is enabled

### Logs & Debugging

**Supabase Edge Function Logs:**
```bash
supabase functions logs webhook-handler --tail
```

**Cloud Run Worker Logs:**
```bash
gcloud run jobs executions logs <execution-name>
```

**Local Worker Debugging:**
```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG
python -m src.worker
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Supabase](https://supabase.com), [Twilio](https://twilio.com), and [Google Cloud Run](https://cloud.google.com/run)
- Vision capabilities powered by [OpenRouter](https://openrouter.ai)
- Social media scraping via [yt-dlp](https://github.com/yt-dlp/yt-dlp)
