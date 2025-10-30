#!/usr/bin/env python3
"""
Test specific pot-limit scenario

Testing the scenario where:
- Starting stack: 1000
- Blinds: 10/20
- Max bet should be 70 (making stack 930, pot 140 when called)
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pypokerengine.engine import Player, ActionManager


def test_specific_scenario():
    """Test the specific pot-limit scenario."""
    print("🧮 TESTING SPECIFIC POT-LIMIT SCENARIO")
    print("=" * 50)
    print("Scenario: Starting stack 1000, blinds 10/20")
    print("Expected: Max bet should be 70 (stack becomes 930, pot 140 when called)")
    print()
    
    # Create scenario: preflop, small blind vs big blind
    # Small blind posts 10, big blind posts 20
    # Pot = 30, current bet = 20 (big blind)
    # Small blind can raise up to pot limit
    
    sb_player = Player("SB", 1000, "SB")
    bb_player = Player("BB", 1000, "BB")
    
    # Post blinds
    sb_player.post_blind(10, "small")
    bb_player.post_blind(20, "big")
    
    print(f"After posting blinds:")
    print(f"  SB: {sb_player.stack} chips, bet: {sb_player.current_bet}")
    print(f"  BB: {bb_player.stack} chips, bet: {bb_player.current_bet}")
    print(f"  Pot: {sb_player.current_bet + bb_player.current_bet}")
    
    # SB can now raise
    pot_size = sb_player.current_bet + bb_player.current_bet  # 30
    current_bet = bb_player.current_bet  # 20
    big_blind = 20
    
    print(f"\nSB's turn to act:")
    print(f"  Pot size: {pot_size}")
    print(f"  Current bet: {current_bet}")
    print(f"  Big blind: {big_blind}")
    
    legal_actions = ActionManager.get_legal_actions(
        sb_player, [sb_player, bb_player], current_bet, pot_size, big_blind
    )
    
    print(f"\nLegal actions for SB:")
    print(f"  {legal_actions}")
    
    if legal_actions.get('raise') and legal_actions['raise']['allowed']:
        min_raise = legal_actions['raise']['min']
        max_raise = legal_actions['raise']['max']
        
        print(f"\nRaise limits:")
        print(f"  Min raise: {min_raise}")
        print(f"  Max raise: {max_raise}")
        
        # Calculate what happens if SB raises to max
        if sb_player.place_bet(max_raise):
            print(f"\nIf SB raises to {max_raise}:")
            print(f"  SB stack: {sb_player.stack}")
            print(f"  SB bet: {sb_player.current_bet}")
            
            # If BB calls
            bb_player.call(max_raise)
            total_pot = sb_player.current_bet + bb_player.current_bet
            print(f"  After BB calls:")
            print(f"    BB stack: {bb_player.stack}")
            print(f"    BB bet: {bb_player.current_bet}")
            print(f"    Total pot: {total_pot}")
            
            # Expected: SB stack = 930, pot = 140
            expected_sb_stack = 930
            expected_pot = 140
            
            print(f"\nExpected:")
            print(f"  SB stack: {expected_sb_stack}")
            print(f"  Total pot: {expected_pot}")
            
            if sb_player.stack == expected_sb_stack and total_pot == expected_pot:
                print(f"  ✅ CORRECT!")
            else:
                print(f"  ❌ INCORRECT!")
                print(f"    Got SB stack: {sb_player.stack}, expected: {expected_sb_stack}")
                print(f"    Got pot: {total_pot}, expected: {expected_pot}")
    else:
        print("❌ No raise allowed - this is wrong!")


if __name__ == "__main__":
    test_specific_scenario()
