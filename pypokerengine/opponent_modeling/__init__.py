"""
Opponent Modeling Module

Track opponent behavior, estimate hand ranges, and predict tendencies
using both rule-based heuristics and machine learning.

This module bridges Phase 2 (equity calculations) with Phase 4 (AI training)
by providing context about what opponents likely hold based on their actions.
"""

from .player_profile import PlayerProfile, PlayerArchetype
from .hand_history import HandHistory, ActionRecord, Street
from .range_estimator import RuleBasedRangeEstimator
from .features import FeatureExtractor, extract_features
from .range_predictor import RangePredictor, HybridRangeEstimator

__all__ = [
    'PlayerProfile',
    'PlayerArchetype',
    'HandHistory',
    'ActionRecord',
    'Street',
    'RuleBasedRangeEstimator',
    'FeatureExtractor',
    'extract_features',
    'RangePredictor',
    'HybridRangeEstimator',
]

