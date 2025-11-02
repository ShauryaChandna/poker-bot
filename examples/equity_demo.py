"""
Equity Calculator Demo

Demonstrates the Phase 2 simulation layer capabilities:
- Hand vs hand equity
- Hand vs range equity
- Preflop scenarios
- Postflop scenarios
- Real-time equity calculation
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pypokerengine.simulation import EquityCalculator, HandRange
from pypokerengine.simulation.monte_carlo import quick_equity_check


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def demo_hand_vs_hand():
    """Demonstrate hand vs hand equity calculations."""
    print_section("Hand vs Hand Equity")
    
    calc = EquityCalculator(default_simulations=10000)
    
    # Classic matchup: AA vs KK
    print("\n1. Classic Matchup: AA vs KK (preflop)")
    result = calc.calculate_equity("AhAd", villain_hand="KsKd")
    print(f"   Hero (AA): {result.equity:.1%} equity")
    print(f"   Villain (KK): {1-result.equity:.1%} equity")
    print(f"   Standard error: ±{result.std_error:.2%}")
    
    # Coin flip: AK vs 22
    print("\n2. Coin Flip: AK vs 22 (preflop)")
    result = calc.calculate_equity("AhKh", villain_hand="2s2d")
    print(f"   Hero (AK): {result.equity:.1%} equity")
    print(f"   Villain (22): {1-result.equity:.1%} equity")
    
    # Postflop scenario
    print("\n3. Postflop: Top pair vs overpair")
    print("   Board: Ac 7d 2s")
    result = calc.calculate_equity("AhKc", villain_hand="QsQd", board="Ac7d2s")
    print(f"   Hero (AK): {result.equity:.1%} equity")
    print(f"   Villain (QQ): {1-result.equity:.1%} equity")


def demo_hand_vs_range():
    """Demonstrate hand vs range equity calculations."""
    print_section("Hand vs Range Equity")
    
    calc = EquityCalculator(default_simulations=10000)
    
    # Premium hand vs opening range
    print("\n1. Premium Hand vs Opening Range")
    print("   Hero: AA")
    print("   Villain range: JJ+, AQs+, AKo")
    result = calc.calculate_equity("AhAd", villain_range="JJ+,AQs,AKs,AKo")
    print(f"   Hero equity: {result.equity:.1%}")
    print(f"   Simulations: {result.simulations:,}")
    
    # Medium hand vs wide range
    print("\n2. Medium Hand vs Wide Range")
    print("   Hero: KK")
    print("   Villain range: 77+, ATs+, KTs+, AJo+")
    result = calc.calculate_equity("KhKc", villain_range="77+,ATs+,KTs+,AJo+")
    print(f"   Hero equity: {result.equity:.1%}")
    
    # Postflop with range
    print("\n3. Postflop: Top pair vs continuation bet range")
    print("   Board: Kh 9d 4s")
    print("   Hero: KdQc (top pair)")
    print("   Villain range: QQ+, AK, KJ, KT")
    result = calc.calculate_equity(
        "KdQc",
        villain_range="QQ+,AK,KJ,KT",
        board="Kh9d4s"
    )
    print(f"   Hero equity: {result.equity:.1%}")


def demo_preflop_scenarios():
    """Demonstrate common preflop scenarios."""
    print_section("Common Preflop Scenarios")
    
    calc = EquityCalculator(default_simulations=10000)
    
    scenarios = [
        ("AA vs random", "AhAd", None),
        ("KK vs random", "KhKc", None),
        ("AK vs random", "AhKh", None),
        ("JJ vs random", "JhJc", None),
        ("77 vs random", "7h7c", None),
        ("22 vs random", "2h2c", None),
    ]
    
    print("\nHand            Equity vs Random")
    print("-" * 40)
    
    for desc, hand, _ in scenarios:
        result = calc.calculate_preflop_equity(hand)
        print(f"{desc:15} {result.equity:>6.1%}")


def demo_postflop_scenarios():
    """Demonstrate common postflop scenarios."""
    print_section("Common Postflop Scenarios")
    
    calc = EquityCalculator(default_simulations=10000)
    
    # Scenario 1: Made hand vs draw
    print("\n1. Made Hand vs Flush Draw")
    print("   Hero: Ah Kc (top pair)")
    print("   Villain: Qh Jh (flush draw)")
    print("   Board: Ac 7h 2h")
    result = calc.calculate_equity(
        "AhKc",
        villain_hand="QhJh",
        board="Ac7h2h"
    )
    print(f"   Hero equity: {result.equity:.1%}")
    
    # Scenario 2: Set vs overpair
    print("\n2. Set vs Overpair")
    print("   Hero: 7h 7c (set)")
    print("   Villain: Ah Ad (overpair)")
    print("   Board: Ac 7d 2s")
    result = calc.calculate_equity(
        "7h7c",
        villain_hand="AhAd",
        board="Ac7d2s"
    )
    print(f"   Hero equity: {result.equity:.1%}")
    
    # Scenario 3: Straight draw vs pair
    print("\n3. Open-Ended Straight Draw vs Pair")
    print("   Hero: Qh Jc (OESD)")
    print("   Villain: Ah Kc (top pair)")
    print("   Board: Td 9h 2s")
    result = calc.calculate_equity(
        "QhJc",
        villain_hand="AhKc",
        board="Td9h2s"
    )
    print(f"   Hero equity: {result.equity:.1%}")


def demo_range_analysis():
    """Demonstrate range parsing and combo counting."""
    print_section("Hand Range Analysis")
    
    ranges = [
        ("Premium pairs", "JJ+"),
        ("Pocket pairs", "22+"),
        ("Medium pairs", "66-TT"),
        ("Suited aces", "ATs+"),
        ("Suited broadways", "AKs,AQs,AJs,KQs"),
        ("Opening range", "77+,A9s+,KTs+,QTs+,AJo+,KQo"),
    ]
    
    print("\nRange                           Hands   Combos")
    print("-" * 55)
    
    for desc, range_str in ranges:
        range_obj = HandRange.from_string(range_str)
        combos = range_obj.get_combinations()
        print(f"{desc:30} {len(range_obj.hands):>4}    {len(combos):>5}")


def demo_quick_calculations():
    """Demonstrate quick equity check utility."""
    print_section("Quick Equity Checks")
    
    print("\nUsing quick_equity_check() for rapid calculations:\n")
    
    matchups = [
        ("AA vs KK", "AhAd", "KsKd", ""),
        ("AK vs QQ", "AhKh", "QsQd", ""),
        ("AK vs QQ (Ace flop)", "AhKh", "QsQd", "Ac7d2s"),
        ("AK vs QQ (Queen flop)", "AhKh", "QsQd", "Qc7d2s"),
    ]
    
    for desc, hero, villain, board in matchups:
        equity = quick_equity_check(hero, villain, board)
        board_str = f" [{board}]" if board else " [preflop]"
        print(f"{desc:25}{board_str:20} → {equity:.1%}")


def demo_caching_performance():
    """Demonstrate caching performance."""
    print_section("Caching Performance")
    
    import time
    
    calc = EquityCalculator(default_simulations=10000, cache_size=1000)
    
    print("\nComparing cached vs uncached calculations:\n")
    
    # First calculation (uncached)
    start = time.time()
    result1 = calc.calculate_equity("AhAd", villain_hand="KsKd")
    time1 = time.time() - start
    
    # Second calculation (cached)
    start = time.time()
    result2 = calc.calculate_equity("AhAd", villain_hand="KsKd")
    time2 = time.time() - start
    
    print(f"First call (uncached):  {time1*1000:.1f}ms → equity: {result1.equity:.3f}")
    print(f"Second call (cached):   {time2*1000:.1f}ms → equity: {result2.equity:.3f}")
    print(f"Speedup: {time1/time2:.1f}x faster")
    
    # Show cache statistics
    cache_info = calc.cache_info()
    print(f"\nCache statistics:")
    print(f"  Hits: {cache_info['hand_vs_hand']['hits']}")
    print(f"  Misses: {cache_info['hand_vs_hand']['misses']}")
    print(f"  Cache size: {cache_info['hand_vs_hand']['currsize']}/{cache_info['hand_vs_hand']['maxsize']}")


def main():
    """Run all demonstrations."""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  POKER EQUITY CALCULATOR DEMO - PHASE 2".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    try:
        demo_hand_vs_hand()
        demo_hand_vs_range()
        demo_preflop_scenarios()
        demo_postflop_scenarios()
        demo_range_analysis()
        demo_quick_calculations()
        demo_caching_performance()
        
        print_section("Demo Complete!")
        print("\n✅ Phase 2 Simulation Layer is ready for AI training!")
        print("\nNext steps:")
        print("  - Phase 3: Opponent Modeling")
        print("  - Phase 4: CFR + Reinforcement Learning")
        print("  - Phase 6: Full deployment\n")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

