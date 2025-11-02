"""
Tests for HandRange module.

Tests range parsing, combo generation, and blocker removal.
"""

import pytest
from pypokerengine.simulation.hand_range import HandRange, parse_hand_to_cards
from pypokerengine.engine.card import Card


class TestHandRange:
    """Test HandRange parsing and functionality."""
    
    def test_single_pair(self):
        """Test parsing single pair."""
        range_obj = HandRange.from_string("AA")
        assert len(range_obj.hands) == 1
        assert "AA" in range_obj.hands
    
    def test_multiple_hands(self):
        """Test parsing multiple hands."""
        range_obj = HandRange.from_string("AA,KK,QQ")
        assert len(range_obj.hands) == 3
        assert "AA" in range_obj.hands
        assert "KK" in range_obj.hands
        assert "QQ" in range_obj.hands
    
    def test_pair_plus(self):
        """Test pair+ notation."""
        range_obj = HandRange.from_string("JJ+")
        # Should be JJ, QQ, KK, AA
        assert len(range_obj.hands) == 4
        assert "JJ" in range_obj.hands
        assert "QQ" in range_obj.hands
        assert "KK" in range_obj.hands
        assert "AA" in range_obj.hands
    
    def test_pair_range(self):
        """Test pair range notation."""
        range_obj = HandRange.from_string("22-55")
        assert len(range_obj.hands) == 4
        assert "22" in range_obj.hands
        assert "33" in range_obj.hands
        assert "44" in range_obj.hands
        assert "55" in range_obj.hands
    
    def test_suited_plus(self):
        """Test suited+ notation."""
        range_obj = HandRange.from_string("ATs+")
        # ATs, AJs, AQs, (but not AKs since T to K = T, J, Q)
        assert "ATs" in range_obj.hands or "ATs" in str(range_obj)
        # Check if contains suited ace hands
        suited_aces = [h for h in range_obj.hands if h.startswith('A') and h.endswith('s')]
        assert len(suited_aces) >= 3  # At least ATs, AJs, AQs
    
    def test_offsuit_plus(self):
        """Test offsuit+ notation."""
        range_obj = HandRange.from_string("AJo+")
        # AJo, AQo, (but not AKo since J to K = J, Q)
        offsuit_aces = [h for h in range_obj.hands if h.startswith('A') and h.endswith('o')]
        assert len(offsuit_aces) >= 2  # At least AJo, AQo
    
    def test_suited_hand(self):
        """Test parsing suited hand."""
        range_obj = HandRange.from_string("AKs")
        assert "AKS" in range_obj.hands or "AKs" in range_obj.hands
    
    def test_offsuit_hand(self):
        """Test parsing offsuit hand."""
        range_obj = HandRange.from_string("AKo")
        assert "AKO" in range_obj.hands or "AKo" in range_obj.hands
    
    def test_combo_count_pair(self):
        """Test combination count for pairs."""
        range_obj = HandRange.from_string("AA")
        combos = range_obj.get_combinations()
        # AA has 6 combinations (4 choose 2)
        assert len(combos) == 6
    
    def test_combo_count_suited(self):
        """Test combination count for suited hands."""
        range_obj = HandRange.from_string("AKs")
        combos = range_obj.get_combinations()
        # AKs has 4 combinations (one per suit)
        assert len(combos) == 4
    
    def test_combo_count_offsuit(self):
        """Test combination count for offsuit hands."""
        range_obj = HandRange.from_string("AKo")
        combos = range_obj.get_combinations()
        # AKo has 12 combinations (4*3)
        assert len(combos) == 12
    
    def test_blocker_removal(self):
        """Test that blockers are properly removed."""
        range_obj = HandRange.from_string("AA")
        
        # Remove one ace
        ace_spades = Card(14, 0)  # Ace of spades
        combos_with_blocker = range_obj.get_combinations(exclude_cards=[ace_spades])
        
        # Should have fewer than 6 combinations
        assert len(combos_with_blocker) < 6
        
        # Verify no combo contains the blocker
        for c1, c2 in combos_with_blocker:
            assert c1 != ace_spades
            assert c2 != ace_spades
    
    def test_blocker_removal_eliminates_all(self):
        """Test that blockers can eliminate all combinations."""
        range_obj = HandRange.from_string("AKs")
        
        # Block all aces
        blockers = [Card(14, s) for s in range(4)]
        combos_with_blockers = range_obj.get_combinations(exclude_cards=blockers)
        
        # Should have 0 combinations
        assert len(combos_with_blockers) == 0
    
    def test_complex_range(self):
        """Test complex range notation."""
        range_obj = HandRange.from_string("AA,KK,QQ,AKs,AKo")
        assert len(range_obj.hands) >= 4
        
        combos = range_obj.get_combinations()
        # AA(6) + KK(6) + QQ(6) + AKs(4) + AKo(12) = 34
        assert len(combos) == 34


class TestParseHandToCards:
    """Test hand string parsing."""
    
    def test_parse_valid_hand(self):
        """Test parsing valid hand."""
        card1, card2 = parse_hand_to_cards("AhKh")
        assert card1.rank == 14
        assert card1.suit == 2  # Hearts
        assert card2.rank == 13
        assert card2.suit == 2
    
    def test_parse_different_suits(self):
        """Test parsing hand with different suits."""
        card1, card2 = parse_hand_to_cards("AsKd")
        assert card1.rank == 14
        assert card1.suit == 3  # Spades
        assert card2.rank == 13
        assert card2.suit == 1  # Diamonds
    
    def test_parse_invalid_length(self):
        """Test that invalid length raises error."""
        with pytest.raises(ValueError):
            parse_hand_to_cards("AK")
    
    def test_parse_invalid_length_too_long(self):
        """Test that too long string raises error."""
        with pytest.raises(ValueError):
            parse_hand_to_cards("AhKhQd")


class TestHandRangeEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_range(self):
        """Test empty range."""
        range_obj = HandRange.from_string("")
        assert len(range_obj.hands) == 0
    
    def test_whitespace_handling(self):
        """Test whitespace is handled correctly."""
        range_obj = HandRange.from_string("AA, KK , QQ")
        assert len(range_obj.hands) == 3
    
    def test_count_combinations_method(self):
        """Test count_combinations convenience method."""
        range_obj = HandRange.from_string("AA,KK")
        count = range_obj.count_combinations()
        assert count == 12  # 6 + 6
    
    def test_string_representation(self):
        """Test string representation."""
        range_obj = HandRange.from_string("AA,KK")
        str_repr = str(range_obj)
        assert "AA" in str_repr or "aa" in str_repr.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

