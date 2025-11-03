"""
Tests for HandHistory tracker.
"""

import pytest
from pypokerengine.opponent_modeling.hand_history import (
    HandHistory, HandRecord, ActionRecord, Street
)


class TestHandHistory:
    """Tests for hand history tracking."""
    
    def test_start_new_hand(self):
        """Test starting a new hand."""
        history = HandHistory()
        
        hand = history.start_new_hand(
            hand_id="hand_001",
            button_player="player1",
            small_blind=50,
            big_blind=100
        )
        
        assert hand.hand_id == "hand_001"
        assert hand.button_player == "player1"
        assert hand.small_blind == 50
        assert hand.big_blind == 100
        assert len(hand.actions) == 0
    
    def test_record_action(self):
        """Test recording an action."""
        history = HandHistory()
        history.start_new_hand("hand_001", "player1", 50, 100)
        
        history.record_action(
            player_id="player1",
            street=Street.PREFLOP,
            action_type="raise",
            amount=200,
            pot_size=150,
            position="BTN"
        )
        
        assert len(history._current_hand.actions) == 1
        action = history._current_hand.actions[0]
        assert action.player_id == "player1"
        assert action.action_type == "raise"
        assert action.amount == 200
    
    def test_finish_hand(self):
        """Test finishing a hand."""
        history = HandHistory()
        history.start_new_hand("hand_001", "player1", 50, 100)
        
        history.record_action("player1", Street.PREFLOP, "raise", 200)
        history.record_action("player2", Street.PREFLOP, "call", 200)
        
        history.finish_hand(
            board=["As", "Kh", "Qd"],
            pot_size=400,
            winner="player1"
        )
        
        assert len(history.hands) == 1
        assert history._current_hand is None
        
        completed_hand = history.hands[0]
        assert completed_hand.board == ["As", "Kh", "Qd"]
        assert completed_hand.winner == "player1"
    
    def test_get_player_hands(self):
        """Test getting hands for a specific player."""
        history = HandHistory()
        
        # Hand 1
        history.start_new_hand("hand_001", "player1", 50, 100)
        history.record_action("player1", Street.PREFLOP, "raise", 200)
        history.finish_hand([], 400, "player1")
        
        # Hand 2
        history.start_new_hand("hand_002", "player2", 50, 100)
        history.record_action("player2", Street.PREFLOP, "call", 100)
        history.finish_hand([], 200, "player2")
        
        # Hand 3
        history.start_new_hand("hand_003", "player1", 50, 100)
        history.record_action("player1", Street.PREFLOP, "fold", 0)
        history.finish_hand([], 100, "player2")
        
        player1_hands = history.get_player_hands("player1")
        assert len(player1_hands) == 2
    
    def test_count_hands(self):
        """Test counting hands."""
        history = HandHistory()
        
        for i in range(5):
            history.start_new_hand(f"hand_{i}", "player1", 50, 100)
            history.finish_hand([], 100, "player1")
        
        assert history.count_hands() == 5
        assert len(history) == 5
    
    def test_action_record_to_dict(self):
        """Test action record serialization."""
        action = ActionRecord(
            player_id="player1",
            street=Street.FLOP,
            action_type="bet",
            amount=150,
            pot_size=300
        )
        
        action_dict = action.to_dict()
        assert action_dict['player_id'] == "player1"
        assert action_dict['street'] == "flop"
        assert action_dict['action_type'] == "bet"
    
    def test_hand_record_preflop_analysis(self):
        """Test preflop action analysis."""
        hand = HandRecord(
            hand_id="test",
            button_player="player1",
            small_blind=50,
            big_blind=100
        )
        
        hand.add_action(ActionRecord("player1", Street.PREFLOP, "raise", 200))
        hand.add_action(ActionRecord("player2", Street.PREFLOP, "call", 200))
        
        assert hand.did_player_vpip("player1") is True
        assert hand.did_player_vpip("player2") is True
        assert hand.did_player_raise_preflop("player1") is True
        assert hand.did_player_raise_preflop("player2") is False
    
    def test_get_actions_by_street(self):
        """Test filtering actions by street."""
        hand = HandRecord("test", "player1", 50, 100)
        
        hand.add_action(ActionRecord("player1", Street.PREFLOP, "raise"))
        hand.add_action(ActionRecord("player2", Street.PREFLOP, "call"))
        hand.add_action(ActionRecord("player1", Street.FLOP, "bet"))
        hand.add_action(ActionRecord("player2", Street.FLOP, "fold"))
        
        preflop_actions = hand.get_actions_by_street(Street.PREFLOP)
        assert len(preflop_actions) == 2
        
        flop_actions = hand.get_actions_by_street(Street.FLOP)
        assert len(flop_actions) == 2

