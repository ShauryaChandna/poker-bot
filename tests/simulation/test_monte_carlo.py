"""
Tests for Monte Carlo Simulator.

Tests simulation accuracy and performance against known equity scenarios.
"""

import pytest
from pypokerengine.simulation.monte_carlo import (
    MonteCarloSimulator,
    SimulationResult,
    quick_equity_check
)
from pypokerengine.simulation.hand_range import HandRange
from pypokerengine.engine.card import Card


class TestSimulationResult:
    """Test SimulationResult class."""
    
    def test_equity_calculation(self):
        """Test equity calculation from wins/losses/ties."""
        result = SimulationResult(wins=800, losses=200, ties=0)
        assert result.equity == 0.8
    
    def test_equity_with_ties(self):
        """Test equity calculation with ties."""
        result = SimulationResult(wins=400, losses=400, ties=200)
        # 400 + (200 * 0.5) = 500 / 1000 = 0.5
        assert result.equity == 0.5
    
    def test_win_rate(self):
        """Test win rate calculation."""
        result = SimulationResult(wins=600, losses=300, ties=100)
        assert result.win_rate == 0.6
    
    def test_tie_rate(self):
        """Test tie rate calculation."""
        result = SimulationResult(wins=450, losses=450, ties=100)
        assert result.tie_rate == 0.1


class TestMonteCarloSimulator:
    """Test Monte Carlo simulator."""
    
    def test_simulator_initialization(self):
        """Test simulator can be initialized."""
        sim = MonteCarloSimulator(n_simulations=1000)
        assert sim.n_simulations == 1000
    
    def test_simulator_with_seed(self):
        """Test simulator with seed produces deterministic results."""
        sim1 = MonteCarloSimulator(n_simulations=1000, seed=42)
        sim2 = MonteCarloSimulator(n_simulations=1000, seed=42)
        
        hero = [Card.from_string('Ah'), Card.from_string('Kh')]
        villain = [Card.from_string('Qs'), Card.from_string('Qd')]
        
        result1 = sim1.simulate_hand_vs_hand(hero, villain)
        result2 = sim2.simulate_hand_vs_hand(hero, villain)
        
        # With same seed, results should be similar (not exact due to shuffling)
        assert abs(result1.equity - result2.equity) < 0.1


class TestHandVsHandSimulation:
    """Test hand vs hand equity calculations."""
    
    def test_aa_vs_kk_preflop(self):
        """Test AA vs KK preflop equity (known ~82/18)."""
        sim = MonteCarloSimulator(n_simulations=10000)
        
        hero = [Card.from_string('Ah'), Card.from_string('Ad')]
        villain = [Card.from_string('Ks'), Card.from_string('Kd')]
        
        result = sim.simulate_hand_vs_hand(hero, villain, board=[])
        
        # AA should have ~80-85% equity against KK
        assert 0.75 < result.equity < 0.90
    
    def test_ak_vs_22_preflop(self):
        """Test AK vs 22 preflop (known coin flip ~50/50)."""
        sim = MonteCarloSimulator(n_simulations=10000)
        
        hero = [Card.from_string('Ah'), Card.from_string('Kh')]
        villain = [Card.from_string('2s'), Card.from_string('2d')]
        
        result = sim.simulate_hand_vs_hand(hero, villain, board=[])
        
        # Should be close to 50/50
        assert 0.43 < result.equity < 0.57
    
    def test_made_hand_vs_draw(self):
        """Test made hand vs flush draw on flop."""
        sim = MonteCarloSimulator(n_simulations=10000)
        
        # Hero has top pair
        hero = [Card.from_string('Ah'), Card.from_string('Kc')]
        # Villain has flush draw
        villain = [Card.from_string('Qh'), Card.from_string('Jh')]
        # Board with two hearts
        board = [Card.from_string('Ac'), Card.from_string('7h'), Card.from_string('2h')]
        
        result = sim.simulate_hand_vs_hand(hero, villain, board)
        
        # Top pair should be ahead of flush draw (~65-70%)
        assert 0.55 < result.equity < 0.75
    
    def test_made_flush_vs_nothing(self):
        """Test completed flush vs weak hand."""
        sim = MonteCarloSimulator(n_simulations=1000)
        
        # Hero has flush
        hero = [Card.from_string('Ah'), Card.from_string('Kh')]
        # Villain has weak pair
        villain = [Card.from_string('2s'), Card.from_string('2d')]
        # Board with flush completed
        board = [
            Card.from_string('Qh'),
            Card.from_string('7h'),
            Card.from_string('3h'),
            Card.from_string('9c')
        ]
        
        result = sim.simulate_hand_vs_hand(hero, villain, board)
        
        # Flush should have very high equity
        assert result.equity > 0.85
    
    def test_identical_hands_tie(self):
        """Test identical hands always tie."""
        sim = MonteCarloSimulator(n_simulations=1000)
        
        hero = [Card.from_string('Ah'), Card.from_string('Kh')]
        villain = [Card.from_string('As'), Card.from_string('Ks')]
        board = [
            Card.from_string('Qc'),
            Card.from_string('Jc'),
            Card.from_string('Tc')
        ]
        
        result = sim.simulate_hand_vs_hand(hero, villain, board)
        
        # Should be exactly 50% due to ties
        assert 0.48 < result.equity < 0.52
        assert result.tie_rate > 0.9  # Most should be ties
    
    def test_override_simulations(self):
        """Test overriding simulation count."""
        sim = MonteCarloSimulator(n_simulations=1000)
        
        hero = [Card.from_string('Ah'), Card.from_string('Kh')]
        villain = [Card.from_string('Qs'), Card.from_string('Qd')]
        
        result = sim.simulate_hand_vs_hand(hero, villain, n_simulations=500)
        
        assert result.total_simulations == 500
    
    def test_invalid_hero_cards(self):
        """Test error on invalid hero cards."""
        sim = MonteCarloSimulator()
        
        with pytest.raises(ValueError):
            sim.simulate_hand_vs_hand(
                [Card.from_string('Ah')],  # Only 1 card
                [Card.from_string('Ks'), Card.from_string('Kd')]
            )
    
    def test_invalid_board(self):
        """Test error on invalid board."""
        sim = MonteCarloSimulator()
        
        hero = [Card.from_string('Ah'), Card.from_string('Kh')]
        villain = [Card.from_string('Qs'), Card.from_string('Qd')]
        
        with pytest.raises(ValueError):
            sim.simulate_hand_vs_hand(
                hero,
                villain,
                board=[Card.from_string('As')] * 6  # Too many cards
            )


class TestHandVsRangeSimulation:
    """Test hand vs range equity calculations."""
    
    def test_aa_vs_range(self):
        """Test AA vs a range of hands."""
        sim = MonteCarloSimulator(n_simulations=5000)
        
        hero = [Card.from_string('Ah'), Card.from_string('Ad')]
        range_obj = HandRange.from_string("KK,QQ,JJ")
        villain_combos = range_obj.get_combinations(exclude_cards=hero)
        
        result = sim.simulate_hand_vs_range(hero, villain_combos)
        
        # AA should dominate this range
        assert result.equity > 0.75
    
    def test_range_with_board(self):
        """Test hand vs range with board cards."""
        sim = MonteCarloSimulator(n_simulations=5000)
        
        hero = [Card.from_string('Ah'), Card.from_string('Kc')]
        board = [Card.from_string('Ac'), Card.from_string('7d'), Card.from_string('2s')]
        
        range_obj = HandRange.from_string("AQ,AJ,AT")
        villain_combos = range_obj.get_combinations(exclude_cards=hero + board)
        
        result = sim.simulate_hand_vs_range(hero, villain_combos, board)
        
        # AK should be ahead of these weaker aces
        assert result.equity > 0.6
    
    def test_empty_range_error(self):
        """Test error on empty range."""
        sim = MonteCarloSimulator()
        
        hero = [Card.from_string('Ah'), Card.from_string('Ad')]
        
        with pytest.raises(ValueError):
            sim.simulate_hand_vs_range(hero, [])


class TestPreflopEquity:
    """Test preflop equity calculations."""
    
    def test_aa_vs_random(self):
        """Test AA vs random hand."""
        sim = MonteCarloSimulator(n_simulations=5000)
        
        hero = [Card.from_string('Ah'), Card.from_string('Ad')]
        
        result = sim.calculate_preflop_equity(hero)
        
        # AA should have ~85% equity vs random
        assert 0.80 < result.equity < 0.90
    
    def test_72o_vs_random(self):
        """Test worst hand (72o) vs random."""
        sim = MonteCarloSimulator(n_simulations=5000)
        
        hero = [Card.from_string('7h'), Card.from_string('2c')]
        
        result = sim.calculate_preflop_equity(hero)
        
        # 72o should have ~35-40% equity vs random
        assert 0.30 < result.equity < 0.45


class TestQuickEquityCheck:
    """Test quick equity check utility function."""
    
    def test_quick_check_basic(self):
        """Test quick equity check."""
        equity = quick_equity_check("AhAd", "KsKd")
        
        # AA should dominate KK
        assert 0.75 < equity < 0.90
    
    def test_quick_check_with_board(self):
        """Test quick equity check with board."""
        equity = quick_equity_check("AhKh", "QsQd", "Ac")
        
        # After hitting ace, AK should be ahead
        assert equity > 0.65


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

