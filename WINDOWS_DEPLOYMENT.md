# Windows Deployment Guide
## AlTi RAG Service - Production Setup

---

## Prerequisites

- **Python 3.11+** installed and in PATH
- **OpenAI API Key** (if using OpenAI as LLM provider)
- **Network access** to `api.openai.com` (if using OpenAI)
- **Disk space**: ~500MB for dependencies + space for vector DB

---

## Directory Structure

```
D:\App\rag-service\
├── main.py
├── config.py
├── requirements.txt
├── .env                    # Environment configuration
├── api/
├── graph/
├── ingestion/
├── models/
├── retrieval/
├── storage/
├── utils/
├── chroma_db/             # Vector database (auto-created)
├── logs/                  # Application logs (auto-created)
│   ├── metrics.jsonl      # Query metrics
│   └── feedback.jsonl     # User feedback
└── data/                  # Document data for ingestion
```

---

## Installation

### 1. Copy Files to Server

```powershell
# Create directory
mkdir D:\App\rag-service

# Copy files from development (via network share, SCP, etc.)
# Ensure all Python files and folders are copied
```

### 2. Create Virtual Environment

```powershell
cd D:\App\rag-service
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

Create `.env` file:

```ini
# Environment
ENVIRONMENT=production

# LLM Provider: "openai" (recommended for production)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here

# Server settings
HOST=0.0.0.0
PORT=8080
DEBUG=false

# Optional: Override default paths (usually not needed)
# WINDOWS_CHROMA_DIR=D:\App\rag-service\chroma_db
# WINDOWS_LOG_DIR=D:\App\rag-service\logs
```

### 5. Test Startup

```powershell
.\venv\Scripts\activate
python main.py
```

You should see:
```
============================================================
AlTi RAG Service - Starting...
Environment: production
============================================================
Environment validation passed
Starting server on 0.0.0.0:8080
```

### 6. Test Health Endpoint

```powershell
curl http://localhost:8080/api/v1/health
```

---

## Running as Windows Service

### Option A: NSSM (Non-Sucking Service Manager)

1. Download NSSM from https://nssm.cc/download

2. Install service:
```powershell
nssm install AlTiRAG "D:\App\rag-service\venv\Scripts\python.exe"
nssm set AlTiRAG AppParameters "D:\App\rag-service\main.py"
nssm set AlTiRAG AppDirectory "D:\App\rag-service"
nssm set AlTiRAG AppStdout "D:\App\rag-service\logs\service.log"
nssm set AlTiRAG AppStderr "D:\App\rag-service\logs\service-error.log"
```

3. Start service:
```powershell
nssm start AlTiRAG
```

### Option B: Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → "AlTi RAG Service"
3. Trigger: "When the computer starts"
4. Action: Start a program
   - Program: `D:\App\rag-service\venv\Scripts\python.exe`
   - Arguments: `main.py`
   - Start in: `D:\App\rag-service`

---

## Firewall Configuration

If dashboard and RAG service are on the same server (localhost), no firewall changes needed.

If on different servers:
```powershell
# Allow inbound on port 8080
netsh advfirewall firewall add rule name="AlTi RAG Service" dir=in action=allow protocol=tcp localport=8080
```

---

## Integration with Dashboard

The RPC Dashboard should call the RAG service at:
```
http://localhost:8080/api/v1/v2/query
```

Update the dashboard's `RAG_SERVICE_URL` constant:
```python
RAG_SERVICE_URL = "http://localhost:8080/api/v1/v2/query"
```

---

## Monitoring

### Log Files

| Log | Location | Purpose |
|-----|----------|---------|
| `metrics.jsonl` | `D:\App\rag-service\logs\` | Query performance, retrieval quality |
| `feedback.jsonl` | `D:\App\rag-service\logs\` | User feedback (thumbs up/down) |
| `service.log` | `D:\App\rag-service\logs\` | Application logs (if using NSSM) |

### Health Check

```powershell
# Quick health check
curl http://localhost:8080/api/v1/health

# Check feedback stats
curl http://localhost:8080/api/v1/feedback/stats
```

### View Recent Logs

```powershell
# Last 10 queries
Get-Content D:\App\rag-service\logs\metrics.jsonl -Tail 10

# Last 10 feedback entries
Get-Content D:\App\rag-service\logs\feedback.jsonl -Tail 10
```

---

## Troubleshooting

### Port Already in Use

```
ERROR: Port 8080 is already in use.
```

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :8080

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### OpenAI API Key Missing

```
ERROR: OPENAI_API_KEY is required when LLM_PROVIDER=openai.
```

**Solution:** Add `OPENAI_API_KEY=sk-...` to `.env` file.

### Cannot Write to Directories

```
ERROR: Cannot write to ChromaDB directory...
```

**Solution:** Check folder permissions:
```powershell
icacls D:\App\rag-service /grant Users:F /T
```

### Service Won't Start

Check logs:
```powershell
Get-Content D:\App\rag-service\logs\service-error.log -Tail 50
```

---

## Updating

1. Stop service:
```powershell
nssm stop AlTiRAG
```

2. Backup existing files:
```powershell
Copy-Item D:\App\rag-service D:\App\rag-service-backup -Recurse
```

3. Copy new files (preserve `.env` and `chroma_db/`)

4. Update dependencies:
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

5. Restart service:
```powershell
nssm start AlTiRAG
```

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Set to `production` for Windows deployment |
| `LLM_PROVIDER` | `ollama` | Use `openai` for production |
| `OPENAI_API_KEY` | (none) | Required when LLM_PROVIDER=openai |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8080` | Listen port |
| `DEBUG` | `false` | Enable debug mode (don't use in production) |

---

*Last updated: 2026-01-11*
