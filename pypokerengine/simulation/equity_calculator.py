"""
Equity Calculator with Lazy Caching

High-level API for poker equity calculations with LRU caching
for performance optimization during training and gameplay.
"""

from typing import List, Optional, Tuple, Union
from functools import lru_cache
import hashlib
from dataclasses import dataclass

from ..engine.card import Card
from .hand_range import HandRange, parse_hand_to_cards
from .monte_carlo import MonteCarloSimulator, SimulationResult


@dataclass
class EquityResult:
    """
    Comprehensive equity calculation result.
    
    Attributes:
        equity: Win equity (0-1)
        win_rate: Pure win rate excluding ties
        tie_rate: Rate of ties
        simulations: Number of simulations run
        std_error: Standard error estimate
    """
    equity: float
    win_rate: float
    tie_rate: float
    simulations: int
    std_error: float
    
    def __repr__(self) -> str:
        """String representation."""
        return (f"EquityResult(equity={self.equity:.4f} ±{self.std_error:.4f}, "
                f"sims={self.simulations})")


class EquityCalculator:
    """
    High-level equity calculator with caching.
    
    Provides convenient API for all equity calculation scenarios:
    - Hand vs hand
    - Hand vs range
    - Range vs range
    - Preflop equity
    
    Uses LRU caching to avoid redundant calculations.
    """
    
    def __init__(
        self,
        default_simulations: int = 10000,
        cache_size: int = 2000,
        seed: Optional[int] = None
    ):
        """
        Initialize equity calculator.
        
        Args:
            default_simulations: Default number of Monte Carlo simulations
            cache_size: Maximum number of cached results
            seed: Random seed for reproducibility
        """
        self.default_simulations = default_simulations
        self.cache_size = cache_size
        self.seed = seed
        self.simulator = MonteCarloSimulator(n_simulations=default_simulations, seed=seed)
        
        # Initialize cached calculation methods
        self._cached_hand_vs_hand = lru_cache(maxsize=cache_size)(self._compute_hand_vs_hand)
        self._range_cache = {}  # Manual cache for range calculations
    
    def calculate_equity(
        self,
        hero_hand: Union[str, List[Card]],
        villain_hand: Optional[Union[str, List[Card], HandRange]] = None,
        villain_range: Optional[Union[str, HandRange]] = None,
        board: Optional[Union[str, List[Card]]] = None,
        n_simulations: Optional[int] = None
    ) -> EquityResult:
        """
        Universal equity calculation method.
        
        Args:
            hero_hand: Hero's hand as "AhKh" or [Card, Card]
            villain_hand: Specific villain hand (optional)
            villain_range: Villain range string or HandRange (optional)
            board: Board as "AcTd2s" or [Card, Card, ...]
            n_simulations: Override default simulation count
            
        Returns:
            EquityResult with comprehensive equity information
            
        Examples:
            # Hand vs hand with board
            >>> calc = EquityCalculator()
            >>> result = calc.calculate_equity("AhKh", villain_hand="QsQd", board="Ac")
            
            # Hand vs range
            >>> result = calc.calculate_equity("AhKh", villain_range="JJ+,AQs+")
            
            # Preflop hand vs random
            >>> result = calc.calculate_equity("AhKh")
        """
        # Parse inputs
        hero_cards = self._parse_hand(hero_hand)
        board_cards = self._parse_board(board) if board else []
        n_sims = n_simulations or self.default_simulations
        
        # Case 1: Hand vs specific hand
        if villain_hand is not None:
            villain_cards = self._parse_hand(villain_hand)
            return self._calculate_hand_vs_hand(
                hero_cards, villain_cards, board_cards, n_sims
            )
        
        # Case 2: Hand vs range
        elif villain_range is not None:
            if isinstance(villain_range, str):
                villain_range = HandRange.from_string(villain_range)
            return self._calculate_hand_vs_range(
                hero_cards, villain_range, board_cards, n_sims
            )
        
        # Case 3: Hand vs random (preflop)
        else:
            return self._calculate_hand_vs_random(hero_cards, board_cards, n_sims)
    
    def calculate_preflop_equity(
        self,
        hero_hand: Union[str, List[Card]],
        villain_range: Optional[Union[str, HandRange]] = None,
        n_simulations: Optional[int] = None
    ) -> EquityResult:
        """
        Calculate preflop equity (no board).
        
        Args:
            hero_hand: Hero's hand
            villain_range: Villain's range (None for random hand)
            n_simulations: Override default simulation count
            
        Returns:
            EquityResult for preflop scenario
        """
        return self.calculate_equity(
            hero_hand,
            villain_range=villain_range,
            board=None,
            n_simulations=n_simulations
        )
    
    def calculate_postflop_equity(
        self,
        hero_hand: Union[str, List[Card]],
        villain_range: Union[str, HandRange],
        board: Union[str, List[Card]],
        n_simulations: Optional[int] = None
    ) -> EquityResult:
        """
        Calculate postflop equity with board.
        
        Args:
            hero_hand: Hero's hand
            villain_range: Villain's range
            board: Board cards
            n_simulations: Override default simulation count
            
        Returns:
            EquityResult for postflop scenario
        """
        return self.calculate_equity(
            hero_hand,
            villain_range=villain_range,
            board=board,
            n_simulations=n_simulations
        )
    
    def _calculate_hand_vs_hand(
        self,
        hero_cards: List[Card],
        villain_cards: List[Card],
        board_cards: List[Card],
        n_simulations: int
    ) -> EquityResult:
        """Internal method for hand vs hand calculation with caching."""
        # Create cache key
        cache_key = self._make_hand_vs_hand_key(
            hero_cards, villain_cards, board_cards, n_simulations
        )
        
        # Use cached method
        sim_result = self._cached_hand_vs_hand(cache_key)
        
        return self._result_to_equity_result(sim_result)
    
    def _calculate_hand_vs_range(
        self,
        hero_cards: List[Card],
        villain_range: HandRange,
        board_cards: List[Card],
        n_simulations: int
    ) -> EquityResult:
        """Internal method for hand vs range calculation with caching."""
        # Get villain combinations (accounting for blockers)
        exclude_cards = hero_cards + board_cards
        villain_combos = villain_range.get_combinations(exclude_cards=exclude_cards)
        
        if not villain_combos:
            raise ValueError("Villain range has no valid combinations after removing blockers")
        
        # Create cache key
        cache_key = self._make_hand_vs_range_key(
            hero_cards, villain_combos, board_cards, n_simulations
        )
        
        # Check cache first
        if hasattr(self, '_range_cache') and cache_key in self._range_cache:
            sim_result = self._range_cache[cache_key]
        else:
            # Compute and cache
            sim_result = self.simulator.simulate_hand_vs_range(
                hero_cards, villain_combos, board_cards, n_simulations
            )
            if not hasattr(self, '_range_cache'):
                self._range_cache = {}
            # Simple LRU: if cache too big, clear oldest
            if len(self._range_cache) >= self.cache_size:
                # Remove oldest item (first item)
                self._range_cache.pop(next(iter(self._range_cache)))
            self._range_cache[cache_key] = sim_result
        
        return self._result_to_equity_result(sim_result)
    
    def _calculate_hand_vs_random(
        self,
        hero_cards: List[Card],
        board_cards: List[Card],
        n_simulations: int
    ) -> EquityResult:
        """Calculate equity against a random hand."""
        sim_result = self.simulator.calculate_preflop_equity(
            hero_cards, villain_cards=None, n_simulations=n_simulations
        )
        return self._result_to_equity_result(sim_result)
    
    def _compute_hand_vs_hand(self, cache_key: str) -> SimulationResult:
        """Compute hand vs hand equity (called by cached method)."""
        # Unpack cache key
        hero_cards, villain_cards, board_cards, n_sims = self._unpack_hand_vs_hand_key(cache_key)
        
        # Run simulation
        return self.simulator.simulate_hand_vs_hand(
            hero_cards, villain_cards, board_cards, n_sims
        )
    
    
    def _make_hand_vs_hand_key(
        self,
        hero_cards: List[Card],
        villain_cards: List[Card],
        board_cards: List[Card],
        n_simulations: int
    ) -> str:
        """Create cache key for hand vs hand."""
        hero_str = self._cards_to_string(hero_cards)
        villain_str = self._cards_to_string(villain_cards)
        board_str = self._cards_to_string(board_cards)
        
        key = f"hvh:{hero_str}:{villain_str}:{board_str}:{n_simulations}"
        return key
    
    def _make_hand_vs_range_key(
        self,
        hero_cards: List[Card],
        villain_combos: List[Tuple[Card, Card]],
        board_cards: List[Card],
        n_simulations: int
    ) -> str:
        """Create cache key for hand vs range."""
        hero_str = self._cards_to_string(hero_cards)
        board_str = self._cards_to_string(board_cards)
        
        # Create deterministic hash of villain combos
        combo_strs = sorted([self._cards_to_string(list(combo)) for combo in villain_combos])
        combo_hash = hashlib.md5(','.join(combo_strs).encode()).hexdigest()[:8]
        
        key = f"hvr:{hero_str}:{combo_hash}:{board_str}:{n_simulations}"
        return key
    
    def _unpack_hand_vs_hand_key(self, key: str) -> Tuple[List[Card], List[Card], List[Card], int]:
        """Unpack cache key for hand vs hand."""
        parts = key.split(':')
        hero_cards = self._string_to_cards(parts[1])
        villain_cards = self._string_to_cards(parts[2])
        board_cards = self._string_to_cards(parts[3])
        n_sims = int(parts[4])
        return hero_cards, villain_cards, board_cards, n_sims
    
    
    def _cards_to_string(self, cards: List[Card]) -> str:
        """Convert cards to sortable string."""
        return ','.join(sorted([str(card) for card in cards]))
    
    def _string_to_cards(self, s: str) -> List[Card]:
        """Convert string back to cards."""
        if not s:
            return []
        card_strs = s.split(',')
        return [Card.from_string(cs.replace('♣', 'c').replace('♦', 'd')
                                    .replace('♥', 'h').replace('♠', 's')) 
                for cs in card_strs]
    
    def _parse_hand(self, hand: Union[str, List[Card]]) -> List[Card]:
        """Parse hand input to list of cards."""
        if isinstance(hand, list):
            return hand
        
        if len(hand) == 4:  # "AhKh"
            return list(parse_hand_to_cards(hand))
        
        raise ValueError(f"Invalid hand format: {hand}")
    
    def _parse_board(self, board: Union[str, List[Card]]) -> List[Card]:
        """Parse board input to list of cards."""
        if isinstance(board, list):
            return board
        
        # Parse string like "AcTd2s"
        cards = []
        for i in range(0, len(board), 2):
            if i + 1 < len(board):
                cards.append(Card.from_string(board[i:i+2]))
        return cards
    
    def _result_to_equity_result(self, sim_result: SimulationResult) -> EquityResult:
        """Convert SimulationResult to EquityResult with error estimates."""
        # Calculate standard error (simplified)
        # For binomial distribution: std_error ≈ sqrt(p*(1-p)/n)
        equity = sim_result.equity
        n = sim_result.total_simulations
        std_error = (equity * (1 - equity) / n) ** 0.5 if n > 0 else 0.0
        
        return EquityResult(
            equity=equity,
            win_rate=sim_result.win_rate,
            tie_rate=sim_result.tie_rate,
            simulations=n,
            std_error=std_error
        )
    
    def clear_cache(self):
        """Clear all cached equity calculations."""
        self._cached_hand_vs_hand.cache_clear()
        if hasattr(self, '_range_cache'):
            self._range_cache.clear()
    
    def cache_info(self) -> dict:
        """Get cache statistics."""
        hvh_info = self._cached_hand_vs_hand.cache_info()._asdict()
        range_size = len(self._range_cache) if hasattr(self, '_range_cache') else 0
        return {
            'hand_vs_hand': hvh_info,
            'hand_vs_range': {'currsize': range_size, 'maxsize': self.cache_size},
        }


# Convenience function for quick calculations
def calculate_equity(
    hero_hand: str,
    villain_hand: Optional[str] = None,
    villain_range: Optional[str] = None,
    board: Optional[str] = None,
    n_simulations: int = 10000
) -> float:
    """
    Quick equity calculation convenience function.
    
    Args:
        hero_hand: Hero hand like "AhKh"
        villain_hand: Villain hand like "QsQd"
        villain_range: Villain range like "JJ+,AQs+"
        board: Board like "AcTd2s"
        n_simulations: Number of simulations
        
    Returns:
        Equity as float (0-1)
        
    Example:
        >>> equity = calculate_equity("AhKh", villain_hand="QsQd", board="Ac")
        >>> print(f"{equity:.2%}")
    """
    calc = EquityCalculator(default_simulations=n_simulations)
    result = calc.calculate_equity(hero_hand, villain_hand, villain_range, board)
    return result.equity

