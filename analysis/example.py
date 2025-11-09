"""
Primjeri korištenja NBA Analysis modula
"""

import sys
sys.path.insert(0, '/home/user/nba_api/src')

from analysis import NBADataFetcher, PropsScoringModel, DailyAnalysis
from analysis.config import CURRENT_SEASON


def example_1_daily_analysis():
    """
    Primjer 1: Potpuna dnevna analiza svih utakmica
    """
    print("\n" + "="*80)
    print("PRIMJER 1: Dnevna analiza svih utakmica")
    print("="*80)

    # Kreiraj analizu
    analysis = DailyAnalysis(season=CURRENT_SEASON)

    # Pokreni analizu
    results = analysis.run_daily_analysis(
        prop_types=['points', 'rebounds', 'assists'],  # Analiziraj ove props
        min_confidence=0.65,  # Minimum 65% confidence
        top_n=10  # Top 10 pickova
    )

    # Prikaži rezultate
    analysis.print_results(results, detailed=True)

    # Exportuj u JSON
    filepath = analysis.export_results(results, output_format='json')
    print(f"\nRezultati exportovani u: {filepath}")


def example_2_specific_player():
    """
    Primjer 2: Analiza specifičnog igrača
    """
    print("\n" + "="*80)
    print("PRIMJER 2: Analiza specifičnog igrača - LeBron James")
    print("="*80)

    analysis = DailyAnalysis(season=CURRENT_SEASON)

    # Analiziraj LeBron James protiv Warriors, home game
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

    # Prikaži rezultate
    analysis.print_results(results, detailed=True)


def example_3_custom_analysis():
    """
    Primjer 3: Custom analiza sa wrapper funkcijama
    """
    print("\n" + "="*80)
    print("PRIMJER 3: Custom analiza koristeći wrappers direktno")
    print("="*80)

    # Kreiraj data fetcher
    fetcher = NBADataFetcher(season=CURRENT_SEASON)

    # Pronađi igrača
    player = fetcher.get_player_by_name('Nikola Jokic')
    if not player:
        print("Igrač nije pronađen")
        return

    print(f"\nIgrač: {player['full_name']} (ID: {player['id']})")

    # Dohvati game log
    game_log = fetcher.get_player_game_log(player['id'], last_n=10)

    if not game_log.empty:
        print(f"\nZadnjih 10 utakmica:")
        print(f"Prosjek PTS: {game_log['PTS'].mean():.1f}")
        print(f"Prosjek REB: {game_log['REB'].mean():.1f}")
        print(f"Prosjek AST: {game_log['AST'].mean():.1f}")

    # Dohvati splits
    splits = fetcher.get_player_splits(player['id'])

    if 'location' in splits and not splits['location'].empty:
        print(f"\nHome/Away Splits:")
        location_df = splits['location']
        for _, row in location_df.iterrows():
            loc = row['GROUP_VALUE']
            pts = row.get('PTS', 0)
            games = row.get('GP', 0)
            print(f"  {loc}: {pts:.1f} PPG ({games} utakmica)")


def example_4_scoring_model():
    """
    Primjer 4: Direktno korištenje scoring modela
    """
    print("\n" + "="*80)
    print("PRIMJER 4: Direktno korištenje scoring modela")
    print("="*80)

    # Setup
    fetcher = NBADataFetcher(season=CURRENT_SEASON)
    scoring_model = PropsScoringModel(fetcher)

    # Pronađi igrača i timove
    player = fetcher.get_player_by_name('Stephen Curry')
    warriors = fetcher.get_team_by_name('Golden State Warriors')
    lakers = fetcher.get_team_by_name('Los Angeles Lakers')

    if not player or not warriors or not lakers:
        print("Podaci nisu pronađeni")
        return

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

    # Prikaži rezultat
    print(f"\nPlayer: {result['player_name']}")
    print(f"Prop: {result['prop_type'].upper()} - Line: {result['prop_line']}")
    print(f"Projected: {result['projected_value']:.1f}")
    print(f"Edge: {result['edge']:+.1f} ({result['edge_pct']:+.1f}%)")
    print(f"Confidence: {result['confidence_score']:.1%} ({result['confidence_label']})")
    print(f"Recommendation: {result['recommendation']}")

    print(f"\nFactor Breakdown:")
    for factor, score in result['factors'].items():
        print(f"  {factor}: {score:.1%}")

    print(f"\nDetails:")
    import json
    print(json.dumps(result['details'], indent=2))


def example_5_todays_games():
    """
    Primjer 5: Dohvati današnje utakmice
    """
    print("\n" + "="*80)
    print("PRIMJER 5: Današnje utakmice")
    print("="*80)

    fetcher = NBADataFetcher(season=CURRENT_SEASON)

    games = fetcher.get_todays_games()

    if not games:
        print("Nema utakmica danas")
        return

    print(f"\nPronađeno {len(games)} utakmica:\n")

    for i, game in enumerate(games, 1):
        print(f"{i}. {game['away_team']} @ {game['home_team']}")
        print(f"   Status: {game['status_text']}")
        if game['status'] != 1:  # Ako nije pre-game
            print(f"   Score: {game['away_score']} - {game['home_score']}")
        print()


def example_6_player_vs_opponent():
    """
    Primjer 6: Player vs specifični protivnik
    """
    print("\n" + "="*80)
    print("PRIMJER 6: Player protiv specifičnog tima")
    print("="*80)

    fetcher = NBADataFetcher(season=CURRENT_SEASON)

    player = fetcher.get_player_by_name('Luka Doncic')
    lakers = fetcher.get_team_by_name('Los Angeles Lakers')

    if not player or not lakers:
        print("Podaci nisu pronađeni")
        return

    vs_opponent = fetcher.get_player_vs_opponent(player['id'], lakers['id'])

    if not vs_opponent.empty:
        print(f"\n{player['full_name']} vs {lakers['full_name']}:")
        row = vs_opponent.iloc[0]
        print(f"  Utakmica: {row.get('GP', 0)}")
        print(f"  PPG: {row.get('PTS', 0):.1f}")
        print(f"  RPG: {row.get('REB', 0):.1f}")
        print(f"  APG: {row.get('AST', 0):.1f}")
        print(f"  FG%: {row.get('FG_PCT', 0)*100:.1f}%")
    else:
        print("Nema historijskih podataka")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Pokreni sve primjere"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                   NBA PROPS ANALYSIS - PRIMJERI                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")

    examples = {
        '1': ('Dnevna analiza svih utakmica', example_1_daily_analysis),
        '2': ('Analiza specifičnog igrača', example_2_specific_player),
        '3': ('Custom analiza sa wrappers', example_3_custom_analysis),
        '4': ('Direktno korištenje scoring modela', example_4_scoring_model),
        '5': ('Današnje utakmice', example_5_todays_games),
        '6': ('Player vs opponent', example_6_player_vs_opponent),
    }

    print("\nDostupni primjeri:")
    for key, (desc, _) in examples.items():
        print(f"  {key}. {desc}")

    print("\n  0. Pokreni sve primjere")
    print("  q. Izlaz")

    choice = input("\nOdaberi primjer: ").strip()

    if choice == 'q':
        return

    if choice == '0':
        for _, (desc, func) in examples.items():
            try:
                func()
            except Exception as e:
                print(f"\nError u primjeru '{desc}': {e}")
                import traceback
                traceback.print_exc()
    elif choice in examples:
        _, func = examples[choice]
        try:
            func()
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Nevažeći izbor")


if __name__ == '__main__':
    main()
