"""
Quick test - Testiranje osnovne funkcionalnosti
"""

import sys
sys.path.insert(0, '/home/user/nba_api/src')

def test_imports():
    """Test da li su svi moduli dostupni"""
    print("Testing imports...")
    try:
        from analysis import NBADataFetcher, PropsScoringModel, DailyAnalysis
        from analysis.config import CURRENT_SEASON, PROPS_TYPES
        from analysis.utils import calculate_average, normalize_score
        print("✅ All imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_data_fetcher():
    """Test NBADataFetcher"""
    print("\nTesting NBADataFetcher...")
    try:
        from analysis import NBADataFetcher

        fetcher = NBADataFetcher(season='2024-25')

        # Test player search
        player = fetcher.get_player_by_name('LeBron James')
        if player:
            print(f"✅ Found player: {player['full_name']} (ID: {player['id']})")
        else:
            print("⚠️  Player not found (možda ime nije točno)")

        # Test team search
        team = fetcher.get_team_by_name('Lakers')
        if team:
            print(f"✅ Found team: {team['full_name']} (ID: {team['id']})")
        else:
            print("⚠️  Team not found")

        # Test game log (možda će biti prazno izvan sezone)
        if player:
            game_log = fetcher.get_player_game_log(player['id'], last_n=5)
            print(f"✅ Game log fetched: {len(game_log)} games")

        return True

    except Exception as e:
        print(f"❌ NBADataFetcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scoring_model():
    """Test PropsScoringModel"""
    print("\nTesting PropsScoringModel...")
    try:
        from analysis import NBADataFetcher, PropsScoringModel

        fetcher = NBADataFetcher(season='2024-25')
        model = PropsScoringModel(fetcher)

        print("✅ PropsScoringModel initialized successfully!")

        # Test scoring functions
        import pandas as pd
        import numpy as np

        # Create mock data
        mock_game_log = pd.DataFrame({
            'PTS': [25, 28, 22, 30, 27],
            'REB': [7, 8, 6, 9, 7],
            'AST': [6, 7, 5, 8, 6],
            'MIN': [35, 36, 34, 37, 35]
        })

        # Test calculation
        from analysis.utils import calculate_average
        avg_pts = calculate_average(mock_game_log, 'PTS', 5)
        print(f"✅ Average calculation test: {avg_pts:.1f} PPG")

        return True

    except Exception as e:
        print(f"❌ PropsScoringModel test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_utils():
    """Test utility functions"""
    print("\nTesting Utils...")
    try:
        from analysis.utils import (
            normalize_score,
            calculate_average,
            get_confidence_label,
            get_recommendation
        )
        import pandas as pd

        # Test normalize_score
        score = normalize_score(75, 50, 100)
        assert 0 <= score <= 1, "Normalize score out of range"
        print(f"✅ normalize_score(75, 50, 100) = {score:.2f}")

        # Test calculate_average
        df = pd.DataFrame({'PTS': [20, 25, 30, 22, 28]})
        avg = calculate_average(df, 'PTS', 5)
        print(f"✅ calculate_average = {avg:.1f}")

        # Test confidence label
        label = get_confidence_label(0.75)
        print(f"✅ get_confidence_label(0.75) = {label}")

        # Test recommendation
        rec = get_recommendation(0.75, 25.0, 28.5)
        print(f"✅ get_recommendation(0.75, line=25.0, proj=28.5) = {rec}")

        return True

    except Exception as e:
        print(f"❌ Utils test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """Test config"""
    print("\nTesting Config...")
    try:
        from analysis.config import (
            CURRENT_SEASON,
            PROPS_TYPES,
            SCORING_WEIGHTS,
            CONFIDENCE_LEVELS
        )

        print(f"✅ Current season: {CURRENT_SEASON}")
        print(f"✅ Props types: {list(PROPS_TYPES.keys())}")
        print(f"✅ Scoring weights sum: {sum(SCORING_WEIGHTS.values()):.2f}")

        # Validate weights sum to 1.0
        weights_sum = sum(SCORING_WEIGHTS.values())
        if abs(weights_sum - 1.0) < 0.01:
            print("✅ Scoring weights properly normalized")
        else:
            print(f"⚠️  Scoring weights sum to {weights_sum:.2f}, should be 1.0")

        return True

    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("="*80)
    print("NBA ANALYSIS MODULE - QUICK TEST")
    print("="*80)

    tests = [
        ("Imports", test_imports),
        ("Config", test_config),
        ("Utils", test_utils),
        ("DataFetcher", test_data_fetcher),
        ("ScoringModel", test_scoring_model),
    ]

    results = []

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"❌ Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Module is ready to use.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")

    print("="*80)


if __name__ == '__main__':
    main()
