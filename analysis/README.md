# NBA Props Analysis & Automation

Automatska analiza NBA utakmica i player props-a za betting, sa integracijom confidence scoring modela.

## 📋 Sadržaj

- [Pregled](#pregled)
- [Instalacija](#instalacija)
- [Brzi Start](#brzi-start)
- [Korištenje](#korištenje)
- [API Wrapper Funkcije](#api-wrapper-funkcije)
- [Scoring Model](#scoring-model)
- [N8N Integracija](#n8n-integracija)
- [Konfiguracija](#konfiguracija)
- [Primjeri](#primjeri)

---

## 🎯 Pregled

Ovaj modul omogućava:

- ✅ **Automatsko preuzimanje** današnjih NBA utakmica
- ✅ **Analizu player props** (points, rebounds, assists, threes, combos)
- ✅ **Confidence scoring** (0-100%) za svaki prop
- ✅ **Multi-faktorsku analizu** (forma, opponent matchup, home/away, defense, pace, usage)
- ✅ **Preporuke** (STRONG OVER/UNDER, OVER/UNDER, LEAN, PASS)
- ✅ **Export rezultata** (JSON, CSV, Excel)
- ✅ **N8N ready** - lako integriraj u automatizaciju

---

## 📦 Instalacija

### Preduvjeti

```bash
pip install nba_api pandas numpy openpyxl
```

### Setup

```bash
cd /home/user/nba_api
python -m analysis.example  # Pokreni primjere
```

---

## 🚀 Brzi Start

### 1. Dnevna analiza

```python
from analysis import DailyAnalysis

# Kreiraj analizu
analysis = DailyAnalysis(season='2024-25')

# Pokreni dnevnu analizu
results = analysis.run_daily_analysis(
    prop_types=['points', 'rebounds', 'assists'],
    min_confidence=0.65,  # Minimum 65% confidence
    top_n=10  # Top 10 pickova
)

# Prikaži rezultate
analysis.print_results(results, detailed=True)

# Exportuj
analysis.export_results(results, output_format='json')
```

### 2. Specifični igrač

```python
from analysis import DailyAnalysis

analysis = DailyAnalysis()

results = analysis.analyze_specific_player_props(
    player_name='LeBron James',
    opponent_team_name='Golden State Warriors',
    is_home_game=True,
    props_to_analyze={
        'points': 25.5,
        'rebounds': 7.5,
        'assists': 7.5
    }
)

analysis.print_results(results, detailed=True)
```

### 3. CLI

```bash
# Dnevna analiza
python -m analysis.daily_analysis --min-confidence 0.70 --top-n 5

# Sa specifičnim props
python -m analysis.daily_analysis --prop-types points rebounds --detailed

# Export u JSON
python -m analysis.daily_analysis --output json
```

---

## 📚 API Wrapper Funkcije

### `NBADataFetcher`

Wrapper klasa za lakše preuzimanje NBA podataka.

#### Današnje utakmice

```python
from analysis import NBADataFetcher

fetcher = NBADataFetcher(season='2024-25')
games = fetcher.get_todays_games()

for game in games:
    print(f"{game['away_team']} @ {game['home_team']}")
```

#### Player Data

```python
# Pronađi igrača
player = fetcher.get_player_by_name('Nikola Jokic')

# Game log (zadnjih N utakmica)
game_log = fetcher.get_player_game_log(player['id'], last_n=10)

# Splits (Home/Away, Last N, etc.)
splits = fetcher.get_player_splits(player['id'])

# Protiv specifičnog tima
vs_lakers = fetcher.get_player_vs_opponent(player['id'], lakers_id)

# Shot chart
shots = fetcher.get_player_shot_chart(player['id'], team_id)

# Passing stats (za assists props)
passing = fetcher.get_player_passing_stats(player['id'], team_id)

# Rebounding tracking (za rebound props)
rebounds = fetcher.get_player_rebounding_stats(player['id'], team_id)
```

#### Team Data

```python
# Team splits
team_splits = fetcher.get_team_splits(team_id)

# Team vs opponent
team_vs_opp = fetcher.get_team_vs_opponent(team_id, opponent_id)

# League defensive stats
defense_stats = fetcher.get_league_team_defense_stats()

# Pace
pace = fetcher.get_pace_for_team(team_id)

# Roster
roster = fetcher.get_team_roster(team_id)
```

---

## 🧠 Scoring Model

### Kako radi?

Model analizira **6 ključnih faktora** i kombinuje ih u jedinstveni **confidence score** (0-1):

| Faktor | Težina | Što analizira |
|--------|--------|---------------|
| **Recent Form** | 25% | Zadnjih N utakmica, konzistentnost, trend |
| **Opponent Matchup** | 20% | Historijski performans protiv tima |
| **Home/Away Split** | 15% | Performance kod kuće vs u gostima |
| **Opponent Defense** | 20% | Defensive rating protivnika |
| **Pace Factor** | 10% | Tempo utakmice (brže = više stats) |
| **Usage Factor** | 10% | Minute i usage (impact ozljeda) |

### Confidence Score → Preporuka

| Confidence | Label | Preporuka |
|------------|-------|-----------|
| 80%+ | Very High | **STRONG OVER/UNDER** |
| 70-80% | High | **OVER/UNDER** |
| 60-70% | Medium | **LEAN OVER/UNDER** |
| 50-60% | Low | **PASS** |
| <50% | Very Low | **PASS** |

### Edge Kalkulacija

- **Projected Value** - baziran na weighted faktore
- **Edge** = Projected - Prop Line
- **Edge %** = (Edge / Prop Line) × 100

Preporuka zahtijeva:
- **STRONG**: 75%+ confidence + 15%+ edge
- **REGULAR**: 65%+ confidence + 10%+ edge
- **LEAN**: 55%+ confidence

### Primjer Output-a

```json
{
  "player_name": "LeBron James",
  "prop_type": "points",
  "prop_line": 25.5,
  "projected_value": 28.3,
  "edge": 2.8,
  "edge_pct": 11.0,
  "confidence_score": 0.742,
  "confidence_label": "high",
  "recommendation": "OVER",
  "factors": {
    "recent_form": 0.82,
    "opponent_matchup": 0.75,
    "home_away_split": 0.68,
    "opponent_defense": 0.71,
    "pace_factor": 0.65,
    "usage_factor": 0.78
  },
  "details": {
    "recent_form": {
      "recent_avg": 27.8,
      "consistency_pct": 70.0,
      "trend": "up"
    },
    "opponent_matchup": {
      "vs_opponent_avg": 29.2,
      "games": 8
    },
    ...
  }
}
```

---

## 🔗 N8N Integracija

### Workflow Koraci

```
┌─────────────────┐
│   Cron Trigger  │  8:00 AM svaki dan
│   (daily 8am)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HTTP Request    │  GET todays_games
│ (Python)        │  fetcher.get_todays_games()
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Loop over games │  Za svaku utakmicu
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ HTTP Request    │  analyze_player_props()
│ (Python)        │  za sve igrače
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Filter          │  confidence >= 0.70
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Sort            │  by confidence_score DESC
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Google Sheets   │  Write top picks
│ / Telegram      │  Send notifications
└─────────────────┘
```

### Python Function Node (N8N)

```python
# N8N Python Function Node

import sys
sys.path.insert(0, '/home/user/nba_api/src')

from analysis import DailyAnalysis

# Dnevna analiza
analysis = DailyAnalysis(season='2024-25')

results = analysis.run_daily_analysis(
    prop_types=['points', 'rebounds', 'assists'],
    min_confidence=0.70,
    top_n=5
)

# Return za N8N
return [{'json': result} for result in results]
```

### HTTP Request (Alternative)

Ako želiš REST API, možeš kreirati Flask/FastAPI endpoint:

```python
# api.py
from flask import Flask, jsonify
from analysis import DailyAnalysis

app = Flask(__name__)

@app.route('/api/daily-analysis', methods=['GET'])
def daily_analysis():
    analysis = DailyAnalysis()
    results = analysis.run_daily_analysis(
        min_confidence=0.70,
        top_n=10
    )
    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Zatim u N8N:
```
HTTP Request Node:
URL: http://localhost:5000/api/daily-analysis
Method: GET
```

---

## ⚙️ Konfiguracija

Edituj `config.py` za prilagođavanje:

```python
# Scoring weights
SCORING_WEIGHTS = {
    'recent_form': 0.25,
    'opponent_matchup': 0.20,
    'home_away_split': 0.15,
    'opponent_defense': 0.20,
    'pace_factor': 0.10,
    'usage_factor': 0.10,
}

# Props types
PROPS_TYPES = {
    'points': {'stat_column': 'PTS', ...},
    'rebounds': {'stat_column': 'REB', ...},
    'assists': {'stat_column': 'AST', ...},
    'threes': {'stat_column': 'FG3M', ...},
}

# Confidence thresholds
CONFIDENCE_LEVELS = {
    'very_high': 0.80,
    'high': 0.70,
    'medium': 0.60,
    'low': 0.50,
}
```

---

## 📖 Primjeri

Pokreni primjere:

```bash
python -m analysis.example
```

Dostupni primjeri:
1. Dnevna analiza svih utakmica
2. Analiza specifičnog igrača
3. Custom analiza sa wrappers
4. Direktno korištenje scoring modela
5. Današnje utakmice
6. Player vs opponent

---

## 📊 Struktura Projekta

```
analysis/
├── __init__.py              # Package init
├── config.py                # Konfiguracija
├── utils.py                 # Helper funkcije
├── wrappers.py              # NBA API wrappers
├── scoring_model.py         # Scoring model
├── daily_analysis.py        # Glavna skripta
├── example.py               # Primjeri
└── README.md                # Ova dokumentacija

output/                      # Auto-kreirani folder za rezultate
└── nba_props_analysis_*.json
```

---

## 🎓 Dodatni Resursi

### Što još trebaš (izvan NBA API):

1. **Injury Reports** - RotoWire, ESPN API
2. **Betting Lines** - The Odds API, Bet365 scraping
3. **Starting Lineups** - RotoWire, FantasyLabs
4. **Advanced Stats** - Cleaning the Glass, BBall Index

### Preporučeni Tools za Stack:

- **N8N** - Automation workflow
- **PostgreSQL** - Historical data storage
- **Google Sheets** - Output & tracking
- **Telegram/Discord** - Notifications
- **Grafana** - Dashboard & metrics

---

## 🔥 Tips & Best Practices

### 1. Kombinuj sa vanjskim izvorima

```python
# Dohvati injury report (eksterni API)
injuries = get_injury_report()  # Tvoj custom API

# Prilagodi analizu
if 'Anthony Davis' in injuries:
    # LeBron će imati veći usage
    lebron_props_boost = True
```

### 2. Trackaj rezultate

```python
# Spremi rezultate u bazu
results = analysis.run_daily_analysis()

for result in results:
    db.insert({
        'date': today,
        'player': result['player_name'],
        'prop': result['prop_type'],
        'line': result['prop_line'],
        'recommendation': result['recommendation'],
        'confidence': result['confidence_score']
    })

# Kasnije, analiziraj accuracy
success_rate = calculate_hit_rate(db.get_historical())
```

### 3. Live Adjustments

```python
# Koristi Live API za in-game tracking
from nba_api.live.nba.endpoints import boxscore

live_box = boxscore.BoxScore(game_id='0022400123')
# Monitor real-time stats i adjust props lines
```

### 4. Kombiniraj više props

```python
# Parlay builder
high_confidence_props = [
    r for r in results
    if r['confidence_score'] >= 0.75
]

# Kreiraj 3-leg parlay
if len(high_confidence_props) >= 3:
    parlay = high_confidence_props[:3]
    combined_odds = calculate_parlay_odds(parlay)
```

---

## 🐛 Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from analysis import DailyAnalysis
analysis = DailyAnalysis()
```

---

## 📝 License

MIT License - koristi slobodno!

---

## 🤝 Contributing

Pull requests are welcome! Za major promjene, molim otvori issue prvo.

---

## 📧 Support

Za pitanja i podršku, otvori issue na GitHub-u.

---

**Sretno sa pickovima! 🏀💰**
