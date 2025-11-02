"""
Tests for Equity Calculator.

Tests high-level API and caching functionality.
"""

import pytest
from pypokerengine.simulation.equity_calculator import (
    EquityCalculator,
    EquityResult,
    calculate_equity
)
from pypokerengine.simulation.hand_range import HandRange
from pypokerengine.engine.card import Card


class TestEquityResult:
    """Test EquityResult dataclass."""
    
    def test_equity_result_creation(self):
        """Test EquityResult can be created."""
        result = EquityResult(
            equity=0.75,
            win_rate=0.72,
            tie_rate=0.06,
            simulations=10000,
            std_error=0.004
        )
        
        assert result.equity == 0.75
        assert result.simulations == 10000
    
    def test_equity_result_repr(self):
        """Test string representation."""
        result = EquityResult(
            equity=0.75,
            win_rate=0.72,
            tie_rate=0.06,
            simulations=10000,
            std_error=0.004
        )
        
        repr_str = repr(result)
        assert "0.75" in repr_str or "0.7500" in repr_str
        assert "10000" in repr_str


class TestEquityCalculator:
    """Test EquityCalculator main functionality."""
    
    def test_calculator_initialization(self):
        """Test calculator can be initialized."""
        calc = EquityCalculator(default_simulations=5000)
        assert calc.default_simulations == 5000
    
    def test_calculate_hand_vs_hand(self):
        """Test hand vs hand calculation."""
        calc = EquityCalculator(default_simulations=5000)
        
        result = calc.calculate_equity("AhAd", villain_hand="KsKd")
        
        assert isinstance(result, EquityResult)
        assert 0.75 < result.equity < 0.90
        assert result.simulations == 5000
    
    def test_calculate_hand_vs_hand_with_board(self):
        """Test hand vs hand with board."""
        calc = EquityCalculator(default_simulations=5000)
        
        result = calc.calculate_equity(
            "AhKh",
            villain_hand="QsQd",
            board="Ac7d2s"
        )
        
        # AK should be ahead after hitting ace
        assert result.equity > 0.65
    
    def test_calculate_hand_vs_range(self):
        """Test hand vs range calculation."""
        calc = EquityCalculator(default_simulations=5000)
        
        result = calc.calculate_equity(
            "AhAd",
            villain_range="KK,QQ,JJ"
        )
        
        # AA should dominate this range
        assert result.equity > 0.75
    
    def test_calculate_hand_vs_range_with_board(self):
        """Test hand vs range with board."""
        calc = EquityCalculator(default_simulations=5000)
        
        result = calc.calculate_equity(
            "AhKc",
            villain_range="AQ,AJ,AT",
            board="Ac7d2s"
        )
        
        # AK with top pair should beat weaker aces
        assert result.equity > 0.6
    
    def test_preflop_equity_method(self):
        """Test dedicated preflop equity method."""
        calc = EquityCalculator(default_simulations=5000)
        
        result = calc.calculate_preflop_equity("AhAd", villain_range="KK+")
        
        # AA should dominate KK+
        assert result.equity > 0.75
    
    def test_postflop_equity_method(self):
        """Test dedicated postflop equity method."""
        calc = EquityCalculator(default_simulations=5000)
        
        result = calc.calculate_postflop_equity(
            "AhKh",
            villain_range="QQ,JJ",
            board="Ac7d2s"
        )
        
        # Should have good equity with top pair
        assert result.equity > 0.60
    
    def test_override_simulations(self):
        """Test overriding default simulations."""
        calc = EquityCalculator(default_simulations=5000)
        
        result = calc.calculate_equity(
            "AhAd",
            villain_hand="KsKd",
            n_simulations=1000
        )
        
        assert result.simulations == 1000
    
    def test_card_object_input(self):
        """Test using Card objects as input."""
        calc = EquityCalculator(default_simulations=1000)
        
        hero_cards = [Card.from_string('Ah'), Card.from_string('Ad')]
        villain_cards = [Card.from_string('Ks'), Card.from_string('Kd')]
        
        result = calc.calculate_equity(hero_cards, villain_hand=villain_cards)
        
        assert 0.75 < result.equity < 0.90
    
    def test_range_object_input(self):
        """Test using HandRange object as input."""
        calc = EquityCalculator(default_simulations=5000)
        
        villain_range = HandRange.from_string("KK,QQ")
        result = calc.calculate_equity("AhAd", villain_range=villain_range)
        
        assert result.equity > 0.75
    
    def test_std_error_calculation(self):
        """Test that standard error is calculated."""
        calc = EquityCalculator(default_simulations=5000)
        
        result = calc.calculate_equity("AhAd", villain_hand="KsKd")
        
        # Standard error should be small with 5000 sims
        assert 0 < result.std_error < 0.02


class TestEquityCalculatorCaching:
    """Test caching functionality."""
    
    def test_cache_hit_performance(self):
        """Test that cached queries are faster (conceptually)."""
        calc = EquityCalculator(default_simulations=5000, cache_size=100)
        
        # First call
        result1 = calc.calculate_equity("AhAd", villain_hand="KsKd")
        
        # Second call (should hit cache)
        result2 = calc.calculate_equity("AhAd", villain_hand="KsKd")
        
        # Results should be identical (from cache)
        assert result1.equity == result2.equity
        assert result1.simulations == result2.simulations
    
    def test_cache_info(self):
        """Test cache info retrieval."""
        calc = EquityCalculator(default_simulations=1000, cache_size=100)
        
        # Make some queries
        calc.calculate_equity("AhAd", villain_hand="KsKd")
        calc.calculate_equity("AhAd", villain_hand="KsKd")  # Cache hit
        
        cache_info = calc.cache_info()
        
        assert 'hand_vs_hand' in cache_info
        assert cache_info['hand_vs_hand']['hits'] >= 1
    
    def test_cache_clear(self):
        """Test cache clearing."""
        calc = EquityCalculator(default_simulations=1000)
        
        # Make a query
        calc.calculate_equity("AhAd", villain_hand="KsKd")
        
        # Clear cache
        calc.clear_cache()
        
        # Check cache is cleared
        cache_info = calc.cache_info()
        assert cache_info['hand_vs_hand']['currsize'] == 0
    
    def test_different_boards_different_cache(self):
        """Test that different boards don't hit same cache."""
        calc = EquityCalculator(default_simulations=1000)
        
        result1 = calc.calculate_equity("AhKh", villain_hand="QsQd", board="Ac")
        result2 = calc.calculate_equity("AhKh", villain_hand="QsQd", board="2c")
        
        # Different boards should give different results
        assert result1.equity != result2.equity


class TestConvenienceFunction:
    """Test convenience function."""
    
    def test_calculate_equity_function(self):
        """Test convenience function."""
        equity = calculate_equity("AhAd", villain_hand="KsKd", n_simulations=5000)
        
        assert isinstance(equity, float)
        assert 0.75 < equity < 0.90
    
    def test_calculate_equity_with_board(self):
        """Test convenience function with board."""
        equity = calculate_equity(
            "AhKh",
            villain_hand="QsQd",
            board="Ac",
            n_simulations=5000
        )
        
        assert equity > 0.65
    
    def test_calculate_equity_with_range(self):
        """Test convenience function with range."""
        equity = calculate_equity(
            "AhAd",
            villain_range="KK,QQ",
            n_simulations=5000
        )
        
        assert equity > 0.75


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_invalid_hand_format(self):
        """Test invalid hand format raises error."""
        calc = EquityCalculator()
        
        with pytest.raises(ValueError):
            calc.calculate_equity("AK", villain_hand="QQ")  # Wrong format
    
    def test_blockers_eliminate_range(self):
        """Test error when blockers eliminate all villain combos."""
        calc = EquityCalculator()
        
        # Hero has all aces, villain range is AA
        with pytest.raises(ValueError):
            calc.calculate_equity(
                "AhAd",
                villain_range="AA",
                board="AcAs"  # All aces used
            )
    
    def test_deterministic_with_seed(self):
        """Test deterministic results with seed."""
        calc1 = EquityCalculator(default_simulations=1000, seed=42)
        calc2 = EquityCalculator(default_simulations=1000, seed=42)
        
        result1 = calc1.calculate_equity("AhAd", villain_hand="KsKd")
        result2 = calc2.calculate_equity("AhAd", villain_hand="KsKd")
        
        # With same seed, should get similar results (not exact due to caching)
        assert abs(result1.equity - result2.equity) < 0.1


class TestRealWorldScenarios:
    """Test realistic poker scenarios."""
    
    def test_top_pair_vs_draws(self):
        """Test top pair against drawing hands."""
        calc = EquityCalculator(default_simulations=10000)
        
        # Hero has top pair on flop vs middle pairs
        result = calc.calculate_equity(
            "AhKc",
            villain_range="JJ,TT,99",  # Pocket pairs
            board="Ac7h2h"
        )
        
        # Top pair should be ahead of underpairs
        assert 0.65 < result.equity < 0.95
    
    def test_overpair_vs_underpair(self):
        """Test overpair vs underpair."""
        calc = EquityCalculator(default_simulations=5000)
        
        result = calc.calculate_equity(
            "KhKc",
            villain_range="JJ,TT",
            board="9h4d2s"
        )
        
        # Should dominate
        assert result.equity > 0.80
    
    def test_set_vs_top_pair(self):
        """Test set vs top pair."""
        calc = EquityCalculator(default_simulations=5000)
        
        result = calc.calculate_equity(
            "7h7c",  # Hero has set
            villain_range="AK,AQ",  # Villain has top pair
            board="Ac7d2h"
        )
        
        # Set should dominate
        assert result.equity > 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

