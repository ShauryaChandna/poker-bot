"""
Opponent Tracker

Stores and updates PlayerProfile for opponents across hands.
Tracks actions and updates statistics after each hand.
"""

from typing import Dict, Optional, List
from ..opponent_modeling.player_profile import PlayerProfile
from ..opponent_modeling.hand_history import Street


class OpponentTracker:
    """
    Tracks opponent profiles across multiple hands.
    
    Maintains in-memory storage of PlayerProfile objects and updates
    them based on observed actions during gameplay.
    """
    
    def __init__(self):
        """Initialize opponent tracker with empty profiles."""
        self.profiles: Dict[str, PlayerProfile] = {}
        self.current_hand_actions: Dict[str, List[Dict]] = {}
    
    def get_profile(self, player_id: str) -> PlayerProfile:
        """
        Get or create player profile.
        
        Args:
            player_id: Player identifier (name)
            
        Returns:
            PlayerProfile for this player
        """
        if player_id not in self.profiles:
            self.profiles[player_id] = PlayerProfile(player_id=player_id)
        return self.profiles[player_id]
    
    def record_action(
        self,
        player_id: str,
        action: str,
        street: Street,
        amount: int = 0,
        current_bet: int = 0,
        is_preflop_raiser: bool = False,
        position: Optional[str] = None
    ):
        """
        Record an action for later processing.
        
        Args:
            player_id: Player who acted
            action: Action type (fold, check, call, raise, bet)
            street: Current street
            amount: Amount bet/raised to
            current_bet: Current bet to call
            is_preflop_raiser: Whether this player raised preflop
            position: Player position (BTN, SB, BB)
        """
        if player_id not in self.current_hand_actions:
            self.current_hand_actions[player_id] = []
        
        self.current_hand_actions[player_id].append({
            'action': action,
            'street': street,
            'amount': amount,
            'current_bet': current_bet,
            'is_preflop_raiser': is_preflop_raiser,
            'position': position
        })
    
    def end_hand(self, showdown_results: Optional[Dict[str, bool]] = None):
        """
        Process all recorded actions and update player profiles.
        
        Called at end of hand to update statistics.
        
        Args:
            showdown_results: Dict mapping player_id -> won_at_showdown (if hand went to showdown)
        """
        for player_id, actions in self.current_hand_actions.items():
            profile = self.get_profile(player_id)
            
            # Process preflop actions
            preflop_actions = [a for a in actions if a['street'] == Street.PREFLOP]
            if preflop_actions:
                self._update_preflop_stats(profile, preflop_actions)
            
            # Process postflop actions
            postflop_actions = [a for a in actions if a['street'] != Street.PREFLOP]
            if postflop_actions:
                self._update_postflop_stats(profile, postflop_actions, actions)
            
            # Update showdown stats if applicable
            if showdown_results and player_id in showdown_results:
                profile.update_showdown(won=showdown_results[player_id])
        
        # Clear actions for next hand
        self.current_hand_actions.clear()
    
    def _update_preflop_stats(self, profile: PlayerProfile, preflop_actions: List[Dict]):
        """Update preflop statistics from actions."""
        # Check for voluntary put in pot (VPIP)
        # VPIP = any call/raise that isn't a forced blind
        is_voluntary = False
        is_raise = False
        is_three_bet = False
        could_three_bet = False
        
        for i, action_dict in enumerate(preflop_actions):
            action = action_dict['action'].lower()
            current_bet = action_dict['current_bet']
            
            # Check if facing a raise (for 3-bet detection)
            if current_bet > 0 and i == 0:
                could_three_bet = True
            
            if action in ['call', 'raise', 'bet']:
                is_voluntary = True
                
                if action in ['raise', 'bet']:
                    is_raise = True
                    
                    # Check if this is a 3-bet (raising after facing a raise)
                    if could_three_bet:
                        is_three_bet = True
        
        # Only count as a hand played if player saw preflop action
        if preflop_actions:
            profile.update_preflop_action(
                action=preflop_actions[-1]['action'],
                is_raise=is_raise,
                is_voluntary=is_voluntary,
                could_three_bet=could_three_bet,
                is_three_bet=is_three_bet
            )
    
    def _update_postflop_stats(
        self,
        profile: PlayerProfile,
        postflop_actions: List[Dict],
        all_actions: List[Dict]
    ):
        """Update postflop statistics from actions."""
        # Check if player was preflop raiser (for c-bet detection)
        was_preflop_raiser = any(a.get('is_preflop_raiser', False) for a in all_actions)
        
        for action_dict in postflop_actions:
            action = action_dict['action'].lower()
            street = action_dict['street']
            
            is_bet = action in ['bet', 'raise']
            is_raise = action == 'raise'
            is_call = action == 'call'
            is_fold = action == 'fold'
            
            # Detect c-bet facing (simplified - if facing bet on flop and wasn't preflop raiser)
            faced_cbet = (
                street == Street.FLOP and
                not was_preflop_raiser and
                action_dict['current_bet'] > 0
            )
            
            profile.update_postflop_action(
                action=action,
                is_bet=is_bet,
                is_raise=is_raise,
                is_call=is_call,
                is_fold=is_fold,
                faced_cbet=faced_cbet
            )
    
    def get_all_profiles(self) -> Dict[str, PlayerProfile]:
        """Get all tracked player profiles."""
        return self.profiles.copy()
    
    def reset(self):
        """Clear all tracked profiles (for new session)."""
        self.profiles.clear()
        self.current_hand_actions.clear()
    
    def __repr__(self) -> str:
        """String representation."""
        return f"OpponentTracker(players={len(self.profiles)})"

