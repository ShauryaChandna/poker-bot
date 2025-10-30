"""
Round Management for Poker

This module provides the Round class for managing poker hand rounds.
"""

from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from .player import Player
from .card import Card, Deck
from .action_manager import ActionManager
from .hand_evaluator import HandEvaluator


class Street(Enum):
    """Betting street constants."""
    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class Round:
    """
    Manages a single poker hand from deal to showdown.
    
    Handles:
    - Card dealing (hole cards and community cards)
    - Betting rounds (preflop, flop, turn, river)
    - Pot management
    - Winner determination
    """
    
    def __init__(
        self,
        players: List[Player],
        small_blind: int,
        big_blind: int,
        dealer_position: int,
        deck: Deck
    ):
        """
        Initialize a new round.
        
        Args:
            players: List of players (should be 2 for heads-up)
            small_blind: Small blind amount
            big_blind: Big blind amount
            dealer_position: Index of dealer (0 or 1)
            deck: Deck to use for this hand
        """
        self.players = players
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.dealer_position = dealer_position
        self.deck = deck
        
        # Game state
        self.pot = 0
        self.current_bet = 0
        self.street = Street.PREFLOP
        self.community_cards: List[Card] = []
        
        # Action tracking
        self.action_history: List[Dict[str, Any]] = []
        self.street_actions: Dict[Street, List[Dict[str, Any]]] = {
            Street.PREFLOP: [],
            Street.FLOP: [],
            Street.TURN: [],
            Street.RIVER: []
        }
        
        # State flags
        self.is_complete = False
        self.winners: List[str] = []
        self.winning_hand: str = ""
        self.last_aggressor = None
    
    def start_hand(self):
        """Start the hand by dealing hole cards and posting blinds."""
        # Reset player states
        for player in self.players:
            player.reset_for_new_hand()
        
        # Shuffle and deal hole cards
        self.deck.reset()
        self.deck.shuffle()
        
        for player in self.players:
            hole_cards = self.deck.deal(2)
            player.deal_hole_cards(hole_cards)
        
        # Post blinds (in heads-up, dealer posts small blind)
        sb_player = self.players[self.dealer_position]
        bb_player = self.players[1 - self.dealer_position]
        
        sb_player.position = "SB"
        bb_player.position = "BB"
        
        # Post blinds
        sb_added = sb_player.post_blind(self.small_blind, "small")
        bb_added = bb_player.post_blind(self.big_blind, "big")
        
        self.pot += sb_added + bb_added
        self.current_bet = self.big_blind
        
        # Record blind actions
        self._record_action(sb_player.name, "small_blind", self.small_blind)
        self._record_action(bb_player.name, "big_blind", self.big_blind)
    
    def run_betting_round(
        self,
        action_callback: Callable[[Player, Dict[str, Any]], tuple]
    ) -> bool:
        """
        Run a single betting round.
        
        Args:
            action_callback: Function that takes (player, legal_actions) and
                           returns (action, amount)
        
        Returns:
            True if hand should continue, False if hand is over
        """
        # Determine action order
        if self.street == Street.PREFLOP:
            # Preflop: SB acts first in heads-up
            acting_order = [self.dealer_position, 1 - self.dealer_position]
        else:
            # Postflop: BB acts first (out of position)
            acting_order = [1 - self.dealer_position, self.dealer_position]
        
        actions_this_round = 0
        current_player_index = 0  # Track which player should act next
        
        while True:
            active_players = [p for p in self.players if p.can_act()]
            
            # Check if betting is complete
            if len(active_players) <= 1:
                return len([p for p in self.players if p.is_active]) > 1
            
            # Check if all active players have acted and bets are equal
            if actions_this_round >= len(active_players):
                all_bets_equal = len(set(
                    p.current_bet for p in active_players
                )) == 1
                if all_bets_equal:
                    break
            
            # Additional check: if all players have checked (no bets) and all have acted
            if self.current_bet == 0 and actions_this_round >= len(active_players):
                break
            
            # Find the next player who needs to act
            player_to_act = None
            for i in range(len(acting_order)):
                pos = acting_order[(current_player_index + i) % len(acting_order)]
                player = self.players[pos]
                if not player.can_act():
                    continue
                
                # Check if player needs to act
                # Player needs to act if:
                # 1. They haven't matched the current bet, OR
                # 2. Not all players have acted yet (but not if this player just raised)
                needs_to_act = player.current_bet < self.current_bet or (actions_this_round < len(active_players) and self.last_aggressor != player)
                
                if needs_to_act:
                    player_to_act = player
                    current_player_index = (current_player_index + i + 1) % len(acting_order)
                    break
            
            # If no player needs to act, all players have checked through
            if player_to_act is None:
                break
            
            player = player_to_act
            legal_actions = ActionManager.get_legal_actions(
                player, self.players, self.current_bet, self.pot, self.big_blind
            )
            
            # Get action from callback
            action, amount = action_callback(player, legal_actions)
            
            # Validate and apply action
            is_valid, error = ActionManager.validate_action(
                player, action, amount, legal_actions
            )
            
            if not is_valid:
                raise ValueError(f"Invalid action: {error}")
            
            # Apply action
            added = ActionManager.apply_action(
                player, action, amount, self.current_bet
            )
            self.pot += added
            
            # Update current bet if raised
            if action.lower() in ["raise", "bet"]:
                self.current_bet = amount
                self.last_aggressor = player
                actions_this_round = 1  # Reset count after raise
            else:
                actions_this_round += 1
            
            # Record action
            self._record_action(player.name, action, amount)
            
            # Check if hand is over
            if action.lower() == "fold":
                return len([p for p in self.players if p.is_active]) > 1
        
        return True
    
    def advance_street(self):
        """Advance to the next street and deal community cards."""
        # Reset bets for new street
        for player in self.players:
            player.reset_current_bet()
        self.current_bet = 0
        # Reset last aggressor for new street
        self.last_aggressor = None
        
        if self.street == Street.PREFLOP:
            # Deal flop (3 cards)
            self.community_cards = self.deck.deal(3)
            self.street = Street.FLOP
        elif self.street == Street.FLOP:
            # Deal turn (1 card)
            self.community_cards.append(self.deck.deal_one())
            self.street = Street.TURN
        elif self.street == Street.TURN:
            # Deal river (1 card)
            self.community_cards.append(self.deck.deal_one())
            self.street = Street.RIVER
        elif self.street == Street.RIVER:
            self.street = Street.SHOWDOWN
    
    def determine_winner(self) -> Dict[str, Any]:
        """
        Determine the winner(s) and award pot.
        
        Returns:
            Dictionary with winner information
        """
        active_players = [p for p in self.players if p.is_active]
        
        if len(active_players) == 1:
            # Winner by fold
            winner = active_players[0]
            winner.win_pot(self.pot)
            self.winners = [winner.name]
            self.winning_hand = "opponent folded"
            self.is_complete = True
            
            return {
                "winners": [winner.name],
                "pot": self.pot,
                "winning_hand": "opponent folded",
                "hands": {}
            }
        
        # Showdown - evaluate hands
        hands = {}
        for player in active_players:
            full_hand = player.hole_cards + self.community_cards
            rank, tiebreakers, hand_name = HandEvaluator.evaluate_hand(full_hand)
            hands[player.name] = {
                "cards": player.hole_cards,
                "rank": rank,
                "tiebreakers": tiebreakers,
                "hand_name": hand_name
            }
        
        # Find winner(s)
        best_rank = max(h["rank"] for h in hands.values())
        best_tiebreakers = max(
            h["tiebreakers"] for h in hands.values() if h["rank"] == best_rank
        )
        
        winners = [
            name for name, h in hands.items()
            if h["rank"] == best_rank and h["tiebreakers"] == best_tiebreakers
        ]
        
        # Split pot among winners
        pot_share = self.pot // len(winners)
        for winner_name in winners:
            winner_player = next(p for p in self.players if p.name == winner_name)
            winner_player.win_pot(pot_share)
        
        self.winners = winners
        self.winning_hand = hands[winners[0]]["hand_name"]
        self.is_complete = True
        
        return {
            "winners": winners,
            "pot": self.pot,
            "pot_share": pot_share,
            "winning_hand": hands[winners[0]]["hand_name"],
            "hands": hands
        }
    
    def _record_action(self, player_name: str, action: str, amount: int):
        """Record an action in the history."""
        action_record = {
            "player": player_name,
            "action": action,
            "amount": amount,
            "street": self.street.value
        }
        self.action_history.append(action_record)
        self.street_actions[self.street].append(action_record)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current round state for external use (AI, UI, etc.).
        
        Returns:
            Dictionary of current state
        """
        return {
            "street": self.street.value,
            "pot": self.pot,
            "current_bet": self.current_bet,
            "community_cards": [str(card) for card in self.community_cards],
            "players": [p.to_dict() for p in self.players],
            "action_history": self.action_history,
            "is_complete": self.is_complete
        }
    
    def __str__(self) -> str:
        """Return string representation of round state."""
        community_str = " ".join(str(card) for card in self.community_cards) or "none"
        return (f"Street: {self.street.value}, Pot: {self.pot}, "
                f"Current Bet: {self.current_bet}, Board: [{community_str}]")

