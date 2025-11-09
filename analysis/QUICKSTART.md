# 🚀 NBA Props Analysis - BRZI START

## 📦 Instalacija Dependencies

```bash
cd /home/user/nba_api
pip install -r analysis/requirements.txt
```

## 🎯 Primjer 1: Dnevna Analiza (Automatska)

```python
from analysis import DailyAnalysis

# Kreiraj analizu
analysis = DailyAnalysis(season='2024-25')

# Pokreni dnevnu analizu - automatski dohvata sve današnje utakmice
results = analysis.run_daily_analysis(
    prop_types=['points', 'rebounds', 'assists'],  # Koje props analizirati
    min_confidence=0.65,                            # Minimum 65% confidence
    top_n=10                                        # Top 10 pickova
)

# Prikaži rezultate
analysis.print_results(results, detailed=True)

# Exportuj u JSON
analysis.export_results(results, output_format='json')
```

**Output:**
```
================================================================================
NBA PROPS ANALYSIS - 2024-11-09 14:30
================================================================================

1. LeBron James - POINTS
   Line: 25.5 | Projected: 28.3 | Edge: +2.8 (+11.0%)
   Recommendation: OVER | Confidence: 74.2% (high)
   Factors:
     - recent_form: 82.0%
     - opponent_matchup: 75.0%
     - home_away_split: 68.0%
     - opponent_defense: 71.0%
     - pace_factor: 65.0%
     - usage_factor: 78.0%

2. Nikola Jokic - REBOUNDS
   Line: 11.5 | Projected: 13.2 | Edge: +1.7 (+14.8%)
   Recommendation: STRONG OVER | Confidence: 81.5% (very_high)
   ...
```

---

## 🎯 Primjer 2: Analiza Specifičnog Igrača

```python
from analysis import DailyAnalysis

analysis = DailyAnalysis()

# Analiziraj LeBron James protiv Warriors (home game)
results = analysis.analyze_specific_player_props(
    player_name='LeBron James',
    opponent_team_name='Golden State Warriors',
    is_home_game=True,
    props_to_analyze={
        'points': 25.5,      # Props linija za poene
        'rebounds': 7.5,     # Props linija za skokove
        'assists': 7.5       # Props linija za asistencije
    }
)

# Prikaži
analysis.print_results(results, detailed=True)
```

---

## 🎯 Primjer 3: Custom Analiza (Napredno)

```python
from analysis import NBADataFetcher, PropsScoringModel

# Setup
fetcher = NBADataFetcher(season='2024-25')
scoring_model = PropsScoringModel(fetcher)

# Pronađi igrača i timove
player = fetcher.get_player_by_name('Stephen Curry')
warriors = fetcher.get_team_by_name('Golden State Warriors')
lakers = fetcher.get_team_by_name('Los Angeles Lakers')

# Analiziraj points prop
result = scoring_model.analyze_player_prop(
    player_id=player['id'],
    player_name=player['full_name'],
    team_id=warriors['id'],
    opponent_team_id=lakers['id'],
    prop_type='points',
    prop_line=27.5,
    is_home_game=True,
    last_n_games=10
)

# Prikaži detalje
print(f"Player: {result['player_name']}")
print(f"Recommendation: {result['recommendation']}")
print(f"Confidence: {result['confidence_score']:.1%}")
print(f"Projected: {result['projected_value']:.1f} vs Line: {result['prop_line']}")
```

---

## 🎯 Primjer 4: CLI - Command Line

```bash
# Dnevna analiza sa default settings
python -m analysis.daily_analysis

# Specifične opcije
python -m analysis.daily_analysis \
  --prop-types points rebounds assists \
  --min-confidence 0.70 \
  --top-n 5 \
  --detailed

# Export u JSON
python -m analysis.daily_analysis --output json

# Export u Excel
python -m analysis.daily_analysis --output excel
```

---

## 🎯 Primjer 5: N8N Integracija

### N8N Python Function Node:

```python
import sys
sys.path.insert(0, '/home/user/nba_api')

from analysis import DailyAnalysis

# Dnevna analiza
analysis = DailyAnalysis(season='2024-25')

results = analysis.run_daily_analysis(
    prop_types=['points', 'rebounds', 'assists'],
    min_confidence=0.70,
    top_n=5
)

# Filter samo STRONG picks
strong_picks = [
    r for r in results
    if 'STRONG' in r.get('recommendation', '')
]

# Return za N8N (svaki result kao zaseban item)
return [{'json': pick} for pick in strong_picks]
```

### N8N Workflow:

```
┌─────────────────┐
│  Cron Trigger   │  Every day at 8:00 AM
│  0 8 * * *      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Python Function │  Run analysis.run_daily_analysis()
│ (Code above)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Filter          │  confidence_score >= 0.75
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Google Sheets   │  Append to "Daily Picks" sheet
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Telegram        │  Send notification
│ "🏀 5 new picks │
│  with 75%+ conf"│
└─────────────────┘
```

---

## 📊 Razumijevanje Output-a

### Confidence Score (0-1)
- **0.80+** = Very High → **STRONG OVER/UNDER**
- **0.70-0.80** = High → **OVER/UNDER**
- **0.60-0.70** = Medium → **LEAN OVER/UNDER**
- **0.50-0.60** = Low → **PASS**
- **<0.50** = Very Low → **PASS**

### Edge Calculation
```
Edge = Projected Value - Prop Line
Edge % = (Edge / Prop Line) × 100

Example:
  Projected: 28.3 PPG
  Line: 25.5
  Edge: +2.8 (+11.0%)
```

### Recommendation Logic
```
STRONG OVER:  Confidence 75%+ AND Edge 15%+
OVER:         Confidence 65%+ AND Edge 10%+
LEAN OVER:    Confidence 55%+
PASS:         Below thresholds
(Same for UNDER)
```

---

## 🔧 Konfiguracija

Edituj `analysis/config.py` za custom settings:

```python
# Promijeni težine faktora
SCORING_WEIGHTS = {
    'recent_form': 0.30,        # Povećaj recent form na 30%
    'opponent_matchup': 0.20,
    'home_away_split': 0.10,    # Smanji home/away na 10%
    'opponent_defense': 0.20,
    'pace_factor': 0.10,
    'usage_factor': 0.10,
}

# Dodaj nove prop types
PROPS_TYPES = {
    'blocks': {
        'stat_column': 'BLK',
        'min_games': 5,
        'consistency_threshold': 0.5
    },
    'steals': {
        'stat_column': 'STL',
        'min_games': 5,
        'consistency_threshold': 0.5
    }
}
```

---

## 🐛 Troubleshooting

### Import Error
```python
# Dodaj na početak skripte:
import sys
sys.path.insert(0, '/home/user/nba_api')

from analysis import DailyAnalysis
```

### API Rate Limiting
```python
# Dodaj delay između API poziva (u wrappers.py)
import time
time.sleep(0.6)  # 600ms između poziva
```

### Nema podataka za današnje utakmice
```python
# Off-season ili休息 dan - testiraj sa specifičnim igračem:
analysis.analyze_specific_player_props(
    player_name='LeBron James',
    opponent_team_name='Warriors',
    is_home_game=True,
    props_to_analyze={'points': 25.5}
)
```

---

## 📖 Više Primjera

Pokreni interaktivne primjere:
```bash
python analysis/example.py
```

Menu sa 6 različitih primjera korištenja.

---

## 📚 Dokumentacija

Potpuna dokumentacija: `analysis/README.md`

---

## 💡 Tips

1. **Trackaj rezultate** - Spremi sve pickove u bazu i analiziraj accuracy
2. **Kombinuj sa injury reports** - Prilagodi usage factor za ozlijeđene
3. **Live tracking** - Koristi Live API za in-game adjustments
4. **Parlay builder** - Kombinuj 3+ high-confidence picksa

---

**Sretno! 🏀💰**
