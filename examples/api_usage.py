"""
API Usage Example

This example demonstrates how to use the poker engine API
for integration with external AI or UI systems.
"""

from pypokerengine.engine import Game, ActionManager
import json


def custom_ai_strategy(player, legal_actions, game_state):
    """
    More sophisticated AI that uses game state.
    
    Args:
        player: The acting player
        legal_actions: Dictionary of legal actions
        game_state: Complete game state dictionary
    
    Returns:
        Tuple of (action, amount)
    """
    # Example: Use pot odds to make decisions
    pot = game_state['current_round']['pot']
    current_bet = game_state['current_round']['current_bet']
    
    # Simple strategy based on pot size
    if legal_actions.get("check"):
        return "check", 0
    
    amount_to_call = current_bet - player.current_bet
    
    # Call if amount is less than 20% of pot
    if legal_actions.get("call") and amount_to_call < pot * 0.2:
        return "call", current_bet
    
    # Otherwise fold
    return "fold", 0


def main():
    """Demonstrate API usage."""
    print("="*60)
    print("POKER ENGINE API USAGE EXAMPLE")
    print("="*60)
    print()
    
    # Create game
    game = Game(
        player1_name="AI_Alpha",
        player2_name="AI_Beta",
        starting_stack=1000,
        small_blind=10,
        big_blind=20,
        seed=123
    )
    
    print("Initial Game State:")
    state = game.get_state()
    print(json.dumps(state, indent=2))
    print()
    
    # Start a hand
    game.start_new_hand()
    
    print("\nGame State After Deal:")
    state = game.get_state()
    print(json.dumps(state, indent=2))
    print()
    
    # Define action callback that uses game state
    def get_action(player, legal_actions, street):
        state = game.get_state()
        
        print(f"\n{player.name}'s turn on {street}:")
        print(f"  Legal actions: {legal_actions}")
        print(f"  Pot: {state['current_round']['pot']}")
        print(f"  Current bet: {state['current_round']['current_bet']}")
        
        action, amount = custom_ai_strategy(player, legal_actions, state)
        
        print(f"  Decision: {action}" + (f" {amount}" if amount > 0 else ""))
        
        return action, amount
    
    # Play the hand
    print("\n" + "="*60)
    print("PLAYING HAND")
    print("="*60)
    
    result = game.play_hand(get_action)
    
    print("\n" + "="*60)
    print("HAND RESULT")
    print("="*60)
    print(json.dumps(result, indent=2, default=str))
    
    # Get updated game state
    print("\n" + "="*60)
    print("FINAL GAME STATE")
    print("="*60)
    state = game.get_state()
    print(json.dumps(state, indent=2))
    
    # Demonstrate get_state() for AI integration
    print("\n" + "="*60)
    print("USING STATE FOR AI/ML TRAINING")
    print("="*60)
    print()
    print("The get_state() method returns a complete dictionary that can be used for:")
    print("  - Reinforcement Learning training")
    print("  - Monte Carlo simulations")
    print("  - UI rendering")
    print("  - Game analysis")
    print()
    print("Key state components:")
    print(f"  - Hand number: {state['hand_number']}")
    print(f"  - Players: {[p['name'] for p in state['players']]}")
    print(f"  - Stacks: {[p['stack'] for p in state['players']]}")
    if 'current_round' in state:
        print(f"  - Street: {state['current_round']['street']}")
        print(f"  - Pot: {state['current_round']['pot']}")
        print(f"  - Community cards: {state['current_round']['community_cards']}")


if __name__ == "__main__":
    main()

