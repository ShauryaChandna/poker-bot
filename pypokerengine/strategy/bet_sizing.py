"""
Bet Sizing Module

Dynamic bet sizing with randomization to avoid predictability.
Adjusts bet sizes based on situation (value, bluff, thin value).
"""

import random
from enum import Enum
from typing import Optional


class BetType(Enum):
    """Type of bet being made."""
    VALUE = "value"           # Strong hand, want calls
    THIN_VALUE = "thin_value"  # Medium hand, want some calls
    BLUFF = "bluff"           # Weak hand, want folds
    PROTECTION = "protection"  # Protect against draws


class BetSizer:
    """
    Intelligent bet sizing with randomization.
    
    Provides bet sizes as fractions of pot, adjusted for:
    - Bet type (value, bluff, protection)
    - Stack sizes
    - Board texture
    - Opponent tendencies
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize bet sizer.
        
        Args:
            seed: Random seed for reproducibility (optional)
        """
        if seed is not None:
            random.seed(seed)
    
    def get_bet_size(
        self,
        pot: int,
        stack: int,
        bet_type: BetType,
        street: str = "flop",
        board_texture: str = "neutral"
    ) -> int:
        """
        Calculate bet size based on situation.
        
        Args:
            pot: Current pot size
            stack: Hero's remaining stack
            bet_type: Type of bet (value, bluff, etc.)
            street: Current street (preflop, flop, turn, river)
            board_texture: Board texture (dry, wet, neutral)
            
        Returns:
            Bet amount in chips
        """
        # Get base sizing as fraction of pot
        pot_fraction = self._get_base_pot_fraction(bet_type, street)
        
        # Add randomization (±10-15%)
        pot_fraction = self._randomize_sizing(pot_fraction)
        
        # Adjust for board texture
        pot_fraction = self._adjust_for_board(pot_fraction, board_texture, bet_type)
        
        # Calculate actual bet amount
        bet_amount = int(pot * pot_fraction)
        
        # Enforce min/max bounds
        min_bet = max(1, int(pot * 0.33))  # Minimum 33% pot
        max_bet = stack  # Can't bet more than stack
        
        bet_amount = max(min_bet, min(bet_amount, max_bet))
        
        return bet_amount
    
    def get_raise_size(
        self,
        pot: int,
        current_bet: int,
        hero_bet: int,
        stack: int,
        bet_type: BetType,
        street: str = "flop"
    ) -> int:
        """
        Calculate raise size when facing a bet.
        
        Args:
            pot: Current pot size
            current_bet: Opponent's bet amount
            hero_bet: Hero's current bet in this round
            stack: Hero's remaining stack
            bet_type: Type of raise (value or bluff)
            street: Current street
            
        Returns:
            Total amount to raise to
        """
        # Standard raise is 2.5-3x opponent's bet
        if bet_type == BetType.VALUE:
            raise_multiplier = random.uniform(2.8, 3.5)
        elif bet_type == BetType.BLUFF:
            raise_multiplier = random.uniform(2.5, 3.0)
        else:
            raise_multiplier = random.uniform(2.5, 3.2)
        
        # Calculate raise amount
        call_amount = current_bet - hero_bet
        raise_amount = int(call_amount * raise_multiplier)
        total_raise = current_bet + raise_amount
        
        # Adjust for pot size (don't go too crazy)
        max_raise = pot + current_bet + stack  # Pot-sized raise
        total_raise = min(total_raise, max_raise)
        
        # Ensure we're actually raising (not just calling)
        min_raise = current_bet + max(call_amount, int(pot * 0.5))
        total_raise = max(total_raise, min_raise)
        
        # Can't raise more than stack
        total_raise = min(total_raise, hero_bet + stack)
        
        return total_raise
    
    def _get_base_pot_fraction(self, bet_type: BetType, street: str) -> float:
        """Get base pot sizing fraction."""
        if bet_type == BetType.VALUE:
            # Strong hands: 60-75% pot
            if street == "river":
                return random.uniform(0.65, 0.85)
            return random.uniform(0.60, 0.75)
        
        elif bet_type == BetType.THIN_VALUE:
            # Medium hands: 40-55% pot
            return random.uniform(0.40, 0.55)
        
        elif bet_type == BetType.BLUFF:
            # Bluffs: 50-70% pot (enough to get folds)
            if street == "river":
                return random.uniform(0.60, 0.80)
            return random.uniform(0.50, 0.70)
        
        elif bet_type == BetType.PROTECTION:
            # Protection bets: 70-90% pot
            return random.uniform(0.70, 0.90)
        
        return 0.66  # Default 2/3 pot
    
    def _randomize_sizing(self, base_fraction: float) -> float:
        """
        Add randomization to avoid predictability.
        
        Args:
            base_fraction: Base pot fraction
            
        Returns:
            Randomized fraction
        """
        # Add Gaussian noise (mean=0, std=0.08)
        noise = random.gauss(0, 0.08)
        randomized = base_fraction + noise
        
        # Keep within reasonable bounds (0.33 to 1.5)
        return max(0.33, min(1.5, randomized))
    
    def _adjust_for_board(
        self,
        pot_fraction: float,
        board_texture: str,
        bet_type: BetType
    ) -> float:
        """
        Adjust sizing based on board texture.
        
        Wet boards (many draws) -> larger bets for protection
        Dry boards -> can bet smaller for value
        """
        if board_texture == "wet" and bet_type == BetType.VALUE:
            # Bet bigger on wet boards to protect
            return pot_fraction * 1.15
        
        elif board_texture == "dry" and bet_type == BetType.BLUFF:
            # Can bluff smaller on dry boards
            return pot_fraction * 0.90
        
        return pot_fraction
    
    def should_overbet(
        self,
        equity: float,
        pot: int,
        stack: int,
        street: str
    ) -> bool:
        """
        Decide whether to make an overbet (> 100% pot).
        
        Args:
            equity: Hero's equity
            pot: Current pot
            stack: Hero's stack
            street: Current street
            
        Returns:
            True if should overbet
        """
        # Only overbet on turn/river
        if street not in ["turn", "river"]:
            return False
        
        # Overbet with very strong hands (> 80% equity) or as big bluffs
        if equity > 0.80:
            return random.random() < 0.15  # 15% chance to overbet nuts
        
        # Occasional overbet bluffs on river
        if street == "river" and equity < 0.25:
            return random.random() < 0.08  # 8% chance to overbet bluff
        
        return False
    
    def get_preflop_raise_size(
        self,
        bb: int,
        position: str,
        facing_raise: bool = False,
        num_callers: int = 0
    ) -> int:
        """
        Get preflop raise/3bet sizing.
        
        Args:
            bb: Big blind size
            position: Hero's position (BTN, SB, BB)
            facing_raise: Whether facing a raise (3-bet)
            num_callers: Number of callers before hero
            
        Returns:
            Raise amount
        """
        if facing_raise:
            # 3-betting: 2.5-3.5x opponent's raise
            return int(bb * random.uniform(2.5, 3.5) * 3)
        else:
            # Opening raise: 2-3bb, adjust for position and callers
            base_raise = bb * random.uniform(2.0, 3.0)
            
            # Add 1bb per caller
            base_raise += num_callers * bb
            
            return int(base_raise)
    
    @staticmethod
    def classify_board_texture(board: list) -> str:
        """
        Classify board as wet, dry, or neutral.
        
        Simplified heuristic:
        - Wet: 3 suited, connected cards, multiple broadway
        - Dry: Rainbow, disconnected, low cards
        - Neutral: In between
        
        Args:
            board: List of Card objects or card strings
            
        Returns:
            "wet", "dry", or "neutral"
        """
        if not board or len(board) < 3:
            return "neutral"
        
        # TODO: Implement proper texture analysis
        # For now, return neutral
        # In production, analyze:
        # - Flush draws (3 suited)
        # - Straight draws (connected cards)
        # - Pair potential
        # - High card count
        
        return "neutral"

