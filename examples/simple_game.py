"""
Simple Example: Complete Game with Simple AI

This example demonstrates a complete game between two simple AI players.
"""

from pypokerengine.engine import Game, Player
from pypokerengine.utils import setup_game_logger
import logging


def simple_ai_strategy(player, legal_actions, street):
    """
    Very simple AI strategy: check/call when possible, otherwise fold.
    
    Args:
        player: The acting player
        legal_actions: Dictionary of legal actions
        street: Current betting street
    
    Returns:
        Tuple of (action, amount)
    """
    if legal_actions.get("check"):
        return "check", 0
    elif legal_actions.get("call"):
        # For call, we need to determine the amount to call
        # The legal_actions['call'] should contain the amount
        call_amount = legal_actions.get('call', 0)
        if isinstance(call_amount, dict):
            call_amount = call_amount.get('amount', 0)
        return "call", call_amount
    else:
        return "fold", 0


def main():
    """Run a simple game between two AI players."""
    # Setup logging
    logger = setup_game_logger(level=logging.INFO)
    
    print("="*60)
    print("SIMPLE POKER GAME EXAMPLE")
    print("="*60)
    print("\nRunning a game between two simple AI players...")
    print("AI Strategy: Check/Call if possible, otherwise fold\n")
    
    # Create game
    game = Game(
        player1_name="Alice",
        player2_name="Bob",
        starting_stack=1000,
        small_blind=10,
        big_blind=20,
        seed=42  # For reproducible results
    )
    
    hands_played = 0
    max_hands = 50  # Limit number of hands for demo
    
    # Play until someone busts or max hands reached
    while not game.is_game_over() and hands_played < max_hands:
        hands_played += 1
        
        print(f"\n{'='*60}")
        print(f"Hand #{hands_played}")
        print(f"{'='*60}")
        
        # Show stacks before hand
        for player in game.players:
            print(f"{player.name}: {player.stack} chips")
        
        # Define action callback
        def get_action(player, legal_actions, street):
            action, amount = simple_ai_strategy(player, legal_actions, street)
            
            # Determine actual amount for call/raise
            if action == "call" and legal_actions.get("call"):
                amount = game.current_round.current_bet
            
            print(f"  {player.name} {action}s" + (f" {amount}" if amount > 0 else ""))
            return action, amount
        
        # Play the hand
        try:
            result = game.play_hand(get_action)
            
            # Show result
            print(f"\nResult:")
            print(f"  Winner(s): {', '.join(result['winners'])}")
            print(f"  Pot: {result['pot']}")
            print(f"  Winning hand: {result['winning_hand']}")
        except Exception as e:
            print(f"Error during hand: {e}")
            break
    
    # Final results
    print(f"\n{'='*60}")
    print("GAME COMPLETE")
    print(f"{'='*60}")
    print(f"\nHands played: {hands_played}")
    
    for player in game.players:
        print(f"{player.name}: {player.stack} chips")
    
    if game.is_game_over():
        winner = game.get_winner()
        print(f"\n{winner.name} wins!")
    else:
        print(f"\nGame stopped after {max_hands} hands (demo limit)")


if __name__ == "__main__":
    main()

