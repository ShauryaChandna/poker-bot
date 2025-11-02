"""
Simulation Layer for Poker Equity Calculations

This module provides Monte Carlo simulation and equity calculation
for heads-up pot-limit Texas Hold'em.

Key Components:
- HandRange: Parse and manipulate poker hand ranges
- MonteCarloSimulator: Fast randomized simulation engine
- EquityCalculator: High-level API with caching for equity calculations
"""

from .hand_range import HandRange
from .monte_carlo import MonteCarloSimulator
from .equity_calculator import EquityCalculator

__all__ = [
    'HandRange',
    'MonteCarloSimulator',
    'EquityCalculator'
]

