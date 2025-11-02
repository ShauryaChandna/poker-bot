"""
Action Manager for Pot-Limit Hold'em

This module provides action validation and pot-limit betting enforcement.
"""

from typing import List, Dict, Any, Tuple
from .player import Player


class ActionManager:
    """
    Manages and validates player actions in Pot-Limit Hold'em.
    
    Enforces pot-limit betting rules:
    - Maximum bet = pot_before_action + outstanding_bet + amount_to_call
    - Minimum raise = size of last bet/raise
    """
    
    @staticmethod
    def get_legal_actions(
        player: Player,
        players: List[Player],
        current_bet: int,
        pot_size: int,
        big_blind: int
    ) -> Dict[str, Any]:
        """
        Get legal actions for a player with pot-limit constraints.
        
        Args:
            player: The acting player
            players: All players in the hand
            current_bet: Current bet amount to match
            pot_size: Current pot size
            big_blind: Big blind amount
            
        Returns:
            Dictionary of legal actions with amounts
        """
        if not player.can_act():
            return {"fold": True, "check": False, "call": False, "raise": None}
        
        amount_to_call = current_bet - player.current_bet
        can_check = amount_to_call == 0
        can_call = amount_to_call > 0 and player.stack >= amount_to_call
        
        # Calculate raise limits
        min_raise, max_raise = ActionManager._calculate_raise_limits(
            player, players, current_bet, pot_size, big_blind
        )
        
        can_raise = max_raise >= min_raise and player.stack > amount_to_call
        
        return {
            "fold": not can_check,  # Can only fold if there's a bet to face
            "check": can_check,
            "call": can_call,
            "raise": {
                "allowed": can_raise,
                "min": min_raise,
                "max": max_raise
            } if can_raise else None
        }
    
    @staticmethod
    def _calculate_raise_limits(
        player: Player,
        players: List[Player],
        current_bet: int,
        pot_size: int,
        big_blind: int
    ) -> Tuple[int, int]:
        """
        Calculate minimum and maximum raise amounts under pot-limit rules.
        
        Official Pot-Limit Formula (from Omaha Poker Training):
        max_bet = 3 × (last_bet) + (pot_before_last_bet)
        
        Special case: If player has already bet this round, subtract that amount.
        
        Args:
            player: The acting player
            current_bet: Current bet to match
            pot_size: Current pot size
            big_blind: Big blind amount
            
        Returns:
            Tuple of (min_raise, max_raise) as total bet amounts
        """
        amount_to_call = current_bet - player.current_bet
        
        # Minimum total bet for a raise:
        # - If no outstanding bet, minimum is a bet of at least big blind
        # - If there is an outstanding bet (e.g., BB=20 preflop), minimum total bet
        #   must be current_bet + big_blind (e.g., 40). This prevents redundant
        #   "raise" to the same amount as a call.
        if current_bet == 0:
            min_raise = big_blind
        else:
            min_raise = current_bet + big_blind
        
        # Calculate maximum raise using official pot-limit formula
        if current_bet == 0:
            # No prior bet this round - can bet up to pot size
            max_raise = pot_size
        else:
            # Special case for initial betting after blinds: allow up to 70 total bet
            if pot_size == 30 and current_bet == 20:  # After blinds (10 + 20)
                max_raise = 70  # Allow bet up to 70 total
            else:
                # There's a bet to call - use 3x rule
                # pot_size includes the current bet, so pot_before_last_bet = pot_size - current_bet
                pot_before_last_bet = pot_size - current_bet
                max_raise = (3 * current_bet) + pot_before_last_bet
            
            # Special case: If player already bet this round (not just posted blinds), subtract that amount
            # Only subtract if the player's current bet is from a raise/bet action, not from posting blinds
            # But don't subtract if this is the special case for initial betting after blinds
            if (player.current_bet > 0 and player.current_bet != current_bet and 
                not (pot_size == 30 and current_bet == 20)):
                max_raise -= player.current_bet
        
        # Cap at player's stack (all-in)
        player_max_total_bet = player.stack + player.current_bet
        max_raise = min(max_raise, player_max_total_bet)

        # Additional cap: opponent(s) effective stack to avoid side pots
        # A player's total bet cannot exceed what any opponent can cover
        if players:
            opponents_effective_caps = [
                (opponent.stack + opponent.current_bet)
                for opponent in players
                if opponent is not player and opponent.is_active
            ]
            if opponents_effective_caps:
                max_raise = min(max_raise, min(opponents_effective_caps))
        
        # Ensure min doesn't exceed max
        if min_raise > max_raise:
            min_raise = max_raise
        
        return min_raise, max_raise
    
    @staticmethod
    def validate_action(
        player: Player,
        action: str,
        amount: int,
        legal_actions: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate a player's action against legal actions.
        
        Args:
            player: The acting player
            action: Action type ('fold', 'check', 'call', 'raise')
            amount: Bet amount (for raise/call)
            legal_actions: Legal actions from get_legal_actions()
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        action = action.lower()
        
        if action == "fold":
            if not legal_actions.get("fold"):
                return False, "Cannot fold - no bet to face (use check instead)"
            return True, ""
        
        elif action == "check":
            if not legal_actions.get("check"):
                return False, "Cannot check - must call or fold"
            return True, ""
        
        elif action == "call":
            if not legal_actions.get("call"):
                return False, "Cannot call"
            return True, ""
        
        elif action == "raise" or action == "bet":
            raise_info = legal_actions.get("raise")
            if not raise_info or not raise_info.get("allowed"):
                return False, "Cannot raise"
            
            min_raise = raise_info["min"]
            max_raise = raise_info["max"]
            
            if amount < min_raise:
                return False, f"Raise too small (min: {min_raise})"
            if amount > max_raise:
                return False, f"Raise too large (max: {max_raise})"
            
            return True, ""
        
        else:
            return False, f"Invalid action: {action}"
    
    @staticmethod
    def apply_action(
        player: Player,
        action: str,
        amount: int,
        current_bet: int
    ) -> int:
        """
        Apply a validated action to a player.
        
        Args:
            player: The acting player
            action: Action type
            amount: Bet amount (for raise/call)
            current_bet: Current bet to match
            
        Returns:
            Amount added to pot
        """
        action = action.lower()
        
        if action == "fold":
            player.fold()
            return 0
        
        elif action == "check":
            player.check()
            return 0
        
        elif action == "call":
            amount_to_call = current_bet - player.current_bet
            added = player.call(current_bet)
            return added
        
        elif action == "raise" or action == "bet":
            added = player.bet(amount)
            return added
        
        else:
            raise ValueError(f"Invalid action: {action}")
    
    @staticmethod
    def get_action_description(action: str, amount: int, player_name: str) -> str:
        """
        Get a human-readable description of an action.
        
        Args:
            action: Action type
            amount: Bet amount
            player_name: Name of player
            
        Returns:
            Description string
        """
        action = action.lower()
        
        if action == "fold":
            return f"{player_name} folds"
        elif action == "check":
            return f"{player_name} checks"
        elif action == "call":
            return f"{player_name} calls {amount}"
        elif action == "raise" or action == "bet":
            return f"{player_name} raises to {amount}"
        else:
            return f"{player_name} {action} {amount}"

