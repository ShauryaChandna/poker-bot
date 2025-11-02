"""
Monte Carlo Simulation Engine

Fast randomized simulation for poker equity calculations.
Optimized for heads-up pot-limit Texas Hold'em.
"""

from typing import List, Tuple, Optional, Dict
import random
from ..engine.card import Card, Deck
from ..engine.hand_evaluator import HandEvaluator


class SimulationResult:
    """
    Result of a Monte Carlo simulation.
    
    Attributes:
        wins: Number of wins
        losses: Number of losses
        ties: Number of ties
        total_simulations: Total simulations run
        equity: Win equity (0-1)
    """
    
    def __init__(self, wins: int, losses: int, ties: int):
        """
        Initialize simulation result.
        
        Args:
            wins: Number of wins
            losses: Number of losses
            ties: Number of ties
        """
        self.wins = wins
        self.losses = losses
        self.ties = ties
        self.total_simulations = wins + losses + ties
    
    @property
    def equity(self) -> float:
        """
        Calculate equity (0-1).
        
        Returns:
            Equity as a float between 0 and 1
        """
        if self.total_simulations == 0:
            return 0.0
        # Ties count as half a win
        return (self.wins + self.ties * 0.5) / self.total_simulations
    
    @property
    def win_rate(self) -> float:
        """Pure win rate (excluding ties)."""
        if self.total_simulations == 0:
            return 0.0
        return self.wins / self.total_simulations
    
    @property
    def tie_rate(self) -> float:
        """Tie rate."""
        if self.total_simulations == 0:
            return 0.0
        return self.ties / self.total_simulations
    
    def __repr__(self) -> str:
        """String representation of result."""
        return (f"SimulationResult(equity={self.equity:.4f}, "
                f"wins={self.wins}, losses={self.losses}, ties={self.ties})")


class MonteCarloSimulator:
    """
    Monte Carlo simulation engine for poker equity calculation.
    
    Runs thousands of random board runouts to estimate win probability.
    """
    
    def __init__(self, n_simulations: int = 10000, seed: Optional[int] = None):
        """
        Initialize Monte Carlo simulator.
        
        Args:
            n_simulations: Number of simulations to run per calculation
            seed: Random seed for reproducibility
        """
        self.n_simulations = n_simulations
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def simulate_hand_vs_hand(
        self,
        hero_cards: List[Card],
        villain_cards: List[Card],
        board: Optional[List[Card]] = None,
        n_simulations: Optional[int] = None
    ) -> SimulationResult:
        """
        Simulate equity between two specific hands.
        
        Args:
            hero_cards: Hero's hole cards (2 cards)
            villain_cards: Villain's hole cards (2 cards)
            board: Current board cards (0-5 cards)
            n_simulations: Override default simulation count
            
        Returns:
            SimulationResult with equity calculation
            
        Example:
            >>> sim = MonteCarloSimulator(n_simulations=10000)
            >>> hero = [Card.from_string('Ah'), Card.from_string('Kh')]
            >>> villain = [Card.from_string('Qs'), Card.from_string('Qd')]
            >>> board = [Card.from_string('Ac')]
            >>> result = sim.simulate_hand_vs_hand(hero, villain, board)
            >>> print(f"Hero equity: {result.equity:.2%}")
        """
        if len(hero_cards) != 2 or len(villain_cards) != 2:
            raise ValueError("Both players must have exactly 2 hole cards")
        
        board = board or []
        if len(board) > 5:
            raise ValueError("Board cannot have more than 5 cards")
        
        n_sims = n_simulations or self.n_simulations
        
        wins = 0
        losses = 0
        ties = 0
        
        # Create deck and remove known cards
        known_cards = set(hero_cards + villain_cards + board)
        
        for _ in range(n_sims):
            # Create a fresh deck for this simulation
            deck = Deck(seed=None)  # Don't use seed for individual simulations
            
            # Remove known cards
            deck.cards = [c for c in deck.cards if c not in known_cards]
            deck.shuffle()
            
            # Complete the board (deal remaining cards)
            remaining_cards = 5 - len(board)
            sim_board = board + [deck.deal_one() for _ in range(remaining_cards)]
            
            # Evaluate both hands
            hero_hand = hero_cards + sim_board
            villain_hand = villain_cards + sim_board
            
            result = HandEvaluator.compare_hands(hero_hand, villain_hand)
            
            if result > 0:
                wins += 1
            elif result < 0:
                losses += 1
            else:
                ties += 1
        
        return SimulationResult(wins, losses, ties)
    
    def simulate_hand_vs_range(
        self,
        hero_cards: List[Card],
        villain_combos: List[Tuple[Card, Card]],
        board: Optional[List[Card]] = None,
        n_simulations: Optional[int] = None
    ) -> SimulationResult:
        """
        Simulate equity of a hand against a range of hands.
        
        Args:
            hero_cards: Hero's hole cards (2 cards)
            villain_combos: List of possible villain hand combinations
            board: Current board cards (0-5 cards)
            n_simulations: Override default simulation count
            
        Returns:
            SimulationResult with equity calculation
            
        Example:
            >>> from .hand_range import HandRange
            >>> sim = MonteCarloSimulator(n_simulations=10000)
            >>> hero = [Card.from_string('Ah'), Card.from_string('Kh')]
            >>> villain_range = HandRange.from_string("22+,AJs+")
            >>> board = [Card.from_string('Ac')]
            >>> villain_combos = villain_range.get_combinations(exclude_cards=hero + board)
            >>> result = sim.simulate_hand_vs_range(hero, villain_combos, board)
        """
        if not villain_combos:
            raise ValueError("Villain range must have at least one combination")
        
        if len(hero_cards) != 2:
            raise ValueError("Hero must have exactly 2 hole cards")
        
        board = board or []
        n_sims = n_simulations or self.n_simulations
        
        total_wins = 0
        total_losses = 0
        total_ties = 0
        
        # For each simulation, randomly select a villain hand from the range
        for _ in range(n_sims):
            # Randomly select villain hand
            villain_cards = list(random.choice(villain_combos))
            
            # Make sure no card overlap with hero (shouldn't happen if range properly filtered)
            if any(card in hero_cards for card in villain_cards):
                continue
            
            # Run one simulation for this matchup
            result = self.simulate_hand_vs_hand(
                hero_cards, 
                villain_cards, 
                board, 
                n_simulations=1
            )
            
            total_wins += result.wins
            total_losses += result.losses
            total_ties += result.ties
        
        return SimulationResult(total_wins, total_losses, total_ties)
    
    def simulate_range_vs_range(
        self,
        hero_combos: List[Tuple[Card, Card]],
        villain_combos: List[Tuple[Card, Card]],
        board: Optional[List[Card]] = None,
        n_simulations: Optional[int] = None
    ) -> SimulationResult:
        """
        Simulate equity between two ranges.
        
        Args:
            hero_combos: List of hero's possible hand combinations
            villain_combos: List of villain's possible hand combinations
            board: Current board cards (0-5 cards)
            n_simulations: Override default simulation count
            
        Returns:
            SimulationResult with equity calculation
        """
        if not hero_combos or not villain_combos:
            raise ValueError("Both ranges must have at least one combination")
        
        board = board or []
        n_sims = n_simulations or self.n_simulations
        
        total_wins = 0
        total_losses = 0
        total_ties = 0
        
        for _ in range(n_sims):
            # Randomly select hands from both ranges
            hero_cards = list(random.choice(hero_combos))
            villain_cards = list(random.choice(villain_combos))
            
            # Ensure no card overlap
            if any(card in villain_cards for card in hero_cards):
                continue
            if board and any(card in hero_cards + villain_cards for card in board):
                continue
            
            # Run one simulation
            result = self.simulate_hand_vs_hand(
                hero_cards,
                villain_cards,
                board,
                n_simulations=1
            )
            
            total_wins += result.wins
            total_losses += result.losses
            total_ties += result.ties
        
        return SimulationResult(total_wins, total_losses, total_ties)
    
    def calculate_preflop_equity(
        self,
        hero_cards: List[Card],
        villain_cards: Optional[List[Card]] = None,
        n_simulations: Optional[int] = None
    ) -> SimulationResult:
        """
        Calculate preflop equity (no board cards).
        
        Args:
            hero_cards: Hero's hole cards
            villain_cards: Villain's hole cards (None for random)
            n_simulations: Override default simulation count
            
        Returns:
            SimulationResult with preflop equity
        """
        if villain_cards:
            return self.simulate_hand_vs_hand(hero_cards, villain_cards, [], n_simulations)
        else:
            # Simulate against a random hand
            # Create all possible villain hands excluding hero cards
            deck = Deck()
            deck.cards = [c for c in deck.cards if c not in hero_cards]
            
            wins = 0
            losses = 0
            ties = 0
            n_sims = n_simulations or self.n_simulations
            
            for _ in range(n_sims):
                deck.shuffle()
                villain_cards = [deck.cards[0], deck.cards[1]]
                
                result = self.simulate_hand_vs_hand(
                    hero_cards,
                    villain_cards,
                    [],
                    n_simulations=1
                )
                
                wins += result.wins
                losses += result.losses
                ties += result.ties
            
            return SimulationResult(wins, losses, ties)


def quick_equity_check(hero_hand: str, villain_hand: str, board_str: str = "") -> float:
    """
    Quick utility function for equity calculation.
    
    Args:
        hero_hand: Hero hand like "AhKh"
        villain_hand: Villain hand like "QsQd"
        board_str: Board like "AcTd2s" (optional)
        
    Returns:
        Hero's equity as a float (0-1)
        
    Example:
        >>> equity = quick_equity_check("AhKh", "QsQd", "Ac")
        >>> print(f"Equity: {equity:.2%}")
    """
    # Parse hero hand
    hero_cards = [
        Card.from_string(hero_hand[0:2]),
        Card.from_string(hero_hand[2:4])
    ]
    
    # Parse villain hand
    villain_cards = [
        Card.from_string(villain_hand[0:2]),
        Card.from_string(villain_hand[2:4])
    ]
    
    # Parse board
    board = []
    if board_str:
        for i in range(0, len(board_str), 2):
            board.append(Card.from_string(board_str[i:i+2]))
    
    # Run simulation
    sim = MonteCarloSimulator(n_simulations=10000)
    result = sim.simulate_hand_vs_hand(hero_cards, villain_cards, board)
    
    return result.equity

