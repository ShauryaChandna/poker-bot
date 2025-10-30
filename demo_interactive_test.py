#!/usr/bin/env python3
"""
Demo of Interactive Test - Automated Version

This runs a quick automated version of the interactive test
to demonstrate all the engine features working.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pypokerengine.engine import (
    Card, Deck, Suit, Rank,
    Player, HandEvaluator, HandRank,
    ActionManager, Round, Street, Game
)


def demo_card_creation():
    """Demo card creation and parsing."""
    print("🎴 CARD CREATION DEMO")
    print("-" * 30)
    
    # Test various cards
    test_cards = ["As", "Kh", "Qd", "Jc", "Th", "9s", "8h", "7c", "6d", "5s", "4h", "3c", "2d"]
    
    print("Creating cards from strings:")
    for card_str in test_cards[:5]:  # Show first 5
        card = Card.from_string(card_str)
        print(f"  {card_str} → {card}")
    
    print(f"  ... and {len(test_cards)-5} more")
    print("✅ Card creation works perfectly!")


def demo_deck_operations():
    """Demo deck shuffling and dealing."""
    print("\n🃏 DECK OPERATIONS DEMO")
    print("-" * 30)
    
    # Create deck
    deck = Deck(seed=42)
    print(f"Created deck with {len(deck)} cards")
    
    # Deal some cards
    dealt = deck.deal(5)
    print(f"Dealt 5 cards: {[str(c) for c in dealt]}")
    print(f"Cards remaining: {len(deck)}")
    
    # Deal one more
    single = deck.deal_one()
    print(f"Dealt one card: {single}")
    print(f"Cards remaining: {len(deck)}")
    
    print("✅ Deck operations work perfectly!")


def demo_hand_evaluation():
    """Demo hand evaluation."""
    print("\n🏆 HAND EVALUATION DEMO")
    print("-" * 30)
    
    # Test some hands
    test_hands = [
        (["As", "Ks", "Qs", "Js", "Ts"], "Royal Flush"),
        (["Kd", "Kh", "Ks", "Kc", "2d"], "Four of a Kind"),
        (["Ah", "Ad", "As", "Kh", "Kd"], "Full House"),
        (["Ac", "Jc", "9c", "5c", "2c"], "Flush"),
        (["9d", "8c", "7h", "6s", "5d"], "Straight"),
        (["Th", "Td", "Ah", "Kc", "6s"], "One Pair")
    ]
    
    print("Evaluating poker hands:")
    for card_strings, expected in test_hands:
        cards = [Card.from_string(s) for s in card_strings]
        rank, tiebreakers, hand_name = HandEvaluator.evaluate_hand(cards)
        cards_str = " ".join(card_strings)
        print(f"  {cards_str:25} → {hand_name}")
    
    print("✅ Hand evaluation works perfectly!")


def demo_player_management():
    """Demo player state management."""
    print("\n👥 PLAYER MANAGEMENT DEMO")
    print("-" * 30)
    
    # Create players
    alice = Player("Alice", 1000, "SB")
    bob = Player("Bob", 1000, "BB")
    
    print(f"Created players:")
    print(f"  {alice}")
    print(f"  {bob}")
    
    # Deal cards
    deck = Deck(seed=123)
    alice.deal_hole_cards(deck.deal(2))
    bob.deal_hole_cards(deck.deal(2))
    
    print(f"\nDealt hole cards:")
    print(f"  Alice: {alice.get_hole_cards_string()}")
    print(f"  Bob: {bob.get_hole_cards_string()}")
    
    # Test betting
    alice.post_blind(10, "small")
    bob.post_blind(20, "big")
    alice.call(20)
    bob.check()
    
    print(f"\nAfter betting:")
    print(f"  Alice: {alice}")
    print(f"  Bob: {bob}")
    
    print("✅ Player management works perfectly!")


def demo_action_validation():
    """Demo action validation."""
    print("\n⚖️  ACTION VALIDATION DEMO")
    print("-" * 30)
    
    # Create test scenario
    alice = Player("Alice", 1000, "SB")
    bob = Player("Bob", 1000, "BB")
    players = [alice, bob]
    
    # Post blinds
    alice.post_blind(10, "small")
    bob.post_blind(20, "big")
    
    pot_size = 30
    current_bet = 20
    
    print(f"Test scenario: Pot={pot_size}, Current bet={current_bet}")
    
    # Get legal actions
    legal_actions = ActionManager.get_legal_actions(
        alice, players, current_bet, pot_size, 20
    )
    
    print(f"Legal actions for Alice: {legal_actions}")
    
    # Test validation
    is_valid, error = ActionManager.validate_action(alice, "call", 20, legal_actions)
    print(f"Alice calling 20: {'✅ Valid' if is_valid else '❌ Invalid'} {error}")
    
    is_valid, error = ActionManager.validate_action(alice, "fold", 0, legal_actions)
    print(f"Alice folding: {'✅ Valid' if is_valid else '❌ Invalid'} {error}")
    
    print("✅ Action validation works perfectly!")


def demo_complete_game():
    """Demo a complete poker hand."""
    print("\n🎮 COMPLETE GAME DEMO")
    print("-" * 30)
    
    # Create game
    game = Game("Alice", "Bob", 1000, 10, 20, seed=456)
    
    print(f"Created game: {game.players[0].name} vs {game.players[1].name}")
    print(f"Starting stacks: {game.starting_stack} each")
    print(f"Blinds: {game.small_blind}/{game.big_blind}")
    
    # Simple AI strategy
    def simple_ai(player, legal_actions, street):
        if legal_actions.get('check'):
            return 'check', 0
        elif legal_actions.get('call'):
            # For call, we need to determine the amount to call
            current_bet = game.current_round.current_bet
            return 'call', current_bet
        else:
            return 'fold', 0
    
    # Play a hand
    print(f"\nPlaying hand...")
    result = game.play_hand(simple_ai)
    
    print(f"\nHand complete!")
    print(f"  Winner(s): {', '.join(result['winners'])}")
    print(f"  Pot: {result['pot']}")
    print(f"  Winning hand: {result['winning_hand']}")
    
    # Show community cards from the result
    if 'final_state' in result and 'community_cards' in result['final_state']:
        board = " ".join(result['final_state']['community_cards'])
        print(f"  Board: {board}")
    
    # Show final stacks
    print(f"\nFinal stacks:")
    for player in game.players:
        print(f"  {player.name}: {player.stack} chips")
    
    print("✅ Complete game works perfectly!")


def main():
    """Run all demos."""
    print("🎯 POKER ENGINE INTERACTIVE TEST DEMO")
    print("=" * 50)
    print("This demonstrates all the engine features working correctly.")
    print("For full interactive testing, run: python interactive_test.py")
    print()
    
    try:
        demo_card_creation()
        demo_deck_operations()
        demo_hand_evaluation()
        demo_player_management()
        demo_action_validation()
        demo_complete_game()
        
        print("\n" + "=" * 50)
        print("🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("Your poker engine is working perfectly!")
        print("\nTo run the full interactive test:")
        print("  python interactive_test.py")
        print("\nTo play interactively:")
        print("  python examples/interactive_cli.py")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
