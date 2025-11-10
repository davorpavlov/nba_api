#!/usr/bin/env python3
"""
Test script za validaciju tačnosti NBA props analiza
Testira analize na prošlim utakmicama gdje znamo stvarne rezultate
"""

import sys
from datetime import datetime, timedelta
from analysis import NBADataFetcher, PropsScoringModel
import pandas as pd

def test_player_props_accuracy(player_id: int, player_name: str, days_back: int = 7):
    """
    Testira tačnost analiza za igrača na prošlim utakmicama

    Args:
        player_id: NBA player ID
        player_name: Ime igrača
        days_back: Koliko dana unazad testirati
    """
    print("=" * 80)
    print(f"TESTING ACCURACY FOR: {player_name}")
    print("=" * 80)

    fetcher = NBADataFetcher()
    scorer = PropsScoringModel(fetcher)

    # Dohvati zadnjih N utakmica
    game_log = fetcher.get_player_game_log(player_id, last_n=days_back)

    if game_log.empty:
        print(f"❌ No games found for player {player_name}")
        return

    print(f"\nAnalyzing last {len(game_log)} games...\n")

    results = {
        'points': {'correct': 0, 'total': 0, 'predictions': []},
        'rebounds': {'correct': 0, 'total': 0, 'predictions': []},
        'assists': {'correct': 0, 'total': 0, 'predictions': []}
    }

    # Testiraj svaku utakmicu
    for idx, game in game_log.iterrows():
        game_date = game.get('GAME_DATE', 'Unknown')
        matchup = game.get('MATCHUP', 'Unknown')

        # Ekstraktuj team_id i opponent_team_id
        team_id = int(game['TEAM_ID'])

        # Opponent team ID - ekstraktuj iz matchupa
        # Format: "LAL vs. CHA" ili "LAL @ CHA"
        is_home = 'vs.' in matchup

        # Stvarni rezultati
        actual_pts = game['PTS']
        actual_reb = game['REB']
        actual_ast = game['AST']

        print(f"\n{'='*80}")
        print(f"Game: {matchup} on {game_date}")
        print(f"Actual Stats: {actual_pts} PTS, {actual_reb} REB, {actual_ast} AST")
        print(f"{'='*80}")

        # Test različite prop linije (standardne betting linije)
        prop_lines = {
            'points': [actual_pts - 2.5, actual_pts, actual_pts + 2.5],
            'rebounds': [actual_reb - 1.5, actual_reb, actual_reb + 1.5],
            'assists': [actual_ast - 1.5, actual_ast, actual_ast + 1.5]
        }

        for prop_type in ['points', 'rebounds', 'assists']:
            stat_map = {'points': 'PTS', 'rebounds': 'REB', 'assists': 'AST'}
            actual_value = game[stat_map[prop_type]]

            # Testiraj srednju liniju (najbliža stvarnoj vrijednosti)
            line = prop_lines[prop_type][1]

            try:
                # NAPOMENA: Ovo će koristiti SVE podatke do ove utakmice
                # Za pravi backtest trebali bi isključiti buduće podatke
                # Ali za brzu validaciju, ovo daje ideju o tome kako model radi

                print(f"\n  Testing {prop_type.upper()} line: {line}")
                print(f"  (Actual: {actual_value})")

                # Ovdje bi trebalo pozvati analizu sa podacima SAMO do tog datuma
                # Za sada samo pokazujemo koncept

                # Simuliraj projekciju baziranu na prosjeku zadnjih utakmica prije ove
                previous_games = game_log.iloc[idx+1:] if idx+1 < len(game_log) else pd.DataFrame()

                if not previous_games.empty:
                    avg_value = previous_games[stat_map[prop_type]].mean()
                    projection = avg_value

                    # Jednostavna logika: ako je projekcija iznad linije, preporuka je OVER
                    if projection > line:
                        prediction = "OVER"
                        correct = actual_value > line
                    elif projection < line:
                        prediction = "UNDER"
                        correct = actual_value < line
                    else:
                        prediction = "PUSH"
                        correct = None

                    if correct is not None:
                        results[prop_type]['total'] += 1
                        if correct:
                            results[prop_type]['correct'] += 1

                        results[prop_type]['predictions'].append({
                            'game': matchup,
                            'date': game_date,
                            'line': line,
                            'prediction': prediction,
                            'actual': actual_value,
                            'correct': correct,
                            'projection': projection
                        })

                        status = "✅ CORRECT" if correct else "❌ WRONG"
                        print(f"  Projection: {projection:.1f}")
                        print(f"  Prediction: {prediction}")
                        print(f"  Result: {status}")

            except Exception as e:
                print(f"  ⚠️  Error analyzing: {e}")

    # Prikaz ukupnih rezultata
    print("\n" + "=" * 80)
    print("ACCURACY SUMMARY")
    print("=" * 80)

    for prop_type in ['points', 'rebounds', 'assists']:
        data = results[prop_type]
        if data['total'] > 0:
            accuracy = (data['correct'] / data['total']) * 100
            print(f"\n{prop_type.upper()}:")
            print(f"  Correct: {data['correct']}/{data['total']}")
            print(f"  Accuracy: {accuracy:.1f}%")

            if accuracy >= 60:
                rating = "🟢 GOOD"
            elif accuracy >= 50:
                rating = "🟡 AVERAGE"
            else:
                rating = "🔴 NEEDS IMPROVEMENT"
            print(f"  Rating: {rating}")

    return results


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("NBA PROPS ANALYSIS - ACCURACY VALIDATION")
    print("=" * 80)

    # Test cases
    test_players = [
        (1629029, "Luka Dončić"),      # Luka
        (203081, "Damian Lillard"),    # Dame
        (2544, "LeBron James"),         # LeBron
    ]

    print("\nNOTE: This is a simplified backtest using historical game averages.")
    print("For production, you should use the full scoring model with proper")
    print("time-series validation (excluding future data).\n")

    for player_id, player_name in test_players:
        try:
            test_player_props_accuracy(player_id, player_name, days_back=5)
            print("\n")
        except Exception as e:
            print(f"Error testing {player_name}: {e}\n")

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print("\nHow to interpret results:")
    print("  60%+ accuracy = Model is performing well")
    print("  50-60% accuracy = Average (better than random)")
    print("  <50% accuracy = Model needs improvement")
    print("\nRemember: Even professional bettors aim for 55-60% accuracy!")
