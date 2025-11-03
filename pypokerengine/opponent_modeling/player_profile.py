"""
Player Profile Module

Tracks opponent statistics and playing tendencies over time.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class PlayerArchetype(Enum):
    """Common player archetypes based on playing style."""
    TIGHT_PASSIVE = "tight_passive"      # Nit: plays few hands, rarely raises
    TIGHT_AGGRESSIVE = "tight_aggressive"  # TAG: plays few hands, raises often
    LOOSE_PASSIVE = "loose_passive"       # Calling station: plays many hands, rarely raises
    LOOSE_AGGRESSIVE = "loose_aggressive"  # LAG: plays many hands, raises often
    UNKNOWN = "unknown"                   # Not enough data yet


@dataclass
class PlayerProfile:
    """
    Tracks comprehensive player statistics and tendencies.
    
    Key Metrics:
    - VPIP (Voluntarily Put $ In Pot): % of hands where player calls/raises preflop
    - PFR (Pre-Flop Raise): % of hands where player raises preflop
    - AF (Aggression Factor): (Bets + Raises) / Calls (postflop)
    - Fold to C-Bet: % of times player folds to continuation bet
    - 3-Bet: % of times player re-raises preflop
    
    Attributes:
        player_id: Unique identifier for the player
        hands_played: Total number of hands observed
        vpip_count: Hands where player voluntarily put money in
        pfr_count: Hands where player raised preflop
        postflop_bets: Number of bets/raises postflop
        postflop_calls: Number of calls postflop
        cbet_faced: Times player faced a continuation bet
        cbet_folded: Times player folded to continuation bet
        three_bet_opportunities: Times player could 3-bet
        three_bet_count: Times player actually 3-bet
    """
    
    player_id: str
    hands_played: int = 0
    
    # Preflop stats
    vpip_count: int = 0
    pfr_count: int = 0
    three_bet_opportunities: int = 0
    three_bet_count: int = 0
    
    # Postflop stats
    postflop_bets: int = 0
    postflop_raises: int = 0
    postflop_calls: int = 0
    postflop_folds: int = 0
    
    # C-bet defense
    cbet_faced: int = 0
    cbet_folded: int = 0
    cbet_called: int = 0
    cbet_raised: int = 0
    
    # Positional stats
    button_vpip: int = 0
    button_hands: int = 0
    
    # Advanced metrics
    seen_showdown: int = 0
    won_at_showdown: int = 0
    
    # Metadata
    notes: str = ""
    
    @property
    def vpip(self) -> float:
        """Voluntarily Put $ In Pot percentage."""
        if self.hands_played == 0:
            return 0.0
        return self.vpip_count / self.hands_played
    
    @property
    def pfr(self) -> float:
        """Pre-Flop Raise percentage."""
        if self.hands_played == 0:
            return 0.0
        return self.pfr_count / self.hands_played
    
    @property
    def aggression_factor(self) -> float:
        """
        Aggression Factor: (Bets + Raises) / Calls
        Higher = more aggressive. Typical ranges:
        - < 1.0: Very passive
        - 1.0-2.0: Passive
        - 2.0-3.0: Balanced
        - 3.0-5.0: Aggressive
        - > 5.0: Very aggressive
        """
        if self.postflop_calls == 0:
            # Avoid division by zero - if no calls, return high value
            aggressive_actions = self.postflop_bets + self.postflop_raises
            return float(aggressive_actions) if aggressive_actions > 0 else 0.0
        return (self.postflop_bets + self.postflop_raises) / self.postflop_calls
    
    @property
    def fold_to_cbet(self) -> float:
        """Percentage of times folded to continuation bet."""
        if self.cbet_faced == 0:
            return 0.0
        return self.cbet_folded / self.cbet_faced
    
    @property
    def three_bet_percentage(self) -> float:
        """Percentage of 3-bet opportunities taken."""
        if self.three_bet_opportunities == 0:
            return 0.0
        return self.three_bet_count / self.three_bet_opportunities
    
    @property
    def wtsd(self) -> float:
        """
        Went To ShowDown percentage.
        % of hands that went to showdown after seeing flop.
        """
        if self.hands_played == 0:
            return 0.0
        return self.seen_showdown / self.hands_played
    
    @property
    def won_at_sd(self) -> float:
        """Won At Showdown percentage."""
        if self.seen_showdown == 0:
            return 0.0
        return self.won_at_showdown / self.seen_showdown
    
    def get_archetype(self) -> PlayerArchetype:
        """
        Classify player into archetype based on VPIP and PFR.
        
        Classification rules:
        - Tight: VPIP < 0.25
        - Loose: VPIP >= 0.25
        - Passive: PFR/VPIP < 0.6 (or AF < 2.0)
        - Aggressive: PFR/VPIP >= 0.6 (or AF >= 2.0)
        
        Returns:
            PlayerArchetype enum value
        """
        # Need minimum hands for classification
        if self.hands_played < 20:
            return PlayerArchetype.UNKNOWN
        
        tight = self.vpip < 0.25
        
        # Check aggression through PFR ratio and AF
        pfr_ratio = self.pfr / self.vpip if self.vpip > 0 else 0
        aggressive = pfr_ratio >= 0.6 or self.aggression_factor >= 2.0
        
        if tight and aggressive:
            return PlayerArchetype.TIGHT_AGGRESSIVE
        elif tight and not aggressive:
            return PlayerArchetype.TIGHT_PASSIVE
        elif not tight and aggressive:
            return PlayerArchetype.LOOSE_AGGRESSIVE
        else:
            return PlayerArchetype.LOOSE_PASSIVE
    
    def update_preflop_action(
        self,
        action: str,
        is_raise: bool = False,
        is_voluntary: bool = False,
        could_three_bet: bool = False,
        is_three_bet: bool = False
    ):
        """
        Update profile with a preflop action.
        
        Args:
            action: Action type ("fold", "call", "raise", "check")
            is_raise: Whether this was a raise
            is_voluntary: Whether money was put in voluntarily (not BB forced)
            could_three_bet: Whether player had opportunity to 3-bet
            is_three_bet: Whether this was a 3-bet
        """
        self.hands_played += 1
        
        if is_voluntary:
            self.vpip_count += 1
        
        if is_raise:
            self.pfr_count += 1
        
        if could_three_bet:
            self.three_bet_opportunities += 1
            if is_three_bet:
                self.three_bet_count += 1
    
    def update_postflop_action(
        self,
        action: str,
        is_bet: bool = False,
        is_raise: bool = False,
        is_call: bool = False,
        is_fold: bool = False,
        faced_cbet: bool = False
    ):
        """
        Update profile with a postflop action.
        
        Args:
            action: Action type
            is_bet: Whether this was a bet
            is_raise: Whether this was a raise
            is_call: Whether this was a call
            is_fold: Whether this was a fold
            faced_cbet: Whether player faced a continuation bet
        """
        if is_bet:
            self.postflop_bets += 1
        if is_raise:
            self.postflop_raises += 1
        if is_call:
            self.postflop_calls += 1
        if is_fold:
            self.postflop_folds += 1
        
        if faced_cbet:
            self.cbet_faced += 1
            if is_fold:
                self.cbet_folded += 1
            elif is_call:
                self.cbet_called += 1
            elif is_raise:
                self.cbet_raised += 1
    
    def update_showdown(self, won: bool):
        """Record a showdown result."""
        self.seen_showdown += 1
        if won:
            self.won_at_showdown += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization."""
        return {
            'player_id': self.player_id,
            'hands_played': self.hands_played,
            'vpip': self.vpip,
            'pfr': self.pfr,
            'aggression_factor': self.aggression_factor,
            'fold_to_cbet': self.fold_to_cbet,
            'three_bet_percentage': self.three_bet_percentage,
            'wtsd': self.wtsd,
            'won_at_sd': self.won_at_sd,
            'archetype': self.get_archetype().value,
            'raw_stats': {
                'vpip_count': self.vpip_count,
                'pfr_count': self.pfr_count,
                'postflop_bets': self.postflop_bets,
                'postflop_raises': self.postflop_raises,
                'postflop_calls': self.postflop_calls,
                'postflop_folds': self.postflop_folds,
                'cbet_faced': self.cbet_faced,
                'cbet_folded': self.cbet_folded,
                'three_bet_opportunities': self.three_bet_opportunities,
                'three_bet_count': self.three_bet_count,
                'seen_showdown': self.seen_showdown,
                'won_at_showdown': self.won_at_showdown,
            }
        }
    
    def __repr__(self) -> str:
        """String representation of player profile."""
        archetype = self.get_archetype().value.replace('_', ' ').title()
        return (
            f"PlayerProfile(id={self.player_id}, hands={self.hands_played}, "
            f"VPIP={self.vpip:.1%}, PFR={self.pfr:.1%}, AF={self.aggression_factor:.2f}, "
            f"archetype={archetype})"
        )

