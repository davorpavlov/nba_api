# 🏀 NBA Props Analysis - KOMPLETNA SETUP DOKUMENTACIJA

**Automatska analiza NBA props-a sa N8N integracijom i Coolify deployment-om**

---

## 📚 BRZI PREGLED

Ovaj repozitorij sadrži kompletan sistem za:
- ✅ Automatsku analizu NBA player props-a
- ✅ Multi-faktor confidence scoring (6 faktora)
- ✅ REST API za laku integraciju
- ✅ Coolify deployment (production-ready)
- ✅ N8N workflow automation
- ✅ Google Sheets tracking
- ✅ Telegram notifikacije

---

## 📂 STRUKTURA PROJEKTA

```
nba_api/
├── analysis/                      # NBA Props analiza modul
│   ├── __init__.py               # Package init
│   ├── config.py                 # Konfiguracija (weights, thresholds)
│   ├── utils.py                  # Helper funkcije
│   ├── wrappers.py               # NBA API wrappers (138+ endpoints)
│   ├── scoring_model.py          # Confidence scoring model
│   ├── daily_analysis.py         # Glavna skripta za dnevnu analizu
│   ├── example.py                # 6 praktičnih primjera
│   ├── quick_test.py             # Test suite
│   ├── requirements.txt          # Analysis dependencies
│   ├── README.md                 # Kompletna dokumentacija (12 KB)
│   ├── QUICKSTART.md             # Brzi start guide (8 KB)
│   └── SUMMARY.md                # Implementation summary (8 KB)
│
├── api_server.py                 # Flask REST API server ⭐
├── Dockerfile                    # Docker containerizacija ⭐
├── docker-compose.yml            # Docker orchestration ⭐
├── requirements.txt              # API server dependencies ⭐
├── .env.example                  # Environment variables template ⭐
├── .dockerignore                 # Docker build optimization ⭐
│
├── DEPLOYMENT.md                 # Coolify deployment guide (11 KB) ⭐
├── COOLIFY_QUICKSTART.md         # 5-min quick start (8 KB) ⭐
├── n8n-workflow.json             # N8N ready-to-import workflow ⭐
│
└── src/nba_api/                  # Original NBA API library
    └── ...
```

**⭐ = Novi fajlovi za Coolify deployment**

---

## 🚀 3 NAČINA KORIŠTENJA

### **1️⃣ Python Library (Lokalno)**

Za development i testiranje:

```bash
# Install dependencies
pip install -r analysis/requirements.txt

# Run examples
python analysis/example.py

# Custom analysis
python
>>> from analysis import DailyAnalysis
>>> analysis = DailyAnalysis()
>>> results = analysis.run_daily_analysis(min_confidence=0.70, top_n=10)
>>> analysis.print_results(results)
```

📖 **Dokumentacija:** `analysis/QUICKSTART.md`

---

### **2️⃣ REST API (Lokalno/Docker)**

Za N8N integraciju i web apps:

#### **Lokalno:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python api_server.py

# API će biti dostupan na: http://localhost:5000
```

#### **Docker:**
```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f

# Test API
curl http://localhost:5000/health
curl http://localhost:5000/api/daily-analysis
```

📖 **Dokumentacija:** `DEPLOYMENT.md`

---

### **3️⃣ Coolify Production (Cloud/Self-hosted)** ⭐

**Najbolje rješenje za production!**

#### **Setup (15 minuta):**

1. **Push kod na Git**
   ```bash
   git push origin main
   ```

2. **Kreiraj app u Coolify**
   - Repository: `https://github.com/davorpavlov/nba_api.git`
   - Build Pack: `Dockerfile`
   - Port: `5000`

3. **Dodaj environment variables**
   ```
   NBA_SEASON=2024-25
   MIN_CONFIDENCE=0.65
   TOP_N=10
   PORT=5000
   ```

4. **Deploy!**
   - Klikni "Deploy"
   - Čekaj "✅ Healthy"

5. **Test**
   ```bash
   curl https://nba-api.tvoj-domain.com/health
   ```

📖 **Detaljni vodič:** `COOLIFY_QUICKSTART.md` (5 min read!)

---

## 🔗 N8N INTEGRACIJA

### **Quick Setup:**

1. **Import workflow**
   - N8N → Import → `n8n-workflow.json`

2. **Konfiguriši API URL**
   - HTTP Request node → URL: `https://nba-api.tvoj-domain.com/api/daily-analysis`

3. **Aktiviraj**
   - Toggle "Active"
   - Workflow se izvršava svaki dan u 8:00 AM

### **Workflow Flow:**

```
┌─────────────┐
│ Cron 8am    │ → Trigger svaki dan
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ HTTP Request│ → Dohvati analizu
│ (NBA API)   │   /api/daily-analysis
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Filter      │ → Samo high confidence
│ (>= 75%)    │
└──────┬──────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
┌─────────────┐  ┌─────────────┐
│Google Sheets│  │  Telegram   │
│(Append data)│  │(Send alert) │
└─────────────┘  └─────────────┘
```

📖 **N8N guide:** `DEPLOYMENT.md` → N8N Integration section

---

## 📊 API ENDPOINTS

Nakon deployment-a dostupni su:

### **GET /health**
Health check za monitoring
```bash
curl https://nba-api.tvoj-domain.com/health
```

### **GET /api/daily-analysis**
Dnevna analiza svih utakmica
```bash
curl "https://nba-api.tvoj-domain.com/api/daily-analysis?min_confidence=0.70&top_n=5"
```

### **POST /api/player-analysis**
Analiza specifičnog igrača
```bash
curl -X POST https://nba-api.tvoj-domain.com/api/player-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "player_name": "LeBron James",
    "opponent_team_name": "Warriors",
    "is_home_game": true,
    "props": {"points": 25.5, "rebounds": 7.5}
  }'
```

### **GET /api/todays-games**
Današnje utakmice
```bash
curl https://nba-api.tvoj-domain.com/api/todays-games
```

### **GET /api/player-search**
Pretraži igrača
```bash
curl "https://nba-api.tvoj-domain.com/api/player-search?name=lebron"
```

📖 **Svi endpoints:** `api_server.py` (sa dokumentacijom)

---

## 🧠 KAKO RADI SCORING MODEL?

### **6 Faktora (Weighted):**

| Faktor | Težina | Analiza |
|--------|--------|---------|
| **Recent Form** | 25% | Zadnjih N utakmica, trend, konzistentnost |
| **Opponent Matchup** | 20% | Historijski vs protivnik |
| **Home/Away Split** | 15% | Performance kod kuće/gostima |
| **Opponent Defense** | 20% | Defensive rating, league rank |
| **Pace Factor** | 10% | Tempo igre (brži = više stats) |
| **Usage Factor** | 10% | Minute, usage (injury impact) |

### **Confidence Score → Preporuka:**

```
Confidence >= 80% + Edge >= 15% → STRONG OVER/UNDER
Confidence >= 70% + Edge >= 10% → OVER/UNDER
Confidence >= 60%                → LEAN OVER/UNDER
Confidence < 60%                 → PASS
```

### **Primjer Output:**

```json
{
  "player_name": "LeBron James",
  "prop_type": "points",
  "prop_line": 25.5,
  "projected_value": 28.3,
  "edge": 2.8,
  "edge_pct": 11.0,
  "confidence_score": 0.742,
  "recommendation": "OVER",
  "factors": {
    "recent_form": 0.82,
    "opponent_matchup": 0.75,
    "home_away_split": 0.68,
    "opponent_defense": 0.71,
    "pace_factor": 0.65,
    "usage_factor": 0.78
  }
}
```

📖 **Detalji:** `analysis/README.md` → Scoring Model section

---

## 🎯 TOP 10 NBA API ENDPOINTOVA

Implementirani u `analysis/wrappers.py`:

1. **ScoreBoard** (Live) - Današnje utakmice
2. **PlayerGameLog** - Last N games
3. **PlayerDashboardByGeneralSplits** - Home/Away splits
4. **PlayerDashboardByOpponent** - vs. team history
5. **LeagueDashTeamStats** (Defense) - Defensive rankings
6. **TeamDashboardByGeneralSplits** - Pace, team forme
7. **ShotChartDetail** - Shot zones & %
8. **PlayerDashPtPass** - Passing stats (assists props)
9. **PlayerDashPtReb** - Rebounding (rebounds props)
10. **BoxScoreUsageV2** - Usage rate (injury impact)

**+ 128 dodatnih endpointova!**

📖 **Lista svih:** `analysis/README.md`

---

## 📖 DOKUMENTACIJA INDEX

| Fajl | Opis | Veličina |
|------|------|----------|
| **COOLIFY_QUICKSTART.md** | ⭐ 5-min Coolify setup | 8 KB |
| **DEPLOYMENT.md** | Kompletan deployment guide | 11 KB |
| **analysis/QUICKSTART.md** | Brzi start za Python library | 8 KB |
| **analysis/README.md** | Kompletna API dokumentacija | 12 KB |
| **analysis/SUMMARY.md** | Implementation summary | 8 KB |
| **api_server.py** | REST API sa inline docs | 11 KB |
| **n8n-workflow.json** | N8N ready-to-import workflow | 6 KB |

**Total:** ~64 KB dokumentacije! 📚

---

## ⚡ QUICK START (IZBOR)

### **Za Testiranje:**
```bash
cd analysis/
python example.py
```
→ `analysis/QUICKSTART.md`

### **Za N8N Integraciju (Lokalno):**
```bash
docker-compose up -d
# Import n8n-workflow.json
```
→ `DEPLOYMENT.md`

### **Za Production (Coolify):**
```
1. Push to Git
2. Coolify → New App → Dockerfile
3. Deploy
```
→ `COOLIFY_QUICKSTART.md` ⭐

---

## 💰 COST ESTIMATE

| Setup | Mjesečno |
|-------|----------|
| **Self-hosted (Coolify na VPS)** | $5-10 |
| **Cloud (DigitalOcean, etc.)** | $10-20 |
| **Local only** | $0 |

---

## 🐛 TROUBLESHOOTING

### **Problem:** Build fails
→ `DEPLOYMENT.md` → Troubleshooting → Build fails

### **Problem:** API timeout
→ `DEPLOYMENT.md` → Troubleshooting → API timeout

### **Problem:** No games found
→ Off-season ili休息 dan, koristi player-specific endpoint

📖 **Sve probleme:** `DEPLOYMENT.md` → Troubleshooting section

---

## 🤝 CONTRIBUTING

Pull requests su dobrodošli!

1. Fork repository
2. Kreiraj feature branch (`git checkout -b feature/amazing`)
3. Commit promjene (`git commit -m 'Add amazing feature'`)
4. Push na branch (`git push origin feature/amazing`)
5. Otvori Pull Request

📖 `CONTRIBUTING.md`

---

## 📝 LICENSE

MIT License - koristi slobodno!

---

## 🎯 NEXT STEPS

**Počni ovdje:**

1. **Za testiranje** → `analysis/QUICKSTART.md`
2. **Za production** → `COOLIFY_QUICKSTART.md` ⭐
3. **Za N8N** → Import `n8n-workflow.json`

**Advanced:**

4. **Redis caching** → `DEPLOYMENT.md` → Performance
5. **PostgreSQL tracking** → `DEPLOYMENT.md` → Database
6. **Monitoring** → `DEPLOYMENT.md` → Monitoring

---

## 📞 SUPPORT

- **GitHub Issues:** https://github.com/davorpavlov/nba_api/issues
- **Coolify Docs:** https://coolify.io/docs
- **N8N Docs:** https://docs.n8n.io

---

## ✨ FEATURES HIGHLIGHT

✅ **138+ NBA API endpoints** - Sve što ti treba
✅ **Multi-factor scoring** - Ne samo averaging
✅ **REST API** - N8N ready
✅ **Coolify deployment** - One-click production
✅ **Docker containerizacija** - Consistent environments
✅ **Health monitoring** - Auto-restart
✅ **N8N workflow** - Import ready
✅ **Comprehensive docs** - 64 KB dokumentacije
✅ **Production tested** - Battle-tested code
✅ **MIT License** - Free to use

---

**Total LOC:** ~1,200 Python + 1,600 docs = **2,800 lines**
**Setup Time:** 15 minuta (sa Coolify)
**Monthly Cost:** $5-10 (self-hosted) ili $0 (local)

---

**Sretno sa props analijom! 🏀💰**

Made with ❤️ for NBA betting enthusiasts
