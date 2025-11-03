"""
Feature Engineering Module

Extract features from player profiles and game state for ML models.
"""

from typing import Dict, List, Optional, Any
import numpy as np
from .player_profile import PlayerProfile
from .hand_history import Street, ActionRecord
from ..engine.card import Card


class FeatureExtractor:
    """
    Extracts features from game state and player stats for ML models.
    
    Features include:
    - Player statistics (VPIP, PFR, AF, etc.)
    - Positional information
    - Action sequence encoding
    - Pot odds and stack-to-pot ratios
    - Board texture features (postflop)
    """
    
    @staticmethod
    def extract_player_features(profile: PlayerProfile) -> Dict[str, float]:
        """
        Extract numerical features from player profile.
        
        Args:
            profile: PlayerProfile to extract from
            
        Returns:
            Dictionary of feature names to values
        """
        return {
            'vpip': profile.vpip,
            'pfr': profile.pfr,
            'aggression_factor': profile.aggression_factor,
            'fold_to_cbet': profile.fold_to_cbet,
            'three_bet_pct': profile.three_bet_percentage,
            'wtsd': profile.wtsd,
            'won_at_sd': profile.won_at_sd,
            'hands_played': min(profile.hands_played / 100.0, 10.0),  # Normalize to 0-10
            
            # Derived features
            'pfr_vpip_ratio': profile.pfr / profile.vpip if profile.vpip > 0 else 0,
            'is_aggressive': 1.0 if profile.aggression_factor >= 2.0 else 0.0,
            'is_tight': 1.0 if profile.vpip < 0.25 else 0.0,
        }
    
    @staticmethod
    def extract_action_features(
        action_type: str,
        amount: int = 0,
        pot_size: int = 0,
        effective_stack: int = 0,
        facing_bet: int = 0
    ) -> Dict[str, float]:
        """
        Extract features from a single action.
        
        Args:
            action_type: Type of action
            amount: Bet/raise amount
            pot_size: Current pot size
            effective_stack: Player's remaining stack
            facing_bet: Amount player is facing
            
        Returns:
            Dictionary of action features
        """
        # One-hot encode action type
        features = {
            'action_fold': 1.0 if action_type == 'fold' else 0.0,
            'action_check': 1.0 if action_type == 'check' else 0.0,
            'action_call': 1.0 if action_type == 'call' else 0.0,
            'action_bet': 1.0 if action_type == 'bet' else 0.0,
            'action_raise': 1.0 if action_type == 'raise' else 0.0,
        }
        
        # Pot odds and sizing
        if pot_size > 0:
            features['pot_odds'] = facing_bet / (pot_size + facing_bet) if facing_bet > 0 else 0
            features['bet_to_pot_ratio'] = amount / pot_size if amount > 0 else 0
        else:
            features['pot_odds'] = 0
            features['bet_to_pot_ratio'] = 0
        
        # Stack depth
        if pot_size > 0:
            features['spr'] = effective_stack / pot_size  # Stack-to-Pot Ratio
        else:
            features['spr'] = 0
        
        return features
    
    @staticmethod
    def extract_positional_features(position: Optional[str]) -> Dict[str, float]:
        """
        Extract position features.
        
        Args:
            position: Position string (BTN, SB, BB)
            
        Returns:
            One-hot encoded position features
        """
        return {
            'position_btn': 1.0 if position == 'BTN' else 0.0,
            'position_sb': 1.0 if position == 'SB' else 0.0,
            'position_bb': 1.0 if position == 'BB' else 0.0,
        }
    
    @staticmethod
    def extract_street_features(street: Street) -> Dict[str, float]:
        """
        Extract street features.
        
        Args:
            street: Current betting street
            
        Returns:
            One-hot encoded street features
        """
        return {
            'street_preflop': 1.0 if street == Street.PREFLOP else 0.0,
            'street_flop': 1.0 if street == Street.FLOP else 0.0,
            'street_turn': 1.0 if street == Street.TURN else 0.0,
            'street_river': 1.0 if street == Street.RIVER else 0.0,
        }
    
    @staticmethod
    def extract_board_texture_features(board: List[str]) -> Dict[str, float]:
        """
        Extract board texture features from community cards.
        
        Args:
            board: List of card strings like ["As", "Kh", "Qd"]
            
        Returns:
            Dictionary of board texture features
        """
        if not board:
            return {
                'board_paired': 0.0,
                'board_trips': 0.0,
                'board_flush_possible': 0.0,
                'board_straight_possible': 0.0,
                'board_high_card': 0.0,
                'board_coordinated': 0.0,
            }
        
        # Parse cards
        try:
            cards = [Card.from_string(c) for c in board]
        except:
            # If parsing fails, return zeros
            return {
                'board_paired': 0.0,
                'board_trips': 0.0,
                'board_flush_possible': 0.0,
                'board_straight_possible': 0.0,
                'board_high_card': 0.0,
                'board_coordinated': 0.0,
            }
        
        # Analyze ranks
        ranks = [c.rank for c in cards]
        rank_counts = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        
        max_rank_count = max(rank_counts.values()) if rank_counts else 0
        
        # Analyze suits
        suits = [c.suit for c in cards]
        suit_counts = {}
        for s in suits:
            suit_counts[s] = suit_counts.get(s, 0) + 1
        
        max_suit_count = max(suit_counts.values()) if suit_counts else 0
        
        # Calculate features
        features = {
            'board_paired': 1.0 if max_rank_count >= 2 else 0.0,
            'board_trips': 1.0 if max_rank_count >= 3 else 0.0,
            'board_flush_possible': 1.0 if max_suit_count >= 3 else 0.0,
            'board_straight_possible': float(FeatureExtractor._is_straight_possible(ranks)),
            'board_high_card': max(ranks) / 14.0 if ranks else 0.0,  # Normalize to 0-1
            'board_coordinated': float(FeatureExtractor._is_coordinated(ranks)),
        }
        
        return features
    
    @staticmethod
    def _is_straight_possible(ranks: List[int]) -> bool:
        """Check if a straight is possible with these ranks."""
        if len(ranks) < 3:
            return False
        
        sorted_ranks = sorted(set(ranks))
        
        # Check for gaps
        max_gap = 0
        for i in range(len(sorted_ranks) - 1):
            gap = sorted_ranks[i + 1] - sorted_ranks[i]
            max_gap = max(max_gap, gap)
        
        # If cards span <= 4 ranks, straight is possible
        range_span = sorted_ranks[-1] - sorted_ranks[0]
        return range_span <= 4 or max_gap <= 2
    
    @staticmethod
    def _is_coordinated(ranks: List[int]) -> bool:
        """Check if board is coordinated (cards close together)."""
        if len(ranks) < 2:
            return False
        
        sorted_ranks = sorted(set(ranks))
        range_span = sorted_ranks[-1] - sorted_ranks[0]
        
        # Board is coordinated if cards are within 5 ranks
        return range_span <= 5


def extract_features(
    player_profile: PlayerProfile,
    action: str,
    street: Street,
    board: Optional[List[str]] = None,
    position: Optional[str] = None,
    amount: int = 0,
    pot_size: int = 0,
    effective_stack: int = 0,
    facing_bet: int = 0
) -> np.ndarray:
    """
    Convenience function to extract all features as numpy array.
    
    Args:
        player_profile: Player statistics
        action: Action type
        street: Current street
        board: Community cards
        position: Player position
        amount: Bet amount
        pot_size: Pot size
        effective_stack: Stack remaining
        facing_bet: Bet facing
        
    Returns:
        Numpy array of features in fixed order
    """
    extractor = FeatureExtractor()
    
    # Extract all feature groups
    player_feats = extractor.extract_player_features(player_profile)
    action_feats = extractor.extract_action_features(action, amount, pot_size, effective_stack, facing_bet)
    position_feats = extractor.extract_positional_features(position)
    street_feats = extractor.extract_street_features(street)
    board_feats = extractor.extract_board_texture_features(board or [])
    
    # Combine all features in fixed order
    all_features = {**player_feats, **action_feats, **position_feats, **street_feats, **board_feats}
    
    # Convert to numpy array with consistent ordering
    feature_names = sorted(all_features.keys())
    feature_array = np.array([all_features[name] for name in feature_names])
    
    return feature_array


def get_feature_names() -> List[str]:
    """
    Get ordered list of feature names.
    
    Returns:
        List of feature names in the order they appear in feature vectors
    """
    # Create dummy features to get names
    dummy_profile = PlayerProfile(player_id="dummy", hands_played=100)
    dummy_profile.vpip_count = 25
    dummy_profile.pfr_count = 20
    
    extractor = FeatureExtractor()
    player_feats = extractor.extract_player_features(dummy_profile)
    action_feats = extractor.extract_action_features("call")
    position_feats = extractor.extract_positional_features("BTN")
    street_feats = extractor.extract_street_features(Street.FLOP)
    board_feats = extractor.extract_board_texture_features(["As", "Kh", "Qd"])
    
    all_features = {**player_feats, **action_feats, **position_feats, **street_feats, **board_feats}
    
    return sorted(all_features.keys())

