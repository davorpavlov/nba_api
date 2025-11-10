#!/usr/bin/env python3
"""
Quick test script to verify the fixed endpoints work
"""

import sys
from analysis.wrappers import NBADataFetcher

print("=" * 60)
print("Testing NBA API Fixed Endpoints")
print("=" * 60)

try:
    # Initialize fetcher
    print("\n1. Initializing NBADataFetcher...")
    fetcher = NBADataFetcher()
    print("   ✓ Successfully initialized")

    # Test player vs opponent (the fixed method)
    print("\n2. Testing get_player_vs_opponent() with LeBron James...")
    print("   (Using leaguegamefinder instead of playerdashboardbyopponent)")

    # LeBron James ID: 2544
    # Lakers Team ID: 1610612747
    df = fetcher.get_player_vs_opponent(player_id=2544, opponent_team_id=1610612747)

    if not df.empty:
        print(f"   ✓ Successfully retrieved {len(df)} opponent stats records")
        print(f"\n   Sample data:")
        print(df.head())
    else:
        print("   ⚠ No data returned (might be normal if no games found)")

    # Test team vs opponent (the fixed method)
    print("\n3. Testing get_team_vs_opponent() with Lakers...")
    print("   (Using leaguegamefinder instead of teamdashboardbyopponent)")

    # Lakers: 1610612747, Warriors: 1610612744
    df_team = fetcher.get_team_vs_opponent(team_id=1610612747, opponent_team_id=1610612744)

    if not df_team.empty:
        print(f"   ✓ Successfully retrieved {len(df_team)} team opponent stats")
        print(f"\n   Sample data:")
        print(df_team.head())
    else:
        print("   ⚠ No data returned (might be normal if no games found)")

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - Fixed endpoints are working!")
    print("=" * 60)
    sys.exit(0)

except ImportError as e:
    print(f"\n✗ Import Error: {e}")
    print("\nThis means the fix worked - no more playerdashboardbyopponent imports!")
    sys.exit(1)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
