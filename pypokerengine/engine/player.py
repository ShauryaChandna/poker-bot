"""
Player Management

This module provides the Player class for managing player state in poker games.
"""

from typing import List, Optional, Dict, Any
from .card import Card


class Player:
    """
    Represents a poker player with stack, cards, and betting history.
    
    Attributes:
        name (str): Player's name/identifier
        stack (int): Current chip stack
        hole_cards (List[Card]): Player's private cards
        is_active (bool): Whether player is still in the hand
        is_all_in (bool): Whether player is all-in
        position (str): Player's position ('SB' or 'BB')
    """
    
    def __init__(self, name: str, stack: int, position: str = ""):
        """
        Initialize a player.
        
        Args:
            name: Player's name or identifier
            stack: Starting chip stack
            position: Player's position (e.g., 'SB', 'BB')
        """
        self.name = name
        self.stack = stack
        self.initial_stack = stack
        self.position = position
        
        # Cards and hand state
        self.hole_cards: List[Card] = []
        self.is_active = True
        self.is_all_in = False
        self.has_folded = False
        
        # Betting tracking
        self.current_bet = 0  # Amount bet in current betting round
        self.total_bet = 0    # Total amount bet in entire hand
        self.action_history: List[Dict[str, Any]] = []
    
    def deal_hole_cards(self, cards: List[Card]):
        """
        Deal hole cards to the player.
        
        Args:
            cards: List of cards to deal (typically 2 for Hold'em)
        """
        self.hole_cards = cards
    
    def reset_for_new_hand(self):
        """Reset player state for a new hand."""
        self.hole_cards = []
        self.is_active = True
        self.is_all_in = False
        self.has_folded = False
        self.current_bet = 0
        self.total_bet = 0
        self.action_history = []
    
    def reset_current_bet(self):
        """Reset current bet for a new betting round (but preserve total_bet)."""
        self.current_bet = 0
    
    def place_bet(self, amount: int) -> int:
        """
        Place a bet, deducting from stack.
        
        Args:
            amount: Amount to bet (total bet, not additional)
            
        Returns:
            Actual amount added to the pot (amount - current_bet)
        """
        # Calculate additional amount to add
        additional = amount - self.current_bet
        
        # Handle all-in case
        if additional >= self.stack:
            additional = self.stack
            amount = self.current_bet + additional
            self.is_all_in = True
        
        # Deduct from stack
        self.stack -= additional
        self.current_bet = amount
        self.total_bet += additional
        
        return additional
    
    def fold(self):
        """Mark player as folded."""
        self.is_active = False
        self.has_folded = True
        self.add_action("fold", 0)
    
    def check(self):
        """Record a check action."""
        self.add_action("check", 0)
    
    def call(self, amount: int) -> int:
        """
        Call a bet.
        
        Args:
            amount: Total amount to match
            
        Returns:
            Amount added to pot
        """
        added = self.place_bet(amount)
        self.add_action("call", amount)
        return added
    
    def bet(self, amount: int) -> int:
        """
        Place a bet/raise.
        
        Args:
            amount: Total bet amount
            
        Returns:
            Amount added to pot
        """
        added = self.place_bet(amount)
        action_type = "raise" if self.current_bet > 0 else "bet"
        self.add_action(action_type, amount)
        return added
    
    def post_blind(self, amount: int, blind_type: str) -> int:
        """
        Post a blind (small or big).
        
        Args:
            amount: Blind amount
            blind_type: Type of blind ('small' or 'big')
            
        Returns:
            Amount added to pot
        """
        added = self.place_bet(amount)
        self.add_action(f"{blind_type}_blind", amount)
        return added
    
    def add_action(self, action: str, amount: int):
        """
        Record an action in the player's history.
        
        Args:
            action: Action type (fold, check, call, raise, bet, etc.)
            amount: Amount associated with action
        """
        self.action_history.append({
            "action": action,
            "amount": amount
        })
    
    def win_pot(self, amount: int):
        """
        Award pot winnings to player.
        
        Args:
            amount: Amount won
        """
        self.stack += amount
    
    def can_act(self) -> bool:
        """
        Check if player can still act in current hand.
        
        Returns:
            True if player is active and not all-in
        """
        return self.is_active and not self.is_all_in
    
    def get_hole_cards_string(self, hidden: bool = False) -> str:
        """
        Get string representation of hole cards.
        
        Args:
            hidden: If True, show cards as '??'
            
        Returns:
            String representation of hole cards
        """
        if hidden:
            return "?? ??"
        return " ".join(str(card) for card in self.hole_cards)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert player state to dictionary.
        
        Returns:
            Dictionary representation of player state
        """
        return {
            "name": self.name,
            "stack": self.stack,
            "position": self.position,
            "hole_cards": [str(card) for card in self.hole_cards],
            "current_bet": self.current_bet,
            "total_bet": self.total_bet,
            "is_active": self.is_active,
            "is_all_in": self.is_all_in,
            "has_folded": self.has_folded,
            "action_history": self.action_history
        }
    
    def __str__(self) -> str:
        """Return string representation of player."""
        status = ""
        if self.has_folded:
            status = " [FOLDED]"
        elif self.is_all_in:
            status = " [ALL-IN]"
        
        return (f"{self.name} ({self.position}): {self.stack} chips, "
                f"bet: {self.current_bet}{status}")
    
    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"Player(name={self.name}, stack={self.stack}, position={self.position})"

