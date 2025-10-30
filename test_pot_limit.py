#!/usr/bin/env python3
"""
Test Pot-Limit Calculations

This script tests the pot-limit calculations against the official rules
from Omaha Poker Training.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pypokerengine.engine import Player, ActionManager


def test_pot_limit_calculations():
    """Test pot-limit calculations against official rules."""
    print("🧮 TESTING POT-LIMIT CALCULATIONS")
    print("=" * 50)
    print("Testing against official rules from Omaha Poker Training")
    print("Formula: max_bet = 3 × (last_bet) + (pot_before_last_bet)")
    print("Min raise = big blind amount")
    print()
    
    # Test cases from the official guide
    test_cases = [
        {
            "name": "Example 1: Preflop, no limpers",
            "pot_before": 15,  # 5 + 10 blinds
            "current_bet": 10,  # big blind
            "big_blind": 10,
            "expected_min": 10,
            "expected_max": 35,  # (3 × 10) + 5
            "description": "Preflop, you are under the gun. Blinds are $5 and $10."
        },
        {
            "name": "Example 2: Preflop with limpers",
            "pot_before": 9,  # 1 + 2 + 2 + 2 + 2 (blinds + 3 limpers)
            "current_bet": 2,  # last limper
            "big_blind": 2,
            "expected_min": 2,
            "expected_max": 13,  # (3 × 2) + 7 = 6 + 7 = 13
            "description": "Preflop, button. Blinds $1/$2, 3 limpers."
        },
        {
            "name": "Example 3: Flop, no prior bet",
            "pot_before": 15,
            "current_bet": 0,
            "big_blind": 5,
            "expected_min": 5,
            "expected_max": 15,  # match pot
            "description": "Flop, you want to open for pot."
        },
        {
            "name": "Example 4: Facing a bet",
            "pot_before": 15,  # 10 + 5 (pot + bet)
            "current_bet": 5,
            "big_blind": 5,
            "expected_min": 5,
            "expected_max": 25,  # (3 × 5) + 10 = 15 + 10 = 25
            "description": "There is $10 in pot. Player A bets $5."
        },
        {
            "name": "Example 5: Facing a raise",
            "pot_before": 40,  # 10 + 5 + 25 (original pot + bet + raise)
            "current_bet": 25,  # raised to 25
            "big_blind": 5,
            "expected_min": 5,
            "expected_max": 90,  # (3 × 25) + 15 = 75 + 15 = 90
            "description": "Player A bets $5, Player B raises to $25."
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"  Scenario: {test_case['description']}")
        print(f"  Pot before: ${test_case['pot_before']}")
        print(f"  Current bet: ${test_case['current_bet']}")
        print(f"  Big blind: ${test_case['big_blind']}")
        
        # Create a dummy player
        player = Player("TestPlayer", 1000)
        
        # Calculate legal actions
        legal_actions = ActionManager.get_legal_actions(
            player, [player], test_case['current_bet'], 
            test_case['pot_before'], test_case['big_blind']
        )
        
        if legal_actions.get('raise') and legal_actions['raise']['allowed']:
            min_raise = legal_actions['raise']['min']
            max_raise = legal_actions['raise']['max']
            
            print(f"  Calculated min: ${min_raise}")
            print(f"  Calculated max: ${max_raise}")
            print(f"  Expected min: ${test_case['expected_min']}")
            print(f"  Expected max: ${test_case['expected_max']}")
            
            min_correct = min_raise == test_case['expected_min']
            max_correct = max_raise == test_case['expected_max']
            
            if min_correct and max_correct:
                print(f"  ✅ PASSED")
            else:
                print(f"  ❌ FAILED")
                if not min_correct:
                    print(f"    Min raise incorrect: got {min_raise}, expected {test_case['expected_min']}")
                if not max_correct:
                    print(f"    Max raise incorrect: got {max_raise}, expected {test_case['expected_max']}")
                all_passed = False
        else:
            print(f"  ❌ FAILED - No raise allowed when it should be")
            all_passed = False
        
        print()
    
    print("=" * 50)
    if all_passed:
        print("🎉 ALL POT-LIMIT TESTS PASSED!")
        print("Your implementation matches the official rules perfectly!")
    else:
        print("❌ Some tests failed. Check the calculations above.")
    
    return all_passed


def test_special_cases():
    """Test special cases like when player has already bet."""
    print("\n🔬 TESTING SPECIAL CASES")
    print("=" * 50)
    
    # Test case: Player has already bet this round
    print("Special Case: Player already bet this round")
    print("Scenario: You bet $5, opponent raises to $25")
    print("Expected: Subtract your $5 from the calculation")
    
    player = Player("TestPlayer", 1000)
    player.current_bet = 5  # Player already bet $5
    
    legal_actions = ActionManager.get_legal_actions(
        player, [player], 25, 40, 5  # facing $25 bet, $40 pot total (10 + 5 + 25)
    )
    
    if legal_actions.get('raise') and legal_actions['raise']['allowed']:
        min_raise = legal_actions['raise']['min']
        max_raise = legal_actions['raise']['max']
        
        print(f"  Calculated min: ${min_raise}")
        print(f"  Calculated max: ${max_raise}")
        print(f"  Expected min: $5")
        print(f"  Expected max: $85")  # (3 × 25) + 15 - 5 = 75 + 15 - 5 = 85
        
        if min_raise == 5 and max_raise == 85:
            print(f"  ✅ PASSED - Special case handled correctly")
        else:
            print(f"  ❌ FAILED - Special case not handled correctly")
    else:
        print(f"  ❌ FAILED - No raise allowed when it should be")


if __name__ == "__main__":
    print("🎯 POT-LIMIT CALCULATION TEST SUITE")
    print("Testing against official Omaha Poker Training rules")
    print("https://omaha.pokertraining.com/poker/articles/beginners/how-to-calculate-the-pot-in-plo.php")
    print()
    
    test_pot_limit_calculations()
    test_special_cases()
    
    print("\n" + "=" * 50)
    print("Test suite complete!")
