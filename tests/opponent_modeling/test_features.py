"""
Tests for feature extraction.
"""

import pytest
import numpy as np
from pypokerengine.opponent_modeling.features import (
    FeatureExtractor, extract_features, get_feature_names
)
from pypokerengine.opponent_modeling.player_profile import PlayerProfile
from pypokerengine.opponent_modeling.hand_history import Street


class TestFeatureExtractor:
    """Tests for feature extraction."""
    
    def test_extract_player_features(self):
        """Test extracting player features."""
        profile = PlayerProfile(player_id="test", hands_played=100)
        profile.vpip_count = 25
        profile.pfr_count = 20
        profile.postflop_bets = 30
        profile.postflop_raises = 20
        profile.postflop_calls = 25
        
        extractor = FeatureExtractor()
        features = extractor.extract_player_features(profile)
        
        assert 'vpip' in features
        assert 'pfr' in features
        assert 'aggression_factor' in features
        assert features['vpip'] == 0.25
        assert features['pfr'] == 0.20
    
    def test_extract_action_features(self):
        """Test extracting action features."""
        extractor = FeatureExtractor()
        features = extractor.extract_action_features(
            action_type="bet",
            amount=75,
            pot_size=100,
            effective_stack=1000,
            facing_bet=0
        )
        
        assert 'action_bet' in features
        assert features['action_bet'] == 1.0
        assert 'bet_to_pot_ratio' in features
        assert features['bet_to_pot_ratio'] == 0.75
    
    def test_extract_positional_features(self):
        """Test extracting positional features."""
        extractor = FeatureExtractor()
        
        btn_features = extractor.extract_positional_features("BTN")
        assert btn_features['position_btn'] == 1.0
        assert btn_features['position_sb'] == 0.0
        
        sb_features = extractor.extract_positional_features("SB")
        assert sb_features['position_sb'] == 1.0
        assert sb_features['position_btn'] == 0.0
    
    def test_extract_street_features(self):
        """Test extracting street features."""
        extractor = FeatureExtractor()
        
        preflop_features = extractor.extract_street_features(Street.PREFLOP)
        assert preflop_features['street_preflop'] == 1.0
        assert preflop_features['street_flop'] == 0.0
        
        flop_features = extractor.extract_street_features(Street.FLOP)
        assert flop_features['street_flop'] == 1.0
        assert flop_features['street_preflop'] == 0.0
    
    def test_extract_board_texture_features(self):
        """Test extracting board texture features."""
        extractor = FeatureExtractor()
        
        # Paired board
        paired_board = ["As", "Ah", "Kd"]
        features = extractor.extract_board_texture_features(paired_board)
        assert features['board_paired'] == 1.0
        
        # Flush draw board
        flush_board = ["As", "Ks", "Qs"]
        features = extractor.extract_board_texture_features(flush_board)
        assert features['board_flush_possible'] == 1.0
        
        # Empty board (preflop)
        empty_features = extractor.extract_board_texture_features([])
        assert empty_features['board_paired'] == 0.0
    
    def test_extract_features_convenience_function(self):
        """Test convenience function for extracting all features."""
        profile = PlayerProfile(player_id="test", hands_played=100)
        profile.vpip_count = 25
        profile.pfr_count = 20
        
        features = extract_features(
            player_profile=profile,
            action="bet",
            street=Street.FLOP,
            board=["As", "Kh", "Qd"],
            position="BTN",
            amount=75,
            pot_size=100,
            effective_stack=1000,
            facing_bet=0
        )
        
        # Should return numpy array
        assert isinstance(features, np.ndarray)
        assert len(features) > 0
    
    def test_get_feature_names(self):
        """Test getting feature names."""
        feature_names = get_feature_names()
        
        assert isinstance(feature_names, list)
        assert len(feature_names) > 0
        assert 'vpip' in feature_names
        assert 'pfr' in feature_names
        assert 'aggression_factor' in feature_names
    
    def test_board_straight_possible(self):
        """Test detecting straight possibility."""
        extractor = FeatureExtractor()
        
        # Coordinated board (straight possible)
        coordinated = ["9s", "Th", "Jd"]
        assert extractor._is_straight_possible([9, 10, 11]) is True
        
        # Rainbow board (no straight)
        rainbow = ["2s", "7h", "Kd"]
        assert extractor._is_straight_possible([2, 7, 13]) is False
    
    def test_board_coordinated(self):
        """Test detecting coordinated boards."""
        extractor = FeatureExtractor()
        
        # Coordinated
        assert extractor._is_coordinated([9, 10, 11]) is True
        
        # Not coordinated
        assert extractor._is_coordinated([2, 7, 13]) is False

