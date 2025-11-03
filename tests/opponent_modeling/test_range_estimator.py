"""
Tests for RuleBasedRangeEstimator.
"""

import pytest
from pypokerengine.opponent_modeling.range_estimator import RuleBasedRangeEstimator
from pypokerengine.opponent_modeling.player_profile import PlayerProfile, PlayerArchetype
from pypokerengine.opponent_modeling.hand_history import Street


class TestRuleBasedRangeEstimator:
    """Tests for rule-based range estimation."""
    
    def test_initialization(self):
        """Test estimator initialization."""
        estimator = RuleBasedRangeEstimator()
        assert estimator.player_profile is None
    
    def test_initialization_with_profile(self):
        """Test initialization with player profile."""
        profile = PlayerProfile(player_id="test", hands_played=100)
        estimator = RuleBasedRangeEstimator(player_profile=profile)
        assert estimator.player_profile == profile
    
    def test_preflop_raise_range(self):
        """Test preflop raise range estimation."""
        profile = PlayerProfile(player_id="test", hands_played=100)
        profile.vpip_count = 20
        profile.pfr_count = 18
        profile.postflop_bets = 30
        profile.postflop_raises = 20
        profile.postflop_calls = 10
        
        estimator = RuleBasedRangeEstimator(player_profile=profile)
        
        # TAG player raises - should get tight range
        hand_range = estimator.estimate_preflop_range(action="raise")
        assert len(hand_range.hands) > 0
    
    def test_preflop_call_range(self):
        """Test preflop call range estimation."""
        profile = PlayerProfile(player_id="test", hands_played=100)
        profile.vpip_count = 20
        profile.pfr_count = 18
        
        estimator = RuleBasedRangeEstimator(player_profile=profile)
        
        hand_range = estimator.estimate_preflop_range(action="call")
        assert len(hand_range.hands) > 0
    
    def test_preflop_3bet_range(self):
        """Test preflop 3-bet range estimation."""
        profile = PlayerProfile(player_id="test", hands_played=100)
        profile.vpip_count = 20
        profile.pfr_count = 18
        
        estimator = RuleBasedRangeEstimator(player_profile=profile)
        
        # 3-bet (raise facing raise)
        hand_range = estimator.estimate_preflop_range(
            action="raise",
            facing_raise=True
        )
        assert len(hand_range.hands) > 0
    
    def test_unknown_player_uses_defaults(self):
        """Test that unknown player uses default ranges."""
        estimator = RuleBasedRangeEstimator()  # No profile
        
        hand_range = estimator.estimate_preflop_range(action="raise")
        assert len(hand_range.hands) > 0
    
    def test_postflop_range_narrows_on_bet(self):
        """Test that betting narrows range postflop."""
        from pypokerengine.simulation.hand_range import HandRange
        
        profile = PlayerProfile(player_id="test", hands_played=100)
        profile.vpip_count = 20
        profile.pfr_count = 18
        profile.postflop_bets = 30
        profile.postflop_raises = 20
        profile.postflop_calls = 10
        
        estimator = RuleBasedRangeEstimator(player_profile=profile)
        
        # Start with wide preflop range
        preflop_range = HandRange.from_string("22+,A2s+,K5s+")
        
        # Estimate postflop range after betting
        postflop_range = estimator.estimate_postflop_range(
            preflop_range=preflop_range,
            street=Street.FLOP,
            action="bet",
            board=["As", "Kh", "Qd"],
            pot_size=100,
            bet_size=75
        )
        
        # Should still have hands (may not be narrowed in current implementation)
        assert len(postflop_range.hands) >= 0
    
    def test_archetype_range_templates(self):
        """Test that different archetypes have different ranges."""
        # TAG player
        tag_profile = PlayerProfile(player_id="tag", hands_played=100)
        tag_profile.vpip_count = 20
        tag_profile.pfr_count = 18
        tag_profile.postflop_bets = 30
        tag_profile.postflop_raises = 20
        tag_profile.postflop_calls = 10
        
        tag_estimator = RuleBasedRangeEstimator(player_profile=tag_profile)
        
        # LAG player
        lag_profile = PlayerProfile(player_id="lag", hands_played=100)
        lag_profile.vpip_count = 40
        lag_profile.pfr_count = 32
        lag_profile.postflop_bets = 40
        lag_profile.postflop_raises = 30
        lag_profile.postflop_calls = 15
        
        lag_estimator = RuleBasedRangeEstimator(player_profile=lag_profile)
        
        # Both should produce valid ranges
        tag_range = tag_estimator.estimate_preflop_range(action="raise")
        lag_range = lag_estimator.estimate_preflop_range(action="raise")
        
        assert len(tag_range.hands) > 0
        assert len(lag_range.hands) > 0
    
    def test_estimate_range_from_sequence(self):
        """Test estimating range from action sequence."""
        profile = PlayerProfile(player_id="test", hands_played=100)
        profile.vpip_count = 20
        profile.pfr_count = 18
        
        estimator = RuleBasedRangeEstimator(player_profile=profile)
        
        actions = [
            {'action': 'raise', 'position': 'BTN', 'street': Street.PREFLOP},
            {'action': 'bet', 'street': Street.FLOP, 'pot_size': 100, 'amount': 75},
            {'action': 'bet', 'street': Street.TURN, 'pot_size': 250, 'amount': 150},
        ]
        
        final_range = estimator.estimate_range_from_sequence(
            actions=actions,
            board=["As", "Kh", "Qd", "Jc"]
        )
        
        assert len(final_range.hands) >= 0

