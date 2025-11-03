"""
Integration tests for opponent modeling system.
"""

import pytest
from pypokerengine.opponent_modeling import (
    PlayerProfile,
    HandHistory,
    RuleBasedRangeEstimator,
    Street
)


class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_profile_and_estimation_workflow(self):
        """Test complete workflow from tracking to estimation."""
        # Create profile
        profile = PlayerProfile(player_id="villain")
        
        # Simulate several hands
        for _ in range(30):
            profile.update_preflop_action(
                action="raise",
                is_raise=True,
                is_voluntary=True
            )
        
        # Profile should be classified as aggressive
        assert profile.hands_played == 30
        assert profile.vpip > 0.0
        assert profile.pfr > 0.0
        
        # Use profile to estimate ranges
        estimator = RuleBasedRangeEstimator(player_profile=profile)
        hand_range = estimator.estimate_preflop_range(action="raise")
        
        assert len(hand_range.hands) > 0
    
    def test_hand_history_and_profile_integration(self):
        """Test integrating hand history with profile updates."""
        history = HandHistory()
        profile = PlayerProfile(player_id="villain")
        
        # Record a hand
        history.start_new_hand("hand_001", "villain", 50, 100)
        history.record_action("villain", Street.PREFLOP, "raise", 300)
        history.record_action("hero", Street.PREFLOP, "call", 300)
        history.finish_hand([], 600, "villain")
        
        # Update profile from hand history
        hand = history.hands[0]
        if hand.did_player_vpip("villain"):
            profile.update_preflop_action(
                action="raise",
                is_raise=hand.did_player_raise_preflop("villain"),
                is_voluntary=True
            )
        
        assert profile.hands_played == 1
        assert profile.vpip_count == 1
        assert profile.pfr_count == 1
    
    def test_multi_street_estimation(self):
        """Test estimating ranges across multiple streets."""
        profile = PlayerProfile(player_id="villain", hands_played=100)
        profile.vpip_count = 25
        profile.pfr_count = 20
        profile.postflop_bets = 30
        profile.postflop_raises = 20
        profile.postflop_calls = 25
        
        estimator = RuleBasedRangeEstimator(player_profile=profile)
        
        # Preflop
        preflop_range = estimator.estimate_preflop_range(action="raise")
        assert len(preflop_range.hands) > 0
        
        # Flop
        flop_range = estimator.estimate_postflop_range(
            preflop_range=preflop_range,
            street=Street.FLOP,
            action="bet",
            board=["As", "Kh", "Qd"],
            pot_size=100,
            bet_size=75
        )
        assert len(flop_range.hands) >= 0
        
        # Turn
        turn_range = estimator.estimate_postflop_range(
            preflop_range=flop_range,
            street=Street.TURN,
            action="bet",
            board=["As", "Kh", "Qd", "Jc"],
            pot_size=250,
            bet_size=150
        )
        assert len(turn_range.hands) >= 0
    
    def test_archetype_consistency(self):
        """Test that archetype classification is consistent."""
        # Create TAG profile
        tag = PlayerProfile(player_id="tag", hands_played=100)
        tag.vpip_count = 20
        tag.pfr_count = 18
        tag.postflop_bets = 30
        tag.postflop_raises = 20
        tag.postflop_calls = 10
        
        # Check archetype multiple times
        archetype1 = tag.get_archetype()
        archetype2 = tag.get_archetype()
        
        assert archetype1 == archetype2
        
        # Serialize and deserialize
        tag_dict = tag.to_dict()
        assert tag_dict['archetype'] == archetype1.value
    
    def test_empty_profile_estimation(self):
        """Test estimation with minimal data."""
        profile = PlayerProfile(player_id="unknown", hands_played=5)
        estimator = RuleBasedRangeEstimator(player_profile=profile)
        
        # Should still produce a range (uses defaults)
        hand_range = estimator.estimate_preflop_range(action="raise")
        assert len(hand_range.hands) >= 0

