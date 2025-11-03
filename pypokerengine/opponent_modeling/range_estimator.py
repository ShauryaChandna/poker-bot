"""
Rule-Based Range Estimator

Uses hand-crafted heuristics and player statistics to estimate opponent ranges.
Works immediately without training data.
"""

from typing import Optional, Dict, List
from .player_profile import PlayerProfile, PlayerArchetype
from .hand_history import Street
from ..simulation.hand_range import HandRange


class RuleBasedRangeEstimator:
    """
    Estimates opponent hand ranges using rule-based heuristics.
    
    Uses player statistics (VPIP, PFR, aggression) to narrow down
    likely holdings based on their actions.
    """
    
    # Default range templates for different archetypes
    ARCHETYPE_RANGES = {
        PlayerArchetype.TIGHT_AGGRESSIVE: {
            'preflop_raise': "JJ+,AQs+,AKo",  # ~8% range
            'preflop_call': "77-TT,ATs+,AJo+,KQs",  # ~5% range
            'preflop_3bet': "QQ+,AKs,AKo",  # ~3% range
            'cbet_flop': 0.75,  # C-bet 75% of time
            'barrel_turn': 0.50,  # Continue betting turn 50%
            'barrel_river': 0.40,  # Continue betting river 40%
        },
        PlayerArchetype.TIGHT_PASSIVE: {
            'preflop_raise': "TT+,AQs+,AKo",  # ~5% range
            'preflop_call': "22-99,A2s+,A9o+,KTs+,KQo,QJs",  # ~15% range
            'preflop_3bet': "KK+,AKs",  # ~1.5% range
            'cbet_flop': 0.35,  # Rarely c-bets
            'barrel_turn': 0.20,
            'barrel_river': 0.15,
        },
        PlayerArchetype.LOOSE_AGGRESSIVE: {
            'preflop_raise': "22+,A2s+,A5o+,K5s+,K9o+,Q8s+,QTo+,J8s+,JTo,T8s+,97s+,87s",  # ~35% range
            'preflop_call': "A2s+,A2o+,K2s+,K2o+,Q2s+,Q7o+,J6s+,J9o+,T6s+,T9o,96s+,86s+,75s+",  # ~25% range
            'preflop_3bet': "88+,ATs+,AJo+,KQs",  # ~8% range
            'cbet_flop': 0.85,  # C-bets aggressively
            'barrel_turn': 0.65,
            'barrel_river': 0.50,
        },
        PlayerArchetype.LOOSE_PASSIVE: {
            'preflop_raise': "99+,AJs+,AQo+,KQs",  # ~6% range
            'preflop_call': "22+,A2s+,A2o+,K2s+,K7o+,Q5s+,Q9o+,J7s+,JTo,T7s+,97s+,87s,76s",  # ~40% range
            'preflop_3bet': "QQ+,AKs",  # ~2% range
            'cbet_flop': 0.30,
            'barrel_turn': 0.15,
            'barrel_river': 0.10,
        },
    }
    
    # Default range for unknown players (conservative assumption)
    DEFAULT_RANGES = {
        'preflop_raise': "77+,ATs+,AJo+,KQs",  # ~10% range
        'preflop_call': "22-66,A2s+,A9o+,KTs+,KJo+,QTs+,JTs",  # ~12% range
        'preflop_3bet': "JJ+,AQs+,AKo",  # ~4% range
        'cbet_flop': 0.60,
        'barrel_turn': 0.40,
        'barrel_river': 0.30,
    }
    
    def __init__(self, player_profile: Optional[PlayerProfile] = None):
        """
        Initialize range estimator.
        
        Args:
            player_profile: Player statistics to use for estimation.
                           If None, uses default ranges.
        """
        self.player_profile = player_profile
    
    def estimate_preflop_range(
        self,
        action: str,
        position: Optional[str] = None,
        facing_raise: bool = False
    ) -> HandRange:
        """
        Estimate preflop range based on action.
        
        Args:
            action: Player's action ("raise", "call", "3bet", "fold")
            position: Player's position (BTN, SB, BB)
            facing_raise: Whether player is facing a raise
            
        Returns:
            HandRange object representing estimated range
        """
        archetype = self._get_archetype()
        ranges = self._get_range_template(archetype)
        
        # Base range selection
        if action.lower() in ['raise', 'bet']:
            if facing_raise:
                # This is a 3-bet
                range_str = ranges['preflop_3bet']
            else:
                # This is an open raise
                range_str = ranges['preflop_raise']
                
                # Widen range for button (position adjustment)
                if position == 'BTN':
                    range_str = self._widen_range(range_str, factor=1.3)
        
        elif action.lower() == 'call':
            range_str = ranges['preflop_call']
            
            # Adjust based on player stats
            if self.player_profile:
                # If player has high VPIP, widen calling range
                if self.player_profile.vpip > 0.30:
                    range_str = self._widen_range(range_str, factor=1.2)
        
        elif action.lower() in ['fold', 'check']:
            # Folding means hand is NOT in raising/calling range
            # Return empty range or very weak hands
            range_str = "72o,73o,82o,83o,92o,93o"  # Bottom of range
        
        else:
            # Unknown action, use default
            range_str = ranges['preflop_raise']
        
        return HandRange.from_string(range_str)
    
    def estimate_postflop_range(
        self,
        preflop_range: HandRange,
        street: Street,
        action: str,
        board: List[str],
        pot_size: int = 0,
        bet_size: int = 0
    ) -> HandRange:
        """
        Estimate postflop range by narrowing preflop range.
        
        Args:
            preflop_range: Estimated preflop range
            street: Current street (flop, turn, river)
            action: Player's action on this street
            board: Community cards
            pot_size: Current pot size
            bet_size: Size of bet made (if any)
            
        Returns:
            Narrowed HandRange based on action
        """
        archetype = self._get_archetype()
        ranges = self._get_range_template(archetype)
        
        # Start with preflop range
        estimated_range = preflop_range
        
        # Apply continuation logic based on action
        if action.lower() in ['bet', 'raise']:
            # Player is betting - likely has value or good draws
            # Keep top X% of range based on aggression
            if street == Street.FLOP:
                keep_pct = ranges['cbet_flop']
            elif street == Street.TURN:
                keep_pct = ranges['barrel_turn']
            else:  # River
                keep_pct = ranges['barrel_river']
            
            # Narrow range to top keep_pct
            estimated_range = self._narrow_range(preflop_range, keep_pct)
            
            # If large bet (> 0.75 pot), narrow further
            if pot_size > 0 and bet_size / pot_size > 0.75:
                estimated_range = self._narrow_range(estimated_range, 0.7)
        
        elif action.lower() == 'call':
            # Calling typically means medium strength or draws
            # Remove weakest hands (bottom 30%)
            estimated_range = self._narrow_range(preflop_range, 0.70)
        
        elif action.lower() == 'check':
            # Checking could be weak or trap
            # Slightly narrow range (remove top and bottom)
            if self.player_profile and self.player_profile.aggression_factor > 2.5:
                # Aggressive player checking might be trapping
                # Keep wider range
                estimated_range = preflop_range
            else:
                # Passive player checking is likely weak
                estimated_range = self._narrow_range(preflop_range, 0.80)
        
        elif action.lower() == 'fold':
            # Folded - not relevant for future streets
            estimated_range = HandRange(set())
        
        return estimated_range
    
    def _get_archetype(self) -> PlayerArchetype:
        """Get player archetype, or UNKNOWN if no profile."""
        if self.player_profile is None:
            return PlayerArchetype.UNKNOWN
        return self.player_profile.get_archetype()
    
    def _get_range_template(self, archetype: PlayerArchetype) -> Dict:
        """Get range template for an archetype."""
        if archetype == PlayerArchetype.UNKNOWN:
            return self.DEFAULT_RANGES
        return self.ARCHETYPE_RANGES.get(archetype, self.DEFAULT_RANGES)
    
    def _widen_range(self, range_str: str, factor: float = 1.2) -> str:
        """
        Widen a range by adding more hands (simplified heuristic).
        
        For now, returns the same range. In practice, you'd add
        more suited connectors, weaker aces, etc.
        
        Args:
            range_str: Original range string
            factor: How much to widen (1.2 = 20% wider)
            
        Returns:
            Widened range string
        """
        # TODO: Implement intelligent range widening
        # For now, just return original range
        # In production, you'd parse the range and add adjacent hands
        return range_str
    
    def _narrow_range(self, hand_range: HandRange, keep_percentage: float) -> HandRange:
        """
        Narrow a range to top X% of hands.
        
        This is a simplified implementation that keeps the same range.
        In practice, you'd rank hands by equity and keep top X%.
        
        Args:
            hand_range: Original range
            keep_percentage: Percentage to keep (0-1)
            
        Returns:
            Narrowed HandRange
        """
        # TODO: Implement equity-based range narrowing
        # For now, return same range
        # In production, you'd:
        # 1. Calculate equity of each hand combo vs random
        # 2. Sort by equity
        # 3. Keep top X%
        return hand_range
    
    def estimate_range_from_sequence(
        self,
        actions: List[Dict[str, any]],
        board: Optional[List[str]] = None
    ) -> HandRange:
        """
        Estimate range from a sequence of actions across streets.
        
        Args:
            actions: List of action dicts with keys:
                     {'street': Street, 'action': str, 'amount': int}
            board: Community cards (if postflop)
            
        Returns:
            Final estimated HandRange
        """
        # Start with preflop action
        if not actions:
            return HandRange(set())
        
        first_action = actions[0]
        current_range = self.estimate_preflop_range(
            action=first_action.get('action', 'fold'),
            position=first_action.get('position'),
            facing_raise=first_action.get('facing_raise', False)
        )
        
        # Narrow through subsequent streets
        for i, action_dict in enumerate(actions[1:], 1):
            street = action_dict.get('street', Street.FLOP)
            action = action_dict.get('action', 'fold')
            pot_size = action_dict.get('pot_size', 0)
            bet_size = action_dict.get('amount', 0)
            
            current_range = self.estimate_postflop_range(
                preflop_range=current_range,
                street=street,
                action=action,
                board=board or [],
                pot_size=pot_size,
                bet_size=bet_size
            )
        
        return current_range

