"""
Game Management for Heads-Up Pot-Limit Hold'em

This module provides the main Game class that orchestrates the poker game.
"""

from typing import List, Dict, Any, Optional, Callable
from .player import Player
from .card import Deck
from .round import Round, Street
from .action_manager import ActionManager
import logging


class Game:
    """
    Main game controller for Heads-Up Pot-Limit Hold'em.
    
    Manages:
    - Multiple hands/rounds
    - Blind rotation
    - Player stacks
    - Game state
    - Integration with AI/UI layers
    """
    
    def __init__(
        self,
        player1_name: str = "Player 1",
        player2_name: str = "Player 2",
        starting_stack: int = 1000,
        small_blind: int = 10,
        big_blind: int = 20,
        seed: Optional[int] = None
    ):
        """
        Initialize a new game.
        
        Args:
            player1_name: Name of first player
            player2_name: Name of second player
            starting_stack: Starting chip stack for each player
            small_blind: Small blind amount
            big_blind: Big blind amount
            seed: Random seed for reproducibility
        """
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.starting_stack = starting_stack
        
        # Initialize players (positions will be assigned dynamically based on dealer)
        self.players = [
            Player(player1_name, starting_stack, ""),
            Player(player2_name, starting_stack, "")
        ]
        
        # Game state
        self.dealer_position = 0  # Dealer button position (0 or 1)
        self.hand_number = 0
        self.deck = Deck(seed=seed)
        self.current_round: Optional[Round] = None
        self.game_over = False
        
        # History
        self.hand_history: List[Dict[str, Any]] = []
        
        # Logger
        self.logger = logging.getLogger("PokerGame")
    
    def start_new_hand(self) -> Round:
        """
        Start a new hand/round.
        
        Returns:
            The new Round object
        """
        # Check if game is over
        if any(p.stack <= 0 for p in self.players):
            self.game_over = True
            raise ValueError("Game over - a player has no chips")
        
        self.hand_number += 1
        
        # Create new round
        self.current_round = Round(
            self.players,
            self.small_blind,
            self.big_blind,
            self.dealer_position,
            self.deck
        )
        
        # Start the hand (deal cards, post blinds)
        self.current_round.start_hand()
        
        self.logger.info(f"Hand #{self.hand_number} started")
        self.logger.info(f"Dealer: {self.players[self.dealer_position].name}")
        
        return self.current_round
    
    def play_hand(
        self,
        action_callback: Callable[[Player, Dict[str, Any], str], tuple]
    ) -> Dict[str, Any]:
        """
        Play a complete hand from start to finish.
        
        Args:
            action_callback: Function that takes (player, legal_actions, street)
                           and returns (action, amount)
        
        Returns:
            Dictionary with hand results
        """
        if self.current_round is None:
            self.start_new_hand()
        
        round_obj = self.current_round
        
        # Play through all streets
        streets = [Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER]
        
        for street in streets:
            self.logger.info(f"\n{street.value.upper()}")
            
            if street != Street.PREFLOP:
                round_obj.advance_street()
            
            # Display board if postflop
            if round_obj.community_cards:
                cards_str = " ".join(str(c) for c in round_obj.community_cards)
                self.logger.info(f"Board: {cards_str}")
            
            # Run betting round
            def round_callback(player: Player, legal_actions: Dict[str, Any]) -> tuple:
                return action_callback(player, legal_actions, street.value)
            
            continue_hand = round_obj.run_betting_round(round_callback)
            
            if not continue_hand:
                # Hand ended early (fold)
                break
            
            # Check if all but one player is all-in
            can_act = [p for p in self.players if p.can_act()]
            if len(can_act) == 0:
                # All players all-in, deal remaining cards
                self.logger.info("All players all-in, running out the board")
                while round_obj.street != Street.RIVER:
                    round_obj.advance_street()
                    if round_obj.community_cards:
                        cards_str = " ".join(str(c) for c in round_obj.community_cards)
                        self.logger.info(f"Board: {cards_str}")
                break
        
        # Determine winner
        result = round_obj.determine_winner()
        
        # Log result
        self.logger.info(f"\nHand complete!")
        self.logger.info(f"Winner(s): {', '.join(result['winners'])}")
        self.logger.info(f"Winning hand: {result['winning_hand']}")
        self.logger.info(f"Pot: {result['pot']}")
        
        # Record hand history
        hand_record = {
            "hand_number": self.hand_number,
            "dealer": self.players[self.dealer_position].name,
            "result": result,
            "final_state": round_obj.get_state()
        }
        self.hand_history.append(hand_record)
        
        # Rotate dealer button
        self.dealer_position = 1 - self.dealer_position
        
        # Clear current round
        self.current_round = None
        
        return result
    
    def step(
        self,
        action: str,
        amount: int = 0
    ) -> Dict[str, Any]:
        """
        Execute a single action and return updated game state.
        
        Useful for turn-by-turn play with external AI or UI.
        
        Args:
            action: Action to take ('fold', 'check', 'call', 'raise')
            amount: Bet amount (for raise)
        
        Returns:
            Updated game state
        """
        if self.current_round is None:
            raise ValueError("No active round - call start_new_hand() first")
        
        # This would need more sophisticated state management
        # for turn-by-turn play. Simplified version here.
        raise NotImplementedError("step() method needs state machine implementation")
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current game state.
        
        Returns:
            Dictionary of game state for AI/UI consumption
        """
        state = {
            "hand_number": self.hand_number,
            "dealer_position": self.dealer_position,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "game_over": self.game_over,
            "players": [
                {
                    "name": p.name,
                    "stack": p.stack,
                    "position": p.position
                }
                for p in self.players
            ]
        }
        
        if self.current_round:
            state["current_round"] = self.current_round.get_state()
        
        return state
    
    def is_game_over(self) -> bool:
        """
        Check if game is over (a player has busted).
        
        Returns:
            True if game is over
        """
        return any(p.stack <= 0 for p in self.players)
    
    def get_winner(self) -> Optional[Player]:
        """
        Get the game winner (player with chips remaining).
        
        Returns:
            Winning player or None if game not over
        """
        if not self.is_game_over():
            return None
        
        return next((p for p in self.players if p.stack > 0), None)
    
    def get_hand_history(self) -> List[Dict[str, Any]]:
        """
        Get complete hand history.
        
        Returns:
            List of hand records
        """
        return self.hand_history
    
    def reset_game(self):
        """Reset game to initial state."""
        for player in self.players:
            player.stack = self.starting_stack
            player.reset_for_new_hand()
        
        self.dealer_position = 0
        self.hand_number = 0
        self.current_round = None
        self.game_over = False
        self.hand_history = []
        self.deck = Deck()
        
        self.logger.info("Game reset")
    
    def __str__(self) -> str:
        """Return string representation of game state."""
        p1, p2 = self.players
        return (f"Hand #{self.hand_number}\n"
                f"{p1.name}: {p1.stack} chips\n"
                f"{p2.name}: {p2.stack} chips\n"
                f"Blinds: {self.small_blind}/{self.big_blind}")

