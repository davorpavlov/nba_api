# 🚀 Coolify Quick Start - 5 Minuta do Production

**NBA Props Analysis API + N8N Integration**

---

## ✅ Korak 1: Pripremi Kod (2 min)

```bash
# 1. Clone ili pull latest kod
git pull origin main

# 2. Kreiraj .env fajl (opciono, Coolify može bez ovoga)
cp .env.example .env

# 3. Provjeri da li su svi fajlovi tu
ls -la
# Trebalo bi da vidiš:
# - Dockerfile ✅
# - docker-compose.yml ✅
# - api_server.py ✅
# - requirements.txt ✅
# - analysis/ folder ✅

# 4. Commit i push (ako još nisi)
git add .
git commit -m "feat: Add Coolify deployment"
git push origin main
```

---

## ✅ Korak 2: Coolify Setup (3 min)

### A) Otvori Coolify Dashboard

Idi na: `https://tvoj-coolify-server.com`

### B) Kreiraj Novu Aplikaciju

1. Klikni **"+ New"** → **"Resource"**
2. Odaberi **"Application"**
3. Odaberi **"Public Repository"** ili **"Private Repository"**

### C) Unesi Git Info

```
Repository URL: https://github.com/davorpavlov/nba_api.git
Branch: main
```

(ili tvoj fork/branch)

### D) Konfiguriši Build

```
Build Pack: Dockerfile
Dockerfile Location: ./Dockerfile
Base Directory: /
Port: 5000
```

### E) Dodaj Environment Variables

Klikni **"Environment Variables"** i dodaj:

| Ime | Vrijednost |
|-----|------------|
| `NBA_SEASON` | `2024-25` |
| `MIN_CONFIDENCE` | `0.65` |
| `TOP_N` | `10` |
| `PORT` | `5000` |
| `DEBUG` | `False` |

### F) Konfiguriši Domain (Opciono)

```
Domain: nba-api.tvoj-domain.com
```

Ili koristi Coolify auto-generated domain (npr. `abc123.coolify.app`)

### G) Deploy!

1. Klikni **"Deploy"**
2. Prati logs (build može trajati 2-3 min)
3. Čekaj **"✅ Healthy"** status

---

## ✅ Korak 3: Test API (30 sec)

```bash
# Zamijeni sa tvojim domenom
API_URL="https://nba-api.tvoj-domain.com"

# 1. Health check
curl $API_URL/health

# Output:
# {
#   "status": "healthy",
#   "timestamp": "2024-11-09T20:00:00",
#   "season": "2024-25",
#   "service": "nba-props-analysis"
# }

# 2. API info
curl $API_URL/

# 3. Dnevna analiza
curl "$API_URL/api/daily-analysis?min_confidence=0.70&top_n=5"

# 4. Današnje utakmice
curl $API_URL/api/todays-games
```

✅ Ako sve ovo radi → **API je live!** 🎉

---

## ✅ Korak 4: N8N Integracija (5 min)

### Metod A: Import Ready Workflow

1. Otvori N8N
2. Klikni **"+"** → **"Import from File"**
3. Upload: `n8n-workflow.json`
4. Edituj **"Fetch NBA Analysis"** node:
   - URL: `https://tvoj-nba-api-domain.com/api/daily-analysis`
5. Setup Google Sheets credentials (opciono)
6. Setup Telegram credentials (opciono)
7. **Activate workflow**

### Metod B: Manual Setup

#### Node 1: Cron Trigger
```
Name: Daily Trigger
Type: Schedule Trigger
Cron: 0 8 * * * (svaki dan u 8:00)
```

#### Node 2: HTTP Request
```
Name: NBA Analysis
Type: HTTP Request
Method: GET
URL: https://tvoj-nba-api-domain.com/api/daily-analysis
Query Parameters:
  - min_confidence: 0.70
  - top_n: 5
  - prop_types: points,rebounds,assists
Timeout: 120000 ms
```

#### Node 3: Code (Filter)
```javascript
// Filter samo STRONG picks
const results = items[0].json.results || [];

const filtered = results.filter(r =>
  r.recommendation.includes('STRONG')
);

return filtered.map(r => ({ json: r }));
```

#### Node 4: Google Sheets (Opciono)
```
Operation: Append
Spreadsheet: tvoj-sheet-id
Sheet: Sheet1
Columns:
  - Date: {{ $json.timestamp }}
  - Player: {{ $json.player_name }}
  - Prop: {{ $json.prop_type }}
  - Line: {{ $json.prop_line }}
  - Projected: {{ $json.projected_value }}
  - Confidence: {{ $json.confidence_score }}
  - Recommendation: {{ $json.recommendation }}
```

#### Node 5: Telegram (Opciono)
```
Chat ID: tvoj-chat-id
Message:
🏀 NBA Props Alert

{{ $json.player_name }} - {{ $json.prop_type }}
📊 Line: {{ $json.prop_line }}
📈 Projected: {{ $json.projected_value }}
💰 Edge: {{ $json.edge }} ({{ $json.edge_pct }}%)

✅ {{ $json.recommendation }}
🎯 Confidence: {{ $json.confidence_score }}%
```

---

## ✅ Korak 5: Verifikuj Sve Radi (2 min)

### A) Test Manual Execution u N8N

1. Otvori workflow
2. Klikni **"Execute Workflow"**
3. Provjeri da li rezultati stižu

### B) Provjeri Logs u Coolify

1. Coolify dashboard → tvoja aplikacija
2. **"Logs"** tab
3. Trebalo bi da vidiš:
```
INFO - NBA Analysis API initialized for season 2024-25
INFO - Daily analysis request: prop_types=['points'], min_confidence=0.70, top_n=5
INFO - Analysis complete: 10 results
```

### C) Test Full Flow

1. Triggeriraj N8N workflow manually
2. Provjeri Google Sheets (trebalo bi da ima nove redove)
3. Provjeri Telegram (trebalo bi da dobiješ notifikaciju)

---

## 🎯 Gotovo! Sada imaš:

✅ **NBA Props Analysis API** deployovan na Coolify
✅ **Automatic health checks** (svaki 30s)
✅ **Auto-restart** ako crash-a
✅ **N8N workflow** koji se izvršava svaki dan u 8:00
✅ **Google Sheets tracking** (opciono)
✅ **Telegram notifikacije** (opciono)

---

## 📊 Šta Dalje?

### 1. Trackaj Performance

Coolify → Application → **Metrics**:
- CPU usage
- Memory usage
- Request count
- Response time

### 2. Setup Alerts

Coolify → Application → **Notifications**:
- Email alerts za downtime
- Slack/Discord webhooks

### 3. Scale Up (kada treba)

Coolify → Application → **Settings** → **Resources**:
- CPU: 1 → 2 cores
- Memory: 512MB → 1GB
- Replicas: 1 → 2 (load balancing)

### 4. Backups

```bash
# Coolify automatski backup-uje Docker volumes
# Dodatno, možeš exportati rezultate:

curl https://nba-api.tvoj-domain.com/api/daily-analysis?top_n=100 > backup_$(date +%Y%m%d).json
```

### 5. Monitoring Dashboard (Advanced)

Setup Grafana + Prometheus:
- Track API response times
- Monitor hit rates
- Alert na anomalije

---

## 🐛 Common Issues

### Issue 1: Build fails

**Check:**
```bash
# Coolify logs → Build tab
# Common fix: Clear build cache
Coolify → Application → Settings → Clear Build Cache
```

### Issue 2: Health check fails

**Fix:**
```
Coolify → Application → Health Check
Path: /health
Port: 5000
Timeout: 10s
```

### Issue 3: API timeout

**Fix:**
```
Coolify → Application → Advanced
Request Timeout: 120s
```

### Issue 4: Environment vars not loaded

**Fix:**
```
Coolify → Application → Environment Variables
Restart container after changing
```

---

## 💡 Pro Tips

### 1. Use Secrets za Sensitive Data

```bash
# Umjesto hardcoded tokens, koristi Coolify Secrets
Coolify → Secrets → Add Secret
Name: TELEGRAM_BOT_TOKEN
Value: tvoj-token

# Zatim u Environment Variables:
TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
```

### 2. Setup Staging Environment

```bash
# Kreiraj drugi deployment sa staging tagom
Branch: develop
Domain: nba-api-staging.tvoj-domain.com
```

### 3. CI/CD Auto-Deploy

```bash
# U Coolify:
Settings → Git → Auto Deploy: ON
Webhook: https://coolify.app/webhook/xyz

# U GitHub:
Settings → Webhooks → Add webhook
URL: paste Coolify webhook
```

Sad svaki git push auto-deploya! 🚀

---

## 📞 Help & Support

**Coolify Docs:** https://coolify.io/docs
**N8N Docs:** https://docs.n8n.io
**NBA API Issues:** https://github.com/davorpavlov/nba_api/issues

---

## 🎉 Congratulations!

Imaš sada **production-ready NBA Props Analysis system** sa:

- ✅ Auto-scaling
- ✅ Health monitoring
- ✅ Daily automation
- ✅ Notification alerts
- ✅ Historical tracking

**Sretno sa pickovima! 🏀💰**

---

**Vrijeme ukupno:** ~15 minuta
**Rezultat:** Production API + N8N automation
**Mjesečni trošak:** $0 (self-hosted) ili ~$5-10 (cloud hosting)
