"""
Tests for PlayerProfile class.
"""

import pytest
from pypokerengine.opponent_modeling.player_profile import (
    PlayerProfile, PlayerArchetype
)


class TestPlayerProfile:
    """Tests for PlayerProfile tracking."""
    
    def test_initialization(self):
        """Test profile initialization."""
        profile = PlayerProfile(player_id="test_player")
        assert profile.player_id == "test_player"
        assert profile.hands_played == 0
        assert profile.vpip == 0.0
        assert profile.pfr == 0.0
    
    def test_vpip_calculation(self):
        """Test VPIP calculation."""
        profile = PlayerProfile(player_id="test")
        profile.hands_played = 100
        profile.vpip_count = 25
        
        assert profile.vpip == 0.25
    
    def test_pfr_calculation(self):
        """Test PFR calculation."""
        profile = PlayerProfile(player_id="test")
        profile.hands_played = 100
        profile.pfr_count = 20
        
        assert profile.pfr == 0.20
    
    def test_aggression_factor_calculation(self):
        """Test aggression factor calculation."""
        profile = PlayerProfile(player_id="test")
        profile.postflop_bets = 30
        profile.postflop_raises = 20
        profile.postflop_calls = 25
        
        # AF = (Bets + Raises) / Calls = (30 + 20) / 25 = 2.0
        assert profile.aggression_factor == 2.0
    
    def test_aggression_factor_no_calls(self):
        """Test aggression factor when no calls."""
        profile = PlayerProfile(player_id="test")
        profile.postflop_bets = 30
        profile.postflop_raises = 20
        profile.postflop_calls = 0
        
        # Should return high value, not divide by zero
        assert profile.aggression_factor == 50.0
    
    def test_fold_to_cbet(self):
        """Test fold to c-bet calculation."""
        profile = PlayerProfile(player_id="test")
        profile.cbet_faced = 20
        profile.cbet_folded = 15
        
        assert profile.fold_to_cbet == 0.75
    
    def test_three_bet_percentage(self):
        """Test 3-bet percentage."""
        profile = PlayerProfile(player_id="test")
        profile.three_bet_opportunities = 50
        profile.three_bet_count = 10
        
        assert profile.three_bet_percentage == 0.20
    
    def test_archetype_tight_aggressive(self):
        """Test TAG archetype classification."""
        profile = PlayerProfile(player_id="test", hands_played=100)
        profile.vpip_count = 20  # 20% VPIP (tight)
        profile.pfr_count = 18   # 18% PFR (aggressive)
        profile.postflop_bets = 30
        profile.postflop_raises = 20
        profile.postflop_calls = 10  # AF = 5.0 (aggressive)
        
        assert profile.get_archetype() == PlayerArchetype.TIGHT_AGGRESSIVE
    
    def test_archetype_loose_passive(self):
        """Test loose-passive archetype classification."""
        profile = PlayerProfile(player_id="test", hands_played=100)
        profile.vpip_count = 45  # 45% VPIP (loose)
        profile.pfr_count = 10   # 10% PFR (passive)
        profile.postflop_bets = 10
        profile.postflop_raises = 5
        profile.postflop_calls = 30  # AF = 0.5 (passive)
        
        assert profile.get_archetype() == PlayerArchetype.LOOSE_PASSIVE
    
    def test_archetype_unknown_insufficient_hands(self):
        """Test unknown archetype with insufficient data."""
        profile = PlayerProfile(player_id="test", hands_played=10)
        
        assert profile.get_archetype() == PlayerArchetype.UNKNOWN
    
    def test_update_preflop_action(self):
        """Test updating preflop action."""
        profile = PlayerProfile(player_id="test")
        
        # Raise preflop
        profile.update_preflop_action(
            action="raise",
            is_raise=True,
            is_voluntary=True
        )
        
        assert profile.hands_played == 1
        assert profile.vpip_count == 1
        assert profile.pfr_count == 1
    
    def test_update_postflop_action(self):
        """Test updating postflop action."""
        profile = PlayerProfile(player_id="test")
        
        # Bet on flop
        profile.update_postflop_action(
            action="bet",
            is_bet=True
        )
        
        assert profile.postflop_bets == 1
        
        # Call on turn
        profile.update_postflop_action(
            action="call",
            is_call=True,
            faced_cbet=True
        )
        
        assert profile.postflop_calls == 1
        assert profile.cbet_faced == 1
        assert profile.cbet_called == 1
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        profile = PlayerProfile(player_id="test", hands_played=100)
        profile.vpip_count = 25
        profile.pfr_count = 20
        
        profile_dict = profile.to_dict()
        
        assert profile_dict['player_id'] == "test"
        assert profile_dict['hands_played'] == 100
        assert profile_dict['vpip'] == 0.25
        assert profile_dict['pfr'] == 0.20
        assert 'archetype' in profile_dict
        assert 'raw_stats' in profile_dict

