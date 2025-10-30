"""
Command-Line Interface for Poker Game

This module provides an interactive CLI for playing poker.
"""

from typing import Dict, Any, Tuple
import sys
from ..engine.game import Game
from ..engine.player import Player
from ..engine.action_manager import ActionManager


class PokerCLI:
    """
    Interactive command-line interface for Heads-Up Pot-Limit Hold'em.
    
    Supports:
    - Human vs AI play
    - Turn-by-turn display
    - Action prompts with valid options
    """
    
    def __init__(self, game: Game, human_player_index: int = 0):
        """
        Initialize the CLI.
        
        Args:
            game: Game instance to play
            human_player_index: Index of human player (0 or 1)
        """
        self.game = game
        self.human_player_index = human_player_index
        self.ai_player_index = 1 - human_player_index
    
    def display_game_state(self, street: str = ""):
        """Display current game state."""
        print("\n" + "="*60)
        print(f"HAND #{self.game.hand_number}")
        print("="*60)
        
        if self.game.current_round:
            round_obj = self.game.current_round
            
            # Display pot and street
            if street:
                print(f"\n*** {street.upper()} ***")
            print(f"Pot: {round_obj.pot}")
            
            # Display community cards
            if round_obj.community_cards:
                cards_str = " ".join(str(c) for c in round_obj.community_cards)
                print(f"Board: {cards_str}")
            
            # Display players
            print("\nPlayers:")
            for i, player in enumerate(self.game.players):
                prefix = "→ " if i == self.human_player_index else "  "
                status = ""
                if player.has_folded:
                    status = " [FOLDED]"
                elif player.is_all_in:
                    status = " [ALL-IN]"
                
                # Show hole cards only for human player
                if i == self.human_player_index:
                    cards = player.get_hole_cards_string()
                else:
                    cards = "?? ??"
                
                print(f"{prefix}{player.name} ({player.position}): "
                      f"{player.stack} chips, bet: {player.current_bet}, "
                      f"cards: {cards}{status}")
        else:
            # Between hands
            for player in self.game.players:
                print(f"{player.name}: {player.stack} chips")
    
    def get_human_action(
        self,
        player: Player,
        legal_actions: Dict[str, Any]
    ) -> Tuple[str, int]:
        """
        Prompt human player for action.
        
        Args:
            player: The acting player
            legal_actions: Dictionary of legal actions
        
        Returns:
            Tuple of (action, amount)
        """
        print(f"\n{player.name}'s turn:")
        print(f"Your stack: {player.stack}, Current bet: {player.current_bet}")
        
        # Display legal actions
        print("\nLegal actions:")
        actions = []
        
        if legal_actions.get("fold"):
            actions.append("fold")
            print("  [f] Fold")
        
        if legal_actions.get("check"):
            actions.append("check")
            print("  [c] Check")
        
        if legal_actions.get("call"):
            amount = self.game.current_round.current_bet - player.current_bet
            actions.append("call")
            print(f"  [c] Call {amount}")
        
        raise_info = legal_actions.get("raise")
        if raise_info and raise_info.get("allowed"):
            actions.append("raise")
            min_raise = raise_info["min"]
            max_raise = raise_info["max"]
            print(f"  [r] Raise (min: {min_raise}, max: {max_raise})")
        
        # Get input
        while True:
            try:
                user_input = input("\nYour action: ").strip().lower()
                
                if user_input in ['f', 'fold']:
                    if "fold" in actions:
                        return "fold", 0
                    else:
                        print("Cannot fold - no bet to face")
                
                elif user_input in ['c', 'check']:
                    if "check" in actions:
                        return "check", 0
                    elif "call" in actions:
                        return "call", self.game.current_round.current_bet
                    else:
                        print("Invalid action")
                
                elif user_input.startswith('r'):
                    if "raise" not in actions:
                        print("Cannot raise")
                        continue
                    
                    # Parse raise amount
                    parts = user_input.split()
                    if len(parts) == 1:
                        # Prompt for amount
                        try:
                            amount_str = input(f"Raise to (min: {raise_info['min']}, max: {raise_info['max']}): ")
                            amount = int(amount_str)
                        except ValueError:
                            print("Invalid amount")
                            continue
                    else:
                        try:
                            amount = int(parts[1])
                        except (ValueError, IndexError):
                            print("Invalid amount")
                            continue
                    
                    # Validate amount
                    if amount < raise_info["min"]:
                        print(f"Raise too small (min: {raise_info['min']})")
                    elif amount > raise_info["max"]:
                        print(f"Raise too large (max: {raise_info['max']})")
                    else:
                        return "raise", amount
                
                else:
                    print("Invalid input. Use: f (fold), c (check/call), r (raise)")
            
            except KeyboardInterrupt:
                print("\nGame interrupted")
                sys.exit(0)
    
    def get_ai_action(
        self,
        player: Player,
        legal_actions: Dict[str, Any]
    ) -> Tuple[str, int]:
        """
        Get action from simple AI (placeholder for more sophisticated AI).
        
        Args:
            player: The acting player
            legal_actions: Dictionary of legal actions
        
        Returns:
            Tuple of (action, amount)
        """
        # Simple AI: check/call if possible, otherwise fold
        if legal_actions.get("check"):
            print(f"{player.name} checks")
            return "check", 0
        elif legal_actions.get("call"):
            amount = self.game.current_round.current_bet
            print(f"{player.name} calls {amount}")
            return "call", amount
        else:
            print(f"{player.name} folds")
            return "fold", 0
    
    def play_game(self):
        """Play a complete game until one player busts."""
        print("\n" + "="*60)
        print("HEADS-UP POT-LIMIT HOLD'EM")
        print("="*60)
        print(f"\nPlayers: {self.game.players[0].name} vs {self.game.players[1].name}")
        print(f"Starting stacks: {self.game.starting_stack}")
        print(f"Blinds: {self.game.small_blind}/{self.game.big_blind}\n")
        input("Press Enter to start...")
        
        while not self.game.is_game_over():
            self.play_hand()
            
            # Show updated stacks
            print("\n" + "-"*60)
            for player in self.game.players:
                print(f"{player.name}: {player.stack} chips")
            print("-"*60)
            
            if not self.game.is_game_over():
                input("\nPress Enter for next hand...")
        
        # Game over
        winner = self.game.get_winner()
        print("\n" + "="*60)
        print("GAME OVER")
        print("="*60)
        print(f"\n{winner.name} wins with {winner.stack} chips!")
        print(f"Total hands played: {self.game.hand_number}")
    
    def play_hand(self):
        """Play a single hand."""
        self.game.start_new_hand()
        self.display_game_state(street="preflop")
        
        def action_callback(player: Player, legal_actions: Dict[str, Any], street: str) -> Tuple[str, int]:
            # Display state before action
            if player == self.game.players[self.human_player_index]:
                return self.get_human_action(player, legal_actions)
            else:
                return self.get_ai_action(player, legal_actions)
        
        result = self.game.play_hand(action_callback)
        
        # Show final result
        print("\n" + "="*60)
        print("HAND COMPLETE")
        print("="*60)
        
        # Show all hole cards at showdown
        if result.get("hands"):
            print("\nShowdown:")
            for player in self.game.players:
                if player.is_active:
                    cards = player.get_hole_cards_string()
                    hand_info = result["hands"].get(player.name, {})
                    hand_name = hand_info.get("hand_name", "")
                    print(f"{player.name}: {cards} - {hand_name}")
        
        print(f"\nWinner(s): {', '.join(result['winners'])}")
        print(f"Pot: {result['pot']} chips")
        print(f"Winning hand: {result['winning_hand']}")


def main():
    """Main entry point for CLI."""
    print("Welcome to Heads-Up Pot-Limit Hold'em!")
    
    # Get player name
    player_name = input("Enter your name (default: Human): ").strip() or "Human"
    
    # Create game
    game = Game(
        player1_name=player_name,
        player2_name="AI",
        starting_stack=1000,
        small_blind=10,
        big_blind=20
    )
    
    # Create and run CLI
    cli = PokerCLI(game, human_player_index=0)
    cli.play_game()


if __name__ == "__main__":
    main()

