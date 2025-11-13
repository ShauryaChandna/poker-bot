"""
Bot Strategy Orchestrator

High-level bot that coordinates opponent tracking, equity calculations,
and decision making.
"""

from typing import List, Optional, Dict, Tuple
from ..engine.card import Card
from ..engine.round import Street as EngineStreet
from ..opponent_modeling.hand_history import Street
from ..simulation.equity_calculator import EquityCalculator
from .opponent_tracker import OpponentTracker
from .equity_strategy import EquityStrategy, Action
from .bet_sizing import BetSizer


class BotStrategy:
    """
    Complete poker bot strategy.
    
    Manages:
    - Opponent tracking across hands
    - Equity-based decision making
    - Action recording and profile updates
    """
    
    def __init__(
        self,
        bot_name: str,
        opponent_name: str,
        aggression_level: float = 1.0,
        n_simulations: int = 5000
    ):
        """
        Initialize bot strategy.
        
        Args:
            bot_name: Name of this bot
            opponent_name: Name of opponent to track
            aggression_level: How aggressive to play (0.5-2.0)
            n_simulations: Monte Carlo simulations for equity
        """
        self.bot_name = bot_name
        self.opponent_name = opponent_name
        
        # Initialize components
        self.tracker = OpponentTracker()
        self.equity_calc = EquityCalculator(default_simulations=n_simulations)
        self.bet_sizer = BetSizer()
        self.strategy = EquityStrategy(
            equity_calculator=self.equity_calc,
            bet_sizer=self.bet_sizer,
            aggression_level=aggression_level
        )
        
        # Track who was preflop raiser (for c-bet detection)
        self.preflop_raiser: Optional[str] = None
    
    def decide_action(
        self,
        hero_hand: List[Card],
        board: List[Card],
        pot: int,
        current_bet: int,
        hero_current_bet: int,
        hero_stack: int,
        street: EngineStreet,
        position: str,
        legal_actions: Dict,
        big_blind: int,
        opponent_last_action: Optional[str] = None
    ) -> Tuple[str, int]:
        """
        Make a decision for the bot.
        
        Args:
            hero_hand: Bot's hole cards
            board: Community cards
            pot: Current pot size
            current_bet: Current bet to match
            hero_current_bet: Bot's current bet this round
            hero_stack: Bot's remaining stack
            street: Current street
            position: Bot's position
            legal_actions: Dict of legal actions
            big_blind: Big blind amount
            opponent_last_action: Opponent's most recent action
            
        Returns:
            Tuple of (action_string, amount)
        """
        # Convert engine street to opponent modeling street
        om_street = self._convert_street(street)
        
        # Get opponent profile
        opponent_profile = self.tracker.get_profile(self.opponent_name)
        
        # Use appropriate strategy based on street
        if om_street == Street.PREFLOP:
            action, amount = self.strategy.decide_preflop_action(
                hero_hand=hero_hand,
                opponent_profile=opponent_profile,
                pot=pot,
                current_bet=current_bet,
                hero_current_bet=hero_current_bet,
                hero_stack=hero_stack,
                position=position,
                bb=big_blind,
                legal_actions=legal_actions
            )
        else:
            action, amount = self.strategy.decide_action(
                hero_hand=hero_hand,
                board=board,
                opponent_profile=opponent_profile,
                pot=pot,
                current_bet=current_bet,
                hero_current_bet=hero_current_bet,
                hero_stack=hero_stack,
                street=om_street,
                position=position,
                legal_actions=legal_actions,
                last_action=opponent_last_action,
                big_blind=big_blind
            )
        
        # Convert Action enum to string and validate against legal actions
        action_str, final_amount = self._validate_action(
            action, amount, legal_actions, current_bet, hero_stack
        )
        
        return action_str, final_amount
    
    def record_action(
        self,
        player_name: str,
        action: str,
        amount: int,
        street: EngineStreet,
        current_bet: int,
        position: Optional[str] = None
    ):
        """
        Record an action for opponent tracking.
        
        Args:
            player_name: Who acted
            action: Action taken
            amount: Amount bet/raised (if any)
            street: Current street
            current_bet: Bet to match
            position: Player position
        """
        # Track preflop raiser
        if street == EngineStreet.PREFLOP and action.lower() in ['raise', 'bet']:
            self.preflop_raiser = player_name
        
        # Only track opponent actions (not bot's own)
        if player_name == self.opponent_name:
            om_street = self._convert_street(street)
            is_preflop_raiser = (self.preflop_raiser == player_name)
            
            self.tracker.record_action(
                player_id=player_name,
                action=action,
                street=om_street,
                amount=amount,
                current_bet=current_bet,
                is_preflop_raiser=is_preflop_raiser,
                position=position
            )
    
    def end_hand(self, winner: str, showdown: bool = False):
        """
        End hand and update opponent profile.
        
        Args:
            winner: Name of hand winner
            showdown: Whether hand went to showdown
        """
        # Update showdown stats if applicable
        showdown_results = None
        if showdown:
            showdown_results = {
                self.opponent_name: (winner == self.opponent_name)
            }
        
        # Process all recorded actions
        self.tracker.end_hand(showdown_results)
        
        # Reset preflop raiser
        self.preflop_raiser = None
    
    def get_opponent_stats(self) -> Dict:
        """Get opponent statistics for display/debugging."""
        profile = self.tracker.get_profile(self.opponent_name)
        return profile.to_dict()
    
    def _convert_street(self, engine_street: EngineStreet) -> Street:
        """Convert engine street to opponent modeling street."""
        mapping = {
            EngineStreet.PREFLOP: Street.PREFLOP,
            EngineStreet.FLOP: Street.FLOP,
            EngineStreet.TURN: Street.TURN,
            EngineStreet.RIVER: Street.RIVER,
            EngineStreet.SHOWDOWN: Street.RIVER  # Treat showdown as river
        }
        return mapping.get(engine_street, Street.PREFLOP)
    
    def _validate_action(
        self,
        action: Action,
        amount: int,
        legal_actions: Dict,
        current_bet: int,
        stack: int
    ) -> Tuple[str, int]:
        """
        Validate and convert action to legal format.
        
        Ensures action is legal and amounts are correct.
        """
        # Convert Action enum to string
        action_str = action.value
        
        # Check if action is legal
        if action == Action.FOLD:
            if legal_actions.get('fold'):
                return 'fold', 0
            # Can't fold if check is available
            elif legal_actions.get('check'):
                return 'check', 0
            else:
                return 'fold', 0
        
        elif action == Action.CHECK:
            if legal_actions.get('check'):
                return 'check', 0
            # Can't check if facing bet, must call or fold
            elif legal_actions.get('call'):
                return 'call', current_bet
            else:
                return 'fold', 0
        
        elif action == Action.CALL:
            if legal_actions.get('call'):
                return 'call', current_bet
            elif legal_actions.get('check'):
                # No bet to call, check instead
                return 'check', 0
            else:
                return 'fold', 0
        
        elif action == Action.BET:
            bet_info = legal_actions.get('bet')
            if bet_info:
                # Clamp amount to legal range
                min_bet = bet_info['min']
                max_bet = bet_info['max']
                clamped_amount = max(min_bet, min(amount, max_bet))
                return 'bet', clamped_amount
            elif legal_actions.get('check'):
                # Can't bet, check instead
                return 'check', 0
            else:
                return 'fold', 0
        
        elif action == Action.RAISE:
            raise_info = legal_actions.get('raise')
            if raise_info:
                # Clamp amount to legal range
                min_raise = raise_info['min']
                max_raise = raise_info['max']
                clamped_amount = max(min_raise, min(amount, max_raise))
                return 'raise', clamped_amount
            elif legal_actions.get('call'):
                # Can't raise, call instead
                return 'call', current_bet
            elif legal_actions.get('check'):
                return 'check', 0
            else:
                return 'fold', 0
        
        # Default: fold
        return 'fold', 0
    
    def reset(self):
        """Reset bot state (for new session)."""
        self.tracker.reset()
        self.equity_calc.clear_cache()
        self.preflop_raiser = None

