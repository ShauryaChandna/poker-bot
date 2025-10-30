#!/usr/bin/env python3
"""
Interactive Poker Game

Play heads-up poker against a simple AI opponent.
"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pypokerengine.engine import Game
from pypokerengine.utils import setup_game_logger
import logging


def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_separator():
    """Print a separator line."""
    print("-" * 60)


def display_game_state(game, player_name):
    """Display the current game state."""
    you = game.players[0] if game.players[0].name == player_name else game.players[1]
    opponent = game.players[1] if game.players[0].name == player_name else game.players[0]
    
    print(f"\n--- Hand #{game.hand_number} ---")
    print(f"Dealer: {game.players[game.dealer_position].name}")
    
    # Show your cards
    print(f"\nYour cards: {you.get_hole_cards_string()}")
    print(f"Your stack: {you.stack} chips")
    
    # Show opponent info (without cards)
    print(f"Opponent: {opponent.name} ({opponent.stack} chips)")
    
    # Show board
    if game.current_round.community_cards:
        board = " ".join(str(c) for c in game.current_round.community_cards)
        print(f"Board: {board}")
    else:
        print("Board: (no community cards yet)")
    
    # Show pot and betting info
    print(f"Pot: {game.current_round.pot}")
    print(f"Current bet: {game.current_round.current_bet}")
    print(f"Your bet: {you.current_bet}")


def get_player_action(player, legal_actions, street):
    """Get action from human player."""
    print(f"\n--- Your turn on {street.upper()} ---")
    
    # Show board if there are community cards
    if player.game.current_round.community_cards:
        board = " ".join(str(c) for c in player.game.current_round.community_cards)
        print(f"Board: {board}")
    else:
        print("Board: (no community cards yet)")
    
    print(f"Your cards: {player.get_hole_cards_string()}")
    print(f"Your stack: {player.stack}")
    print(f"Current bet: {player.game.current_round.current_bet}")
    print(f"Your bet: {player.current_bet}")
    print(f"Pot: {player.game.current_round.pot}")
    
    print(f"\nLegal actions:")
    if legal_actions.get('fold'):
        print("  [f] Fold")
    if legal_actions.get('check'):
        print("  [c] Check")
    if legal_actions.get('call'):
        current_bet = player.game.current_round.current_bet
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
                    current_bet = player.game.current_round.current_bet
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


def simple_ai_strategy(player, legal_actions, street):
    """Simple AI strategy for the computer opponent."""
    print(f"\n--- {player.name}'s turn on {street.upper()} ---")
    
    # Show board if there are community cards
    if player.game.current_round.community_cards:
        board = " ".join(str(c) for c in player.game.current_round.community_cards)
        print(f"Board: {board}")
    else:
        print("Board: (no community cards yet)")
    
    print(f"{player.name}'s cards: {player.get_hole_cards_string()}")
    print(f"{player.name}'s stack: {player.stack}")
    print(f"Current bet: {player.game.current_round.current_bet}")
    print(f"{player.name}'s bet: {player.current_bet}")
    print(f"Pot: {player.game.current_round.pot}")
    
    # Simple AI logic
    if legal_actions.get('check'):
        print(f"{player.name} checks")
        return 'check', 0
    elif legal_actions.get('call'):
        current_bet = player.game.current_round.current_bet
        print(f"{player.name} calls {current_bet}")
        return 'call', current_bet
    else:
        print(f"{player.name} folds")
        return 'fold', 0


def play_game():
    """Main game loop."""
    print_header("POKER GAME")
    print("Welcome to Heads-Up Pot-Limit Hold'em!")
    print("You'll play against a simple AI opponent.")
    
    # Get player name
    player_name = input("\nEnter your name (or press Enter for 'You'): ").strip()
    if not player_name:
        player_name = "You"
    
    # Create game
    game = Game(player_name, "Computer", 1000, 10, 20, seed=None)
    
    # Add game reference to players for strategy functions
    for player in game.players:
        player.game = game
    
    hand_count = 0
    
    while not game.is_game_over():
        hand_count += 1
        
        try:
            # Start new hand
            game.start_new_hand()
            
            # Re-add game reference to players (in case it was lost)
            for player in game.players:
                player.game = game
            
            # Display initial state
            display_game_state(game, player_name)
            
            # Define strategy that routes to human or AI
            def game_strategy(player, legal_actions, street):
                if player.name == player_name:
                    return get_player_action(player, legal_actions, street)
                else:
                    return simple_ai_strategy(player, legal_actions, street)
            
            # Play the hand
            print(f"\nPlaying hand...")
            result = game.play_hand(game_strategy)
            
            # Show results
            print_separator()
            print("HAND COMPLETE!")
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
            
            # Show final stacks
            print(f"\nFinal stacks:")
            for player in game.players:
                print(f"  {player.name}: {player.stack} chips")
            
            # Check if game is over
            if game.is_game_over():
                winner = game.get_winner()
                print(f"\n🎉 GAME OVER! {winner.name} wins with {winner.stack} chips!")
                break
            
            # Ask if player wants to continue
            print_separator()
            continue_playing = input("Play another hand? (y/n): ").strip().lower()
            if continue_playing not in ['y', 'yes']:
                break
                
        except KeyboardInterrupt:
            print("\n\nGame interrupted by user.")
            break
        except Exception as e:
            print(f"\nError during hand: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print("\nThanks for playing!")


if __name__ == "__main__":
    # Set up logging to reduce noise
    setup_game_logger(level=logging.WARNING)
    
    try:
        play_game()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Goodbye!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
