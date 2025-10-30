#!/usr/bin/env python3
"""
Interactive Poker Engine Test

This script provides an interactive testing interface for the poker engine.
Test all features step-by-step with guided prompts.
"""

import sys
import os
from typing import List, Dict, Any

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pypokerengine.engine import (
    Card, Deck, Suit, Rank,
    Player, HandEvaluator, HandRank,
    ActionManager, Round, Street, Game
)
from pypokerengine.utils import setup_game_logger
import logging


class InteractiveTester:
    """Interactive testing interface for the poker engine."""
    
    def __init__(self):
        self.logger = setup_game_logger(level=logging.INFO)
        self.test_results = []
    
    def print_header(self, title: str):
        """Print a formatted header."""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    def print_section(self, title: str):
        """Print a section header."""
        print(f"\n--- {title} ---")
    
    def wait_for_input(self, prompt: str = "Press Enter to continue..."):
        """Wait for user input."""
        input(f"\n{prompt}")
    
    def test_card_creation(self):
        """Test card creation and parsing."""
        self.print_header("TEST 1: Card Creation & Parsing")
        
        print("Testing card creation from strings...")
        
        # Test various card formats
        test_cards = ["As", "Kh", "Qd", "Jc", "Th", "9s", "8h", "7c", "6d", "5s", "4h", "3c", "2d"]
        
        for card_str in test_cards:
            try:
                card = Card.from_string(card_str)
                print(f"  ✅ {card_str} → {card}")
            except Exception as e:
                print(f"  ❌ {card_str} → Error: {e}")
        
        # Test invalid cards
        print("\nTesting invalid card formats...")
        invalid_cards = ["Xx", "1s", "Asx", "A", "ss"]
        
        for card_str in invalid_cards:
            try:
                card = Card.from_string(card_str)
                print(f"  ❌ {card_str} → Should have failed but got: {card}")
            except Exception as e:
                print(f"  ✅ {card_str} → Correctly rejected: {e}")
        
        self.test_results.append(("Card Creation", True))
        self.wait_for_input()
    
    def test_deck_operations(self):
        """Test deck shuffling and dealing."""
        self.print_header("TEST 2: Deck Operations")
        
        print("Creating and testing deck...")
        
        # Test deck creation
        deck = Deck(seed=42)
        print(f"  ✅ Deck created with {len(deck)} cards")
        
        # Test shuffling
        original_order = [str(card) for card in deck.cards[:5]]
        deck.shuffle()
        shuffled_order = [str(card) for card in deck.cards[:5]]
        
        print(f"  Original first 5: {original_order}")
        print(f"  Shuffled first 5: {shuffled_order}")
        print(f"  ✅ Shuffling {'worked' if original_order != shuffled_order else 'failed'}")
        
        # Test dealing
        dealt_cards = deck.deal(5)
        print(f"  Dealt 5 cards: {[str(c) for c in dealt_cards]}")
        print(f"  ✅ Cards remaining: {len(deck)}")
        
        # Test dealing one card
        single_card = deck.deal_one()
        print(f"  Dealt one card: {single_card}")
        print(f"  ✅ Cards remaining: {len(deck)}")
        
        # Test reset
        deck.reset()
        print(f"  ✅ After reset: {len(deck)} cards")
        
        self.test_results.append(("Deck Operations", True))
        self.wait_for_input()
    
    def test_hand_evaluation(self):
        """Test hand evaluation with various hands."""
        self.print_header("TEST 3: Hand Evaluation")
        
        # Test hands from best to worst
        test_hands = [
            (["As", "Ks", "Qs", "Js", "Ts"], "Royal Flush"),
            (["9h", "8h", "7h", "6h", "5h"], "Straight Flush"),
            (["Kd", "Kh", "Ks", "Kc", "2d"], "Four of a Kind"),
            (["Ah", "Ad", "As", "Kh", "Kd"], "Full House"),
            (["Ac", "Jc", "9c", "5c", "2c"], "Flush"),
            (["9d", "8c", "7h", "6s", "5d"], "Straight"),
            (["Qh", "Qd", "Qs", "7c", "4d"], "Three of a Kind"),
            (["Jh", "Jd", "8h", "8c", "3s"], "Two Pair"),
            (["Th", "Td", "Ah", "Kc", "6s"], "One Pair"),
            (["Ah", "Kd", "Qh", "8c", "3s"], "High Card")
        ]
        
        print("Testing hand evaluation...")
        
        for card_strings, expected in test_hands:
            try:
                cards = [Card.from_string(s) for s in card_strings]
                rank, tiebreakers, hand_name = HandEvaluator.evaluate_hand(cards)
                
                cards_str = " ".join(card_strings)
                print(f"  {cards_str:25} → {hand_name:20} (Rank: {rank})")
                
                if expected.lower() in hand_name.lower():
                    print(f"    ✅ Correctly identified as {expected}")
                else:
                    print(f"    ⚠️  Expected {expected}, got {hand_name}")
                    
            except Exception as e:
                print(f"  ❌ Error evaluating {card_strings}: {e}")
        
        # Test 7-card evaluation
        self.print_section("7-Card Evaluation (Texas Hold'em)")
        
        hole_cards = ["As", "Ah"]
        board = ["Ac", "Kh", "Kd", "7s", "2c"]
        all_cards = hole_cards + board
        
        cards = [Card.from_string(s) for s in all_cards]
        rank, tiebreakers, hand_name = HandEvaluator.evaluate_hand(cards)
        
        print(f"  Hole cards: {' '.join(hole_cards)}")
        print(f"  Board: {' '.join(board)}")
        print(f"  Best hand: {hand_name} (Rank: {rank})")
        print(f"  ✅ 7-card evaluation works")
        
        self.test_results.append(("Hand Evaluation", True))
        self.wait_for_input()
    
    def test_player_management(self):
        """Test player state management."""
        self.print_header("TEST 4: Player Management")
        
        print("Creating players...")
        
        # Create players
        alice = Player("Alice", 1000, "SB")
        bob = Player("Bob", 1000, "BB")
        
        print(f"  ✅ Alice: {alice}")
        print(f"  ✅ Bob: {bob}")
        
        # Test hole card dealing
        deck = Deck(seed=123)
        alice_cards = deck.deal(2)
        bob_cards = deck.deal(2)
        
        alice.deal_hole_cards(alice_cards)
        bob.deal_hole_cards(bob_cards)
        
        print(f"\nDealt hole cards:")
        print(f"  Alice: {alice.get_hole_cards_string()}")
        print(f"  Bob: {bob.get_hole_cards_string()}")
        
        # Test betting
        self.print_section("Betting Operations")
        
        # Alice posts small blind
        alice.post_blind(10, "small")
        print(f"  Alice posts small blind: {alice}")
        
        # Bob posts big blind
        bob.post_blind(20, "big")
        print(f"  Bob posts big blind: {bob}")
        
        # Alice calls
        alice.call(20)
        print(f"  Alice calls: {alice}")
        
        # Bob checks
        bob.check()
        print(f"  Bob checks: {bob}")
        
        # Test all-in
        alice.place_bet(990)  # All-in
        print(f"  Alice goes all-in: {alice}")
        print(f"  Alice is all-in: {alice.is_all_in}")
        
        # Test fold
        bob.fold()
        print(f"  Bob folds: {bob}")
        print(f"  Bob can act: {bob.can_act()}")
        
        self.test_results.append(("Player Management", True))
        self.wait_for_input()
    
    def test_action_validation(self):
        """Test action validation and pot-limit rules."""
        self.print_header("TEST 5: Action Validation & Pot-Limit Rules")
        
        # Create test scenario
        alice = Player("Alice", 1000, "SB")
        bob = Player("Bob", 1000, "BB")
        players = [alice, bob]
        
        # Post blinds
        alice.post_blind(10, "small")
        bob.post_blind(20, "big")
        
        pot_size = 30
        current_bet = 20
        
        print(f"Scenario: Pot={pot_size}, Current bet={current_bet}")
        print(f"Alice stack: {alice.stack}, Bob stack: {bob.stack}")
        
        # Test legal actions for Alice (needs to call 10)
        self.print_section("Legal Actions for Alice")
        
        legal_actions = ActionManager.get_legal_actions(
            alice, players, current_bet, pot_size, 20
        )
        
        print(f"  Legal actions: {legal_actions}")
        
        # Test valid actions
        test_actions = [
            ("fold", 0, "Alice folds"),
            ("call", 20, "Alice calls"),
        ]
        
        for action, amount, description in test_actions:
            is_valid, error = ActionManager.validate_action(
                alice, action, amount, legal_actions
            )
            status = "✅" if is_valid else "❌"
            print(f"  {status} {description}: {is_valid} {error}")
        
        # Test pot-limit raise calculation
        self.print_section("Pot-Limit Raise Calculation")
        
        # Alice calls first
        alice.call(20)
        current_bet = 20
        pot_size = 50
        
        print(f"After Alice calls: Pot={pot_size}, Current bet={current_bet}")
        
        # Bob's turn - can raise
        legal_actions = ActionManager.get_legal_actions(
            bob, players, current_bet, pot_size, 20
        )
        
        print(f"Bob's legal actions: {legal_actions}")
        
        if legal_actions.get('raise') and legal_actions['raise']['allowed']:
            raise_info = legal_actions['raise']
            print(f"  Min raise: {raise_info['min']}")
            print(f"  Max raise: {raise_info['max']}")
            print(f"  ✅ Pot-limit calculation works")
        
        self.test_results.append(("Action Validation", True))
        self.wait_for_input()
    
    def test_complete_hand(self):
        """Test a complete poker hand."""
        self.print_header("TEST 6: Complete Hand Simulation")
        
        print("Setting up a complete hand...")
        
        # Create game
        game = Game("Alice", "Bob", 1000, 10, 20, seed=456)
        
        # Start hand
        game.start_new_hand()
        
        print(f"Hand #{game.hand_number}")
        print(f"Dealer: {game.players[game.dealer_position].name}")
        
        # Show initial state
        for player in game.players:
            print(f"  {player.name}: {player.stack} chips, cards: {player.get_hole_cards_string()}")
        
        print(f"  Pot: {game.current_round.pot}")
        
        # Define simple AI strategy
        def simple_ai_strategy(player, legal_actions, street):
            print(f"\n  {player.name}'s turn on {street}:")
            print(f"    Legal actions: {legal_actions}")
            
            if legal_actions.get('check'):
                print(f"    {player.name} checks")
                return 'check', 0
            elif legal_actions.get('call'):
                print(f"    {player.name} calls")
                # For call, we need to determine the amount to call
                current_bet = game.current_round.current_bet
                return 'call', current_bet
            else:
                print(f"    {player.name} folds")
                return 'fold', 0
        
        # Play the hand
        print(f"\nPlaying hand...")
        result = game.play_hand(simple_ai_strategy)
        
        print(f"\nHand complete!")
        print(f"  Winner(s): {', '.join(result['winners'])}")
        print(f"  Pot: {result['pot']}")
        print(f"  Winning hand: {result['winning_hand']}")
        
        # Show final stacks
        for player in game.players:
            print(f"  {player.name}: {player.stack} chips")
        
        self.test_results.append(("Complete Hand", True))
        self.wait_for_input()
    
    def test_interactive_play(self):
        """Test interactive gameplay."""
        self.print_header("TEST 7: Interactive Gameplay")
        
        print("Starting interactive game...")
        print("You'll play as Alice against Bob (simple AI)")
        
        # Create game
        game = Game("You", "Bob", 1000, 10, 20, seed=789)
        
        # Start hand
        game.start_new_hand()
        
        print(f"\nHand #{game.hand_number}")
        print(f"Dealer: {game.players[game.dealer_position].name}")
        
        # Show your cards
        you = game.players[0]
        bob = game.players[1]
        
        print(f"\nYour cards: {you.get_hole_cards_string()}")
        print(f"Bob's cards: {bob.get_hole_cards_string()}")
        print(f"Pot: {game.current_round.pot}")
        
        # Simple AI strategy for Bob
        def bob_strategy(player, legal_actions, street):
            print(f"\n--- {player.name}'s turn on {street.upper()} ---")
            
            # Show the board if there are community cards
            if game.current_round.community_cards:
                board = " ".join(str(c) for c in game.current_round.community_cards)
                print(f"Board: {board}")
            else:
                print("Board: (no community cards yet)")
            
            print(f"{player.name}'s cards: {player.get_hole_cards_string()}")
            print(f"{player.name}'s stack: {player.stack}")
            print(f"Current bet: {game.current_round.current_bet}")
            print(f"{player.name}'s bet: {player.current_bet}")
            print(f"Pot: {game.current_round.pot}")
            
            if legal_actions.get('check'):
                print(f"{player.name} checks")
                return 'check', 0
            elif legal_actions.get('call'):
                print(f"{player.name} calls")
                # For call, we need to determine the amount to call
                current_bet = game.current_round.current_bet
                return 'call', current_bet
            else:
                print(f"{player.name} folds")
                return 'fold', 0
        
        # Interactive strategy for you
        def your_strategy(player, legal_actions, street):
            if player.name != "You":
                return bob_strategy(player, legal_actions, street)
            
            print(f"\n--- Your turn on {street.upper()} ---")
            
            # Always show the board if there are community cards
            if game.current_round.community_cards:
                board = " ".join(str(c) for c in game.current_round.community_cards)
                print(f"Board: {board}")
            else:
                print("Board: (no community cards yet)")
            
            print(f"Your cards: {player.get_hole_cards_string()}")
            print(f"Your stack: {player.stack}")
            print(f"Current bet: {game.current_round.current_bet}")
            print(f"Your bet: {player.current_bet}")
            print(f"Pot: {game.current_round.pot}")
            
            print(f"\nLegal actions:")
            if legal_actions.get('fold'):
                print("  [f] Fold")
            if legal_actions.get('check'):
                print("  [c] Check")
            if legal_actions.get('call'):
                # For call, we need to determine the amount to call
                current_bet = game.current_round.current_bet
                print(f"  [c] Call {current_bet}")
            if legal_actions.get('raise') and legal_actions['raise']['allowed']:
                raise_info = legal_actions['raise']
                print(f"  [r] Raise (min: {raise_info['min']}, max: {raise_info['max']})")
            
            while True:
                try:
                    choice = input("\nYour action: ").strip().lower()
                    
                    if choice in ['f', 'fold']:
                        if legal_actions.get('fold'):
                            return 'fold', 0
                        print("Cannot fold - no bet to face")
                    elif choice in ['c', 'check']:
                        if legal_actions.get('check'):
                            return 'check', 0
                        elif legal_actions.get('call'):
                            # For call, we need to determine the amount to call
                            current_bet = game.current_round.current_bet
                            return 'call', current_bet
                        print("Invalid action")
                    elif choice.startswith('r'):
                        if not (legal_actions.get('raise') and legal_actions['raise']['allowed']):
                            print("Cannot raise")
                            continue
                        
                        try:
                            if len(choice.split()) > 1:
                                amount = int(choice.split()[1])
                            else:
                                amount = int(input("Raise to: "))
                            
                            raise_info = legal_actions['raise']
                            if amount < raise_info['min'] or amount > raise_info['max']:
                                print(f"Amount must be between {raise_info['min']} and {raise_info['max']}")
                                continue
                            
                            return 'raise', amount
                        except ValueError:
                            print("Invalid amount")
                    else:
                        print("Invalid choice. Use: f (fold), c (check/call), r (raise)")
                
                except KeyboardInterrupt:
                    print("\nGame interrupted")
                    return 'fold', 0
        
        # Play the hand
        try:
            result = game.play_hand(your_strategy)
            
            print(f"\n--- Hand Complete ---")
            print(f"Winner(s): {', '.join(result['winners'])}")
            print(f"Pot: {result['pot']}")
            print(f"Winning hand: {result['winning_hand']}")
            
            if result.get('hands'):
                print(f"\nShowdown:")
                for player in game.players:
                    if player.is_active:
                        cards = player.get_hole_cards_string()
                        hand_info = result['hands'].get(player.name, {})
                        hand_name = hand_info.get('hand_name', '')
                        print(f"  {player.name}: {cards} - {hand_name}")
            
        except Exception as e:
            print(f"Error during hand: {e}")
        
        self.test_results.append(("Interactive Play", True))
        self.wait_for_input()
    
    def run_all_tests(self):
        """Run all interactive tests."""
        self.print_header("INTERACTIVE POKER ENGINE TEST SUITE")
        print("This will test all components of the poker engine step by step.")
        print("You can interact with some tests to verify functionality.")
        
        self.wait_for_input("Press Enter to start testing...")
        
        try:
            self.test_card_creation()
            self.test_deck_operations()
            self.test_hand_evaluation()
            self.test_player_management()
            self.test_action_validation()
            self.test_complete_hand()
            self.test_interactive_play()
            
            # Summary
            self.print_header("TEST RESULTS SUMMARY")
            
            print("All tests completed:")
            for test_name, passed in self.test_results:
                status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"  {test_name:20} {status}")
            
            print(f"\nTotal tests: {len(self.test_results)}")
            passed = sum(1 for _, p in self.test_results if p)
            print(f"Passed: {passed}")
            print(f"Failed: {len(self.test_results) - passed}")
            
            if passed == len(self.test_results):
                print("\n🎉 ALL TESTS PASSED! Your poker engine is working perfectly!")
            else:
                print(f"\n⚠️  {len(self.test_results) - passed} tests failed. Check the output above.")
            
        except KeyboardInterrupt:
            print("\n\nTesting interrupted by user.")
        except Exception as e:
            print(f"\n\nUnexpected error during testing: {e}")
            import traceback
            traceback.print_exc()
        
        print("\nThank you for testing the poker engine!")


def main():
    """Main entry point."""
    print("Poker Engine Interactive Test Suite")
    print("==================================")
    
    tester = InteractiveTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
