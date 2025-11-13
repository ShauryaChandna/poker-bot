"""
Equity-Based Strategy Module

Core decision-making logic using equity calculations, pot odds, and opponent modeling.
Makes intelligent +EV decisions based on mathematical analysis.
"""

import random
from typing import List, Optional, Dict, Tuple
from enum import Enum

from ..engine.card import Card
from ..opponent_modeling.player_profile import PlayerProfile
from ..opponent_modeling.range_estimator import RuleBasedRangeEstimator
from ..opponent_modeling.hand_history import Street
from ..simulation.equity_calculator import EquityCalculator
from ..simulation.hand_range import HandRange
from .bet_sizing import BetSizer, BetType


class Action(Enum):
    """Possible poker actions."""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"


class EquityStrategy:
    """
    Equity-based poker strategy.
    
    Makes decisions based on:
    1. Estimated opponent range
    2. Hero's equity vs that range
    3. Pot odds and implied odds
    4. Opponent tendencies
    5. Position and board texture
    """
    
    # Strategy thresholds (tunable parameters)
    VALUE_BET_THRESHOLD = 0.60      # Bet for value if equity > 60%
    THIN_VALUE_THRESHOLD = 0.53     # Thin value if equity > 53%
    CALL_THRESHOLD_BONUS = 0.08     # Call if equity > pot_odds + 8%
    BLUFF_FREQUENCY = 0.18          # Bluff 18% of the time when weak
    AGGRESSIVE_BLUFF_FREQ = 0.25    # More bluffs vs tight players
    
    def __init__(
        self,
        equity_calculator: Optional[EquityCalculator] = None,
        bet_sizer: Optional[BetSizer] = None,
        aggression_level: float = 1.0
    ):
        """
        Initialize strategy.
        
        Args:
            equity_calculator: EquityCalculator instance
            bet_sizer: BetSizer instance
            aggression_level: Multiplier for aggression (0.5-2.0)
        """
        self.equity_calc = equity_calculator or EquityCalculator(default_simulations=5000)
        self.bet_sizer = bet_sizer or BetSizer()
        self.aggression = aggression_level
    
    def decide_action(
        self,
        hero_hand: List[Card],
        board: List[Card],
        opponent_profile: Optional[PlayerProfile],
        pot: int,
        current_bet: int,
        hero_current_bet: int,
        hero_stack: int,
        street: Street,
        position: str = "BTN",
        legal_actions: Optional[Dict] = None,
        last_action: Optional[str] = None,
        big_blind: int = 20
    ) -> Tuple[Action, int]:
        """
        Decide action based on equity and game state.
        
        Args:
            hero_hand: Hero's hole cards
            board: Community cards
            opponent_profile: Opponent's PlayerProfile (None if no data)
            pot: Current pot size
            current_bet: Current bet to call
            hero_current_bet: Hero's current bet this round
            hero_stack: Hero's remaining stack
            street: Current street
            position: Hero's position
            legal_actions: Dict of legal actions
            last_action: Opponent's last action
            big_blind: Big blind amount
            
        Returns:
            Tuple of (Action, amount)
        """
        # Estimate opponent's range based on their last action
        opponent_range = self._estimate_opponent_range(
            opponent_profile,
            last_action or "unknown",
            street,
            board,
            current_bet,
            pot
        )
        
        # Calculate equity vs opponent's range
        equity = self._calculate_equity(hero_hand, opponent_range, board)
        
        # Calculate pot odds if facing a bet
        call_amount = current_bet - hero_current_bet
        pot_odds = call_amount / (pot + call_amount) if call_amount > 0 else 0
        
        # Decide action based on situation
        if current_bet == hero_current_bet:
            # No bet to face - decide to check or bet
            return self._decide_check_or_bet(
                equity, pot, hero_stack, street, board,
                opponent_profile, position, legal_actions
            )
        else:
            # Facing a bet - decide to fold, call, or raise
            return self._decide_facing_bet(
                equity, pot_odds, pot, current_bet, hero_current_bet,
                hero_stack, street, board, opponent_profile,
                position, legal_actions, call_amount
            )
    
    def _estimate_opponent_range(
        self,
        opponent_profile: Optional[PlayerProfile],
        last_action: str,
        street: Street,
        board: List[Card],
        bet_amount: int,
        pot: int
    ) -> HandRange:
        """Estimate opponent's likely range based on their action."""
        estimator = RuleBasedRangeEstimator(opponent_profile)
        
        if street == Street.PREFLOP:
            # Estimate preflop range
            facing_raise = bet_amount > 0
            return estimator.estimate_preflop_range(
                action=last_action,
                position=None,
                facing_raise=facing_raise
            )
        else:
            # Estimate postflop range (need preflop range first)
            # Assume opponent played reasonable preflop range
            preflop_range = estimator.estimate_preflop_range(
                action="raise" if bet_amount > 0 else "call",
                position=None,
                facing_raise=False
            )
            
            board_strs = [str(c) for c in board]
            return estimator.estimate_postflop_range(
                preflop_range=preflop_range,
                street=street,
                action=last_action,
                board=board_strs,
                pot_size=pot,
                bet_size=bet_amount
            )
    
    def _calculate_equity(
        self,
        hero_hand: List[Card],
        opponent_range: HandRange,
        board: List[Card]
    ) -> float:
        """Calculate hero's equity vs opponent range."""
        try:
            # Convert Card objects to strings with ASCII suits
            def card_to_str(card: Card) -> str:
                """Convert Card to string format like 'Ah', 'Kd'."""
                rank_map = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T'}
                rank_str = rank_map.get(card.rank, str(card.rank))
                
                # Convert unicode suit to ASCII
                suit_str = str(card.suit)
                suit_map = {'♥': 'h', '♦': 'd', '♣': 'c', '♠': 's',
                           'h': 'h', 'd': 'd', 'c': 'c', 's': 's'}
                suit_ascii = suit_map.get(suit_str, 'h')
                
                return f"{rank_str}{suit_ascii}"
            
            hero_str = ''.join([card_to_str(c) for c in hero_hand])
            
            # Convert board to string format (concatenated)
            board_str = None
            if board:
                board_str = ''.join([card_to_str(c) for c in board])
            
            result = self.equity_calc.calculate_equity(
                hero_hand=hero_str,
                villain_range=opponent_range,
                board=board_str,
                n_simulations=5000
            )
            return result.equity
        except Exception as e:
            # Fallback: assume 50% equity if calculation fails
            print(f"Equity calculation failed: {e}. Using 50% default.")
            return 0.50
    
    def _decide_check_or_bet(
        self,
        equity: float,
        pot: int,
        stack: int,
        street: Street,
        board: List[Card],
        opponent_profile: Optional[PlayerProfile],
        position: str,
        legal_actions: Optional[Dict]
    ) -> Tuple[Action, int]:
        """Decide whether to check or bet when no bet to face."""
        # High equity -> bet for value
        if equity >= self.VALUE_BET_THRESHOLD:
            bet_amount = self.bet_sizer.get_bet_size(
                pot=pot,
                stack=stack,
                bet_type=BetType.VALUE,
                street=street.value.lower()
            )
            return Action.BET, bet_amount
        
        # Medium equity -> bet for thin value (sometimes)
        elif equity >= self.THIN_VALUE_THRESHOLD:
            # Bet 60% of the time with medium hands
            if random.random() < 0.60:
                bet_amount = self.bet_sizer.get_bet_size(
                    pot=pot,
                    stack=stack,
                    bet_type=BetType.THIN_VALUE,
                    street=street.value.lower()
                )
                return Action.BET, bet_amount
            else:
                return Action.CHECK, 0
        
        # Low equity -> bluff sometimes, check mostly
        else:
            # Adjust bluff frequency based on opponent
            bluff_freq = self._get_bluff_frequency(opponent_profile)
            
            if random.random() < bluff_freq:
                # Bluff!
                bet_amount = self.bet_sizer.get_bet_size(
                    pot=pot,
                    stack=stack,
                    bet_type=BetType.BLUFF,
                    street=street.value.lower()
                )
                return Action.BET, bet_amount
            else:
                return Action.CHECK, 0
    
    def _decide_facing_bet(
        self,
        equity: float,
        pot_odds: float,
        pot: int,
        current_bet: int,
        hero_current_bet: int,
        stack: int,
        street: Street,
        board: List[Card],
        opponent_profile: Optional[PlayerProfile],
        position: str,
        legal_actions: Optional[Dict],
        call_amount: int
    ) -> Tuple[Action, int]:
        """Decide action when facing a bet."""
        # Very high equity -> raise for value
        if equity >= 0.70:
            # Raise 75% of the time, call 25% (for deception)
            if random.random() < 0.75:
                raise_amount = self.bet_sizer.get_raise_size(
                    pot=pot,
                    current_bet=current_bet,
                    hero_bet=hero_current_bet,
                    stack=stack,
                    bet_type=BetType.VALUE,
                    street=street.value.lower()
                )
                return Action.RAISE, raise_amount
            else:
                return Action.CALL, current_bet
        
        # Good equity -> raise sometimes, call mostly
        elif equity >= self.VALUE_BET_THRESHOLD:
            if random.random() < 0.30:  # Raise 30% for value
                raise_amount = self.bet_sizer.get_raise_size(
                    pot=pot,
                    current_bet=current_bet,
                    hero_bet=hero_current_bet,
                    stack=stack,
                    bet_type=BetType.VALUE,
                    street=street.value.lower()
                )
                return Action.RAISE, raise_amount
            else:
                return Action.CALL, current_bet
        
        # Medium equity -> call if profitable, fold if not
        elif equity >= pot_odds + self.CALL_THRESHOLD_BONUS:
            # Profitable call
            return Action.CALL, current_bet
        
        # Low equity but occasionally bluff-raise
        elif random.random() < self._get_bluff_raise_frequency(opponent_profile, street):
            # Bluff raise!
            raise_amount = self.bet_sizer.get_raise_size(
                pot=pot,
                current_bet=current_bet,
                hero_bet=hero_current_bet,
                stack=stack,
                bet_type=BetType.BLUFF,
                street=street.value.lower()
            )
            return Action.RAISE, raise_amount
        
        # Default: fold
        else:
            return Action.FOLD, 0
    
    def _get_bluff_frequency(self, opponent_profile: Optional[PlayerProfile]) -> float:
        """Calculate how often to bluff based on opponent."""
        base_freq = self.BLUFF_FREQUENCY * self.aggression
        
        if opponent_profile is None:
            return base_freq
        
        # Bluff more vs tight players (high fold to cbet)
        if opponent_profile.fold_to_cbet > 0.60:
            return min(base_freq * 1.4, 0.35)
        
        # Bluff less vs calling stations (low fold to cbet)
        elif opponent_profile.fold_to_cbet < 0.30:
            return base_freq * 0.6
        
        return base_freq
    
    def _get_bluff_raise_frequency(
        self,
        opponent_profile: Optional[PlayerProfile],
        street: Street
    ) -> float:
        """Calculate how often to bluff-raise."""
        # Only bluff-raise on flop/turn, rarely on river
        if street == Street.RIVER:
            base_freq = 0.05
        elif street == Street.TURN:
            base_freq = 0.08
        else:
            base_freq = 0.12
        
        base_freq *= self.aggression
        
        if opponent_profile is None:
            return base_freq
        
        # Bluff-raise more vs tight-aggressive players
        if opponent_profile.vpip < 0.25 and opponent_profile.aggression_factor > 2.5:
            return base_freq * 1.3
        
        # Don't bluff-raise vs calling stations
        if opponent_profile.aggression_factor < 1.5:
            return base_freq * 0.4
        
        return base_freq
    
    def decide_preflop_action(
        self,
        hero_hand: List[Card],
        opponent_profile: Optional[PlayerProfile],
        pot: int,
        current_bet: int,
        hero_current_bet: int,
        hero_stack: int,
        position: str,
        bb: int,
        legal_actions: Optional[Dict] = None
    ) -> Tuple[Action, int]:
        """
        Decide preflop action using simplified ranges.
        
        Uses heads-up preflop ranges rather than equity calculation.
        """
        # Calculate preflop equity vs random hand
        try:
            # Convert Card objects to string format
            def card_to_str(card: Card) -> str:
                rank_map = {14: 'A', 13: 'K', 12: 'Q', 11: 'J', 10: 'T'}
                rank_str = rank_map.get(card.rank, str(card.rank))
                suit_str = str(card.suit)
                suit_map = {'♥': 'h', '♦': 'd', '♣': 'c', '♠': 's',
                           'h': 'h', 'd': 'd', 'c': 'c', 's': 's'}
                suit_ascii = suit_map.get(suit_str, 'h')
                return f"{rank_str}{suit_ascii}"
            
            hero_str = ''.join([card_to_str(c) for c in hero_hand])
            result = self.equity_calc.calculate_preflop_equity(hero_str)
            equity = result.equity
        except:
            # Fallback: basic hand strength
            equity = self._estimate_preflop_strength(hero_hand)
        
        call_amount = current_bet - hero_current_bet
        
        # Facing no bet (we can open raise)
        if current_bet == hero_current_bet:
            # Open raise with top 60% of hands (heads-up range)
            if equity > 0.55:
                raise_amount = self.bet_sizer.get_preflop_raise_size(
                    bb=bb,
                    position=position,
                    facing_raise=False
                )
                return Action.BET, raise_amount
            else:
                return Action.CHECK, 0
        
        # Facing a raise
        else:
            # 3-bet with strong hands (top 20%)
            if equity > 0.70:
                raise_amount = self.bet_sizer.get_preflop_raise_size(
                    bb=bb,
                    position=position,
                    facing_raise=True
                )
                return Action.RAISE, raise_amount
            
            # Call with decent hands (top 50%)
            elif equity > 0.55:
                return Action.CALL, current_bet
            
            # Fold weak hands
            else:
                return Action.FOLD, 0
    
    def _estimate_preflop_strength(self, hero_hand: List[Card]) -> float:
        """
        Estimate preflop hand strength (fallback if equity calc fails).
        
        Returns rough equity vs random hand.
        """
        if len(hero_hand) != 2:
            return 0.50
        
        c1, c2 = hero_hand
        rank1 = c1.rank
        rank2 = c2.rank
        suited = str(c1.suit) == str(c2.suit)
        
        # Pairs
        if rank1 == rank2:
            # AA-KK: 80-85%
            if rank1 >= 13:
                return 0.85
            # QQ-JJ: 70-75%
            elif rank1 >= 11:
                return 0.72
            # TT-88: 65-70%
            elif rank1 >= 8:
                return 0.67
            # 77-22: 55-65%
            else:
                return 0.55 + (rank1 / 100)
        
        # High cards
        max_rank = max(rank1, rank2)
        min_rank = min(rank1, rank2)
        
        # AK, AQ: 65-70%
        if max_rank == 14 and min_rank >= 12:
            return 0.68 if suited else 0.65
        
        # AJ, AT, KQ: 60-65%
        if (max_rank == 14 and min_rank >= 10) or (max_rank == 13 and min_rank == 12):
            return 0.63 if suited else 0.60
        
        # Suited connectors and broadway
        if suited and abs(rank1 - rank2) <= 2:
            return 0.57
        
        # Default based on high card
        return 0.50 + (max_rank / 50)

