"""
Hand History Module

Records and tracks all actions across poker hands for opponent analysis.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class Street(Enum):
    """Betting streets in poker."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


@dataclass
class ActionRecord:
    """
    Records a single action taken by a player.
    
    Attributes:
        player_id: Player who took the action
        street: Which betting street (preflop, flop, turn, river)
        action_type: Type of action ("fold", "check", "call", "bet", "raise")
        amount: Amount bet/raised (0 for check/fold)
        pot_size: Size of pot before action
        effective_stack: Player's remaining stack
        position: Player's position (BTN, SB, BB)
        is_aggressor: Whether player was the aggressor this street
        facing_bet: Amount of bet player is facing (0 if no bet)
    """
    player_id: str
    street: Street
    action_type: str
    amount: int = 0
    pot_size: int = 0
    effective_stack: int = 0
    position: Optional[str] = None
    is_aggressor: bool = False
    facing_bet: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'player_id': self.player_id,
            'street': self.street.value,
            'action_type': self.action_type,
            'amount': self.amount,
            'pot_size': self.pot_size,
            'effective_stack': self.effective_stack,
            'position': self.position,
            'is_aggressor': self.is_aggressor,
            'facing_bet': self.facing_bet,
        }


@dataclass
class HandRecord:
    """
    Complete record of a single hand.
    
    Attributes:
        hand_id: Unique identifier for this hand
        button_player: Player on button
        small_blind: Small blind amount
        big_blind: Big blind amount
        actions: All actions taken in the hand
        board: Community cards (empty for preflop)
        pot_size: Final pot size
        winner: Player who won (if hand went to showdown)
        showdown_hands: Hands shown at showdown (if applicable)
    """
    hand_id: str
    button_player: str
    small_blind: int
    big_blind: int
    actions: List[ActionRecord] = field(default_factory=list)
    board: List[str] = field(default_factory=list)
    pot_size: int = 0
    winner: Optional[str] = None
    showdown_hands: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_action(self, action: ActionRecord):
        """Add an action to this hand."""
        self.actions.append(action)
    
    def get_actions_by_player(self, player_id: str) -> List[ActionRecord]:
        """Get all actions by a specific player."""
        return [a for a in self.actions if a.player_id == player_id]
    
    def get_actions_by_street(self, street: Street) -> List[ActionRecord]:
        """Get all actions on a specific street."""
        return [a for a in self.actions if a.street == street]
    
    def get_preflop_sequence(self, player_id: str) -> List[str]:
        """
        Get preflop action sequence for a player.
        
        Returns:
            List of action types like ["fold"] or ["call", "raise"]
        """
        preflop_actions = [
            a for a in self.actions 
            if a.street == Street.PREFLOP and a.player_id == player_id
        ]
        return [a.action_type for a in preflop_actions]
    
    def did_player_vpip(self, player_id: str) -> bool:
        """
        Check if player voluntarily put money in pot preflop.
        
        Returns True if player called or raised (not counting forced BB).
        """
        preflop_actions = self.get_preflop_sequence(player_id)
        # VPIP means call or raise (not fold, not forced BB)
        return any(action in ['call', 'raise', 'bet'] for action in preflop_actions)
    
    def did_player_raise_preflop(self, player_id: str) -> bool:
        """Check if player raised preflop."""
        preflop_actions = self.get_preflop_sequence(player_id)
        return 'raise' in preflop_actions or 'bet' in preflop_actions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'hand_id': self.hand_id,
            'button_player': self.button_player,
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'actions': [a.to_dict() for a in self.actions],
            'board': self.board,
            'pot_size': self.pot_size,
            'winner': self.winner,
            'showdown_hands': self.showdown_hands,
        }


class HandHistory:
    """
    Tracks complete history of all hands played.
    
    Provides methods to query historical data for opponent modeling.
    """
    
    def __init__(self):
        """Initialize empty hand history."""
        self.hands: List[HandRecord] = []
        self._current_hand: Optional[HandRecord] = None
    
    def start_new_hand(
        self,
        hand_id: str,
        button_player: str,
        small_blind: int,
        big_blind: int
    ) -> HandRecord:
        """
        Start tracking a new hand.
        
        Args:
            hand_id: Unique identifier
            button_player: Player on button
            small_blind: SB amount
            big_blind: BB amount
            
        Returns:
            New HandRecord instance
        """
        hand = HandRecord(
            hand_id=hand_id,
            button_player=button_player,
            small_blind=small_blind,
            big_blind=big_blind
        )
        self._current_hand = hand
        return hand
    
    def record_action(
        self,
        player_id: str,
        street: Street,
        action_type: str,
        amount: int = 0,
        pot_size: int = 0,
        effective_stack: int = 0,
        position: Optional[str] = None,
        is_aggressor: bool = False,
        facing_bet: int = 0
    ):
        """
        Record an action in the current hand.
        
        Args:
            player_id: Player taking action
            street: Betting street
            action_type: Type of action
            amount: Bet/raise amount
            pot_size: Pot before action
            effective_stack: Player's remaining stack
            position: Player's position
            is_aggressor: Whether player is aggressor
            facing_bet: Amount player is facing
        """
        if self._current_hand is None:
            raise ValueError("No active hand. Call start_new_hand() first.")
        
        action = ActionRecord(
            player_id=player_id,
            street=street,
            action_type=action_type,
            amount=amount,
            pot_size=pot_size,
            effective_stack=effective_stack,
            position=position,
            is_aggressor=is_aggressor,
            facing_bet=facing_bet
        )
        self._current_hand.add_action(action)
    
    def finish_hand(
        self,
        board: List[str],
        pot_size: int,
        winner: str,
        showdown_hands: Optional[Dict[str, List[str]]] = None
    ):
        """
        Finish the current hand and add to history.
        
        Args:
            board: Community cards shown
            pot_size: Final pot size
            winner: Winning player
            showdown_hands: Hands shown (if showdown reached)
        """
        if self._current_hand is None:
            raise ValueError("No active hand to finish.")
        
        self._current_hand.board = board
        self._current_hand.pot_size = pot_size
        self._current_hand.winner = winner
        if showdown_hands:
            self._current_hand.showdown_hands = showdown_hands
        
        self.hands.append(self._current_hand)
        self._current_hand = None
    
    def get_player_hands(self, player_id: str, limit: Optional[int] = None) -> List[HandRecord]:
        """
        Get all hands involving a specific player.
        
        Args:
            player_id: Player to filter by
            limit: Maximum number of recent hands to return
            
        Returns:
            List of HandRecords involving the player
        """
        player_hands = [
            hand for hand in self.hands
            if any(a.player_id == player_id for a in hand.actions)
        ]
        
        if limit:
            return player_hands[-limit:]
        return player_hands
    
    def get_recent_hands(self, n: int = 10) -> List[HandRecord]:
        """Get N most recent hands."""
        return self.hands[-n:] if n < len(self.hands) else self.hands
    
    def count_hands(self, player_id: Optional[str] = None) -> int:
        """
        Count total hands.
        
        Args:
            player_id: If provided, count only hands with this player
            
        Returns:
            Number of hands
        """
        if player_id is None:
            return len(self.hands)
        return len(self.get_player_hands(player_id))
    
    def get_action_frequency(
        self,
        player_id: str,
        street: Street,
        action_type: str
    ) -> float:
        """
        Calculate frequency of a specific action type on a street.
        
        Args:
            player_id: Player to analyze
            street: Street to analyze
            action_type: Action type to count
            
        Returns:
            Frequency (0-1) of this action
        """
        player_hands = self.get_player_hands(player_id)
        
        total_actions = 0
        action_count = 0
        
        for hand in player_hands:
            street_actions = [
                a for a in hand.actions
                if a.player_id == player_id and a.street == street
            ]
            total_actions += len(street_actions)
            action_count += sum(1 for a in street_actions if a.action_type == action_type)
        
        if total_actions == 0:
            return 0.0
        return action_count / total_actions
    
    def clear(self):
        """Clear all hand history."""
        self.hands = []
        self._current_hand = None
    
    def __len__(self) -> int:
        """Return number of completed hands."""
        return len(self.hands)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"HandHistory({len(self.hands)} hands)"

