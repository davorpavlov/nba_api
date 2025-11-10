# 🚀 Coolify Deployment Guide - NBA Props Analysis API

Kompletan vodič za deployment NBA Props Analysis API-ja na Coolify.

---

## 📋 Preduslovi

- ✅ Coolify instanca (self-hosted ili cloud)
- ✅ Git repository (GitHub, GitLab, itd.)
- ✅ Domain ili subdomain (opciono, ali preporučeno)

---

## 🎯 Metod 1: Coolify Deployment (Preporučeno)

### Korak 1: Push kod na Git

```bash
# Ako već nisi pushao
git add .
git commit -m "feat: Add Coolify deployment configuration"
git push origin main
```

### Korak 2: Kreiraj novi projekt u Coolify

1. Otvori Coolify dashboard
2. Klikni **"+ New Resource"**
3. Odaberi **"Application"**
4. Odaberi **"Docker Compose"** ili **"Dockerfile"**

### Korak 3: Konfiguriši aplikaciju

#### Git Repository
```
Repository URL: https://github.com/davorpavlov/nba_api.git
Branch: main (ili tvoj branch)
```

#### Build Configuration
```
Build Pack: Dockerfile
Dockerfile Location: ./Dockerfile
Base Directory: /
```

#### Port Configuration
```
Port: 5000
```

#### Environment Variables
Dodaj sljedeće environment varijable:

```bash
NBA_SEASON=2024-25
MIN_CONFIDENCE=0.65
TOP_N=10
PORT=5000
HOST=0.0.0.0
DEBUG=False
```

### Korak 4: Konfiguriši Domain (Opciono)

```
Domain: nba-api.tvoj-domain.com
```

Ili koristi Coolify generirani domain.

### Korak 5: Deploy

1. Klikni **"Deploy"**
2. Prati build logs
3. Čekaj da health check prođe (✅ Healthy)

### Korak 6: Test deployment

```bash
# Test health endpoint
curl https://nba-api.tvoj-domain.com/health

# Test daily analysis
curl https://nba-api.tvoj-domain.com/api/daily-analysis?min_confidence=0.70&top_n=5
```

---

## 🎯 Metod 2: Docker Compose Deployment

### Korak 1: Kreiraj .env fajl

```bash
cp .env.example .env
nano .env
```

Edituj varijable:
```bash
NBA_SEASON=2024-25
MIN_CONFIDENCE=0.65
TOP_N=10
PORT=5000
DEBUG=False
```

### Korak 2: Build i Run

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Korak 3: Verifikuj

```bash
# Health check
curl http://localhost:5000/health

# API info
curl http://localhost:5000/
```

---

## 🎯 Metod 3: Standalone Docker

```bash
# Build
docker build -t nba-props-analysis .

# Run
docker run -d \
  --name nba-api \
  -p 5000:5000 \
  -e NBA_SEASON=2024-25 \
  -e MIN_CONFIDENCE=0.65 \
  -e TOP_N=10 \
  --restart unless-stopped \
  nba-props-analysis

# Check logs
docker logs -f nba-api
```

---

## 📡 API Endpoints

Nakon deployment-a, dostupni su sljedeći endpointovi:

### Health Check
```bash
GET /health
```

### API Info
```bash
GET /
```

### Dnevna Analiza
```bash
GET /api/daily-analysis?prop_types=points,rebounds&min_confidence=0.70&top_n=5
```

### Player Analiza
```bash
POST /api/player-analysis
Content-Type: application/json

{
  "player_name": "LeBron James",
  "opponent_team_name": "Golden State Warriors",
  "is_home_game": true,
  "props": {
    "points": 25.5,
    "rebounds": 7.5,
    "assists": 7.5
  }
}
```

### Današnje Utakmice
```bash
GET /api/todays-games
```

### Player Search
```bash
GET /api/player-search?name=lebron
```

### Team Search
```bash
GET /api/team-search?name=lakers
```

---

## 🔗 N8N Integracija

### Setup 1: HTTP Request Node

Nakon što je API deployed na Coolify, koristi ga direktno u N8N-u:

```
Node: HTTP Request
Method: GET
URL: https://nba-api.tvoj-domain.com/api/daily-analysis
Query Parameters:
  - min_confidence: 0.70
  - top_n: 5
  - prop_types: points,rebounds,assists
```

### Setup 2: Kompletan Workflow

```
┌──────────────┐
│ Cron Node    │ → Svaki dan u 8:00
│ 0 8 * * *    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ HTTP Request │ → GET /api/daily-analysis
│ (NBA API)    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Function     │ → Filter results
│ (Filter)     │   confidence >= 0.75
└──────┬───────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐  ┌──────────────┐
│ Google Sheet │  │ Telegram     │
│ (Append)     │  │ (Send)       │
└──────────────┘  └──────────────┘
```

### N8N JSON Workflow (Import Ready)

```json
{
  "nodes": [
    {
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "cronExpression",
              "expression": "0 8 * * *"
            }
          ]
        }
      },
      "name": "Daily Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300]
    },
    {
      "parameters": {
        "url": "https://nba-api.tvoj-domain.com/api/daily-analysis",
        "queryParameters": {
          "parameters": [
            {
              "name": "min_confidence",
              "value": "0.70"
            },
            {
              "name": "top_n",
              "value": "5"
            }
          ]
        },
        "options": {}
      },
      "name": "NBA Analysis",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "functionCode": "const results = items[0].json.results;\nconst filtered = results.filter(r => r.confidence_score >= 0.75);\nreturn filtered.map(r => ({ json: r }));"
      },
      "name": "Filter High Confidence",
      "type": "n8n-nodes-base.function",
      "position": [650, 300]
    }
  ],
  "connections": {
    "Daily Trigger": {
      "main": [[{"node": "NBA Analysis", "type": "main", "index": 0}]]
    },
    "NBA Analysis": {
      "main": [[{"node": "Filter High Confidence", "type": "main", "index": 0}]]
    }
  }
}
```

---

## 🔧 Troubleshooting

### Problem: Build fails

**Rješenje:**
```bash
# Provjeri Docker logs
docker-compose logs nba-api

# Rebuild sa clean cache
docker-compose build --no-cache
```

### Problem: Health check fails

**Rješenje:**
```bash
# Provjeri da li aplikacija sluša na pravom portu
docker exec -it nba-api netstat -tuln | grep 5000

# Provjeri environment varijable
docker exec -it nba-api env | grep PORT
```

### Problem: API timeout

**Rješenje:**
NBA API može biti spor. Povećaj timeout u Coolify-u:
```
Settings → Advanced → Request Timeout: 120s
```

### Problem: No games found

**Rješenje:**
Off-season ili休息 dan. Testiraj sa specifičnim player endpoint-om:
```bash
curl -X POST https://nba-api.tvoj-domain.com/api/player-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "player_name": "LeBron James",
    "opponent_team_name": "Warriors",
    "is_home_game": true,
    "props": {"points": 25.5}
  }'
```

---

## 📊 Monitoring

### Coolify Metrics

Coolify automatski prati:
- ✅ CPU usage
- ✅ Memory usage
- ✅ Network I/O
- ✅ Health checks

### Custom Monitoring

Dodaj monitoring endpoint:

```python
# U api_server.py (već implementiran)
@app.route('/metrics', methods=['GET'])
def metrics():
    return jsonify({
        'requests_total': request_count,
        'uptime': time.time() - start_time,
        'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024
    })
```

---

## 🔒 Security Best Practices

### 1. Environment Variables
NIKAD ne commitaj `.env` fajl sa secrets!

```bash
# Dodaj u .gitignore
echo ".env" >> .gitignore
```

### 2. Rate Limiting (Opciono)

Instaliraj Flask-Limiter:
```bash
pip install Flask-Limiter
```

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    default_limits=["200 per day", "50 per hour"]
)
```

### 3. HTTPS Only

U Coolify-u, omogući "Force HTTPS".

### 4. Firewall

Zatvori sve portove osim 80/443 (Coolify radi reverse proxy).

---

## 🚀 Performance Optimization

### 1. Caching

Dodaj Redis cache za API rezultate:

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

@app.route('/api/daily-analysis')
@cache.cached(timeout=3600)  # Cache 1h
def daily_analysis():
    ...
```

### 2. Gunicorn Workers

Podesi broj workera u `Dockerfile`:
```bash
CMD ["gunicorn", "--workers", "4", "--threads", "2", ...]
```

**Formula:** workers = (2 × CPU cores) + 1

### 3. Database (Opciono)

Za historical tracking, dodaj PostgreSQL:

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: nba_props
      POSTGRES_USER: nba
      POSTGRES_PASSWORD: ${DB_PASSWORD}
```

---

## 📈 Scaling

### Horizontal Scaling (Višestruke instance)

U Coolify-u:
1. Settings → Replicas → 2+
2. Load balancer automatski distribuira traffic

### Vertical Scaling (Više resursa)

U Coolify-u:
1. Settings → Resources
2. CPU: 2 cores
3. Memory: 2GB

---

## 💾 Backup & Recovery

### Backup

```bash
# Backup Docker volume (logs, output)
docker run --rm \
  -v nba_api_logs:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/nba-backup.tar.gz /data
```

### Recovery

```bash
# Restore
docker run --rm \
  -v nba_api_logs:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/nba-backup.tar.gz -C /
```

---

## 🎓 Sljedeći Koraci

1. ✅ **Deploy na Coolify** - Slijedi Metod 1
2. ✅ **Integriraj sa N8N** - Koristi HTTP Request node
3. ✅ **Setup monitoring** - Grafana + Prometheus (opciono)
4. ✅ **Dodaj rate limiting** - Flask-Limiter
5. ✅ **Implementiraj caching** - Redis
6. ✅ **Trackaj rezultate** - PostgreSQL database

---

## 📞 Support

Za probleme ili pitanja:
- GitHub Issues: https://github.com/davorpavlov/nba_api/issues
- Coolify Docs: https://coolify.io/docs
- N8N Docs: https://docs.n8n.io

---

**Happy Deploying! 🚀🏀💰**
