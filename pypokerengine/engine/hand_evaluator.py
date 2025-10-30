"""
Hand Evaluator for Poker

This module provides comprehensive hand evaluation for 7-card poker (Texas Hold'em).
Evaluates the best 5-card hand from any combination of cards.
"""

from typing import List, Tuple, Dict
from collections import Counter
from itertools import combinations
from .card import Card


class HandRank:
    """Hand ranking constants."""
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9
    
    NAMES = {
        0: "High Card",
        1: "One Pair",
        2: "Two Pair",
        3: "Three of a Kind",
        4: "Straight",
        5: "Flush",
        6: "Full House",
        7: "Four of a Kind",
        8: "Straight Flush",
        9: "Royal Flush"
    }


class HandEvaluator:
    """
    Evaluates poker hands and determines winners.
    
    Supports full 7-card evaluation for Texas Hold'em.
    """
    
    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[int, List[int], str]:
        """
        Evaluate a poker hand (5-7 cards) and return its rank.
        
        For 7 cards, evaluates all possible 5-card combinations and returns the best.
        
        Args:
            cards: List of 5-7 cards to evaluate
            
        Returns:
            Tuple of (hand_rank, tiebreakers, hand_name)
            - hand_rank: Integer rank (0-9, higher is better)
            - tiebreakers: List of integers for breaking ties
            - hand_name: Human-readable hand description
        """
        if len(cards) < 5:
            raise ValueError(f"Need at least 5 cards, got {len(cards)}")
        
        if len(cards) == 5:
            return HandEvaluator._evaluate_5_cards(cards)
        
        # For 6-7 cards, check all 5-card combinations
        best_rank = -1
        best_tiebreakers = []
        best_name = ""
        
        for combo in combinations(cards, 5):
            rank, tiebreakers, name = HandEvaluator._evaluate_5_cards(list(combo))
            
            # Compare hands
            if rank > best_rank or (rank == best_rank and tiebreakers > best_tiebreakers):
                best_rank = rank
                best_tiebreakers = tiebreakers
                best_name = name
        
        return best_rank, best_tiebreakers, best_name
    
    @staticmethod
    def _evaluate_5_cards(cards: List[Card]) -> Tuple[int, List[int], str]:
        """
        Evaluate exactly 5 cards.
        
        Args:
            cards: Exactly 5 cards
            
        Returns:
            Tuple of (hand_rank, tiebreakers, hand_name)
        """
        if len(cards) != 5:
            raise ValueError(f"Expected 5 cards, got {len(cards)}")
        
        ranks = sorted([card.rank for card in cards], reverse=True)
        suits = [card.suit for card in cards]
        
        is_flush = len(set(suits)) == 1
        is_straight, straight_high = HandEvaluator._check_straight(ranks)
        
        rank_counts = Counter(ranks)
        counts_sorted = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)
        
        # Check for specific hands
        if is_straight and is_flush:
            if straight_high == 14:  # Ace-high straight flush
                return HandRank.ROYAL_FLUSH, [14], "Royal Flush"
            return HandRank.STRAIGHT_FLUSH, [straight_high], f"Straight Flush, {HandEvaluator._rank_name(straight_high)} high"
        
        if counts_sorted[0][1] == 4:  # Four of a kind
            quad_rank = counts_sorted[0][0]
            kicker = counts_sorted[1][0]
            return HandRank.FOUR_OF_A_KIND, [quad_rank, kicker], f"Four of a Kind, {HandEvaluator._rank_name(quad_rank)}s"
        
        if counts_sorted[0][1] == 3 and counts_sorted[1][1] == 2:  # Full house
            trips_rank = counts_sorted[0][0]
            pair_rank = counts_sorted[1][0]
            return HandRank.FULL_HOUSE, [trips_rank, pair_rank], f"Full House, {HandEvaluator._rank_name(trips_rank)}s over {HandEvaluator._rank_name(pair_rank)}s"
        
        if is_flush:
            return HandRank.FLUSH, ranks, f"Flush, {HandEvaluator._rank_name(ranks[0])} high"
        
        if is_straight:
            return HandRank.STRAIGHT, [straight_high], f"Straight, {HandEvaluator._rank_name(straight_high)} high"
        
        if counts_sorted[0][1] == 3:  # Three of a kind
            trips_rank = counts_sorted[0][0]
            kickers = sorted([counts_sorted[1][0], counts_sorted[2][0]], reverse=True)
            return HandRank.THREE_OF_A_KIND, [trips_rank] + kickers, f"Three of a Kind, {HandEvaluator._rank_name(trips_rank)}s"
        
        if counts_sorted[0][1] == 2 and counts_sorted[1][1] == 2:  # Two pair
            high_pair = max(counts_sorted[0][0], counts_sorted[1][0])
            low_pair = min(counts_sorted[0][0], counts_sorted[1][0])
            kicker = counts_sorted[2][0]
            return HandRank.TWO_PAIR, [high_pair, low_pair, kicker], f"Two Pair, {HandEvaluator._rank_name(high_pair)}s and {HandEvaluator._rank_name(low_pair)}s"
        
        if counts_sorted[0][1] == 2:  # One pair
            pair_rank = counts_sorted[0][0]
            kickers = sorted([counts_sorted[1][0], counts_sorted[2][0], counts_sorted[3][0]], reverse=True)
            return HandRank.ONE_PAIR, [pair_rank] + kickers, f"Pair of {HandEvaluator._rank_name(pair_rank)}s"
        
        # High card
        return HandRank.HIGH_CARD, ranks, f"{HandEvaluator._rank_name(ranks[0])} high"
    
    @staticmethod
    def _check_straight(ranks: List[int]) -> Tuple[bool, int]:
        """
        Check if ranks form a straight.
        
        Args:
            ranks: Sorted ranks (descending)
            
        Returns:
            Tuple of (is_straight, high_card_rank)
        """
        # Check for normal straight
        if ranks[0] - ranks[4] == 4 and len(set(ranks)) == 5:
            return True, ranks[0]
        
        # Check for wheel (A-2-3-4-5)
        if ranks == [14, 5, 4, 3, 2]:
            return True, 5  # In a wheel, the straight is 5-high
        
        return False, 0
    
    @staticmethod
    def _rank_name(rank: int) -> str:
        """Get the name of a rank."""
        names = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
                 7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten",
                 11: "Jack", 12: "Queen", 13: "King", 14: "Ace"}
        return names.get(rank, str(rank))
    
    @staticmethod
    def compare_hands(hand1: List[Card], hand2: List[Card]) -> int:
        """
        Compare two hands and determine winner.
        
        Args:
            hand1: First hand (5-7 cards)
            hand2: Second hand (5-7 cards)
            
        Returns:
            1 if hand1 wins, -1 if hand2 wins, 0 if tie
        """
        rank1, tiebreakers1, _ = HandEvaluator.evaluate_hand(hand1)
        rank2, tiebreakers2, _ = HandEvaluator.evaluate_hand(hand2)
        
        if rank1 > rank2:
            return 1
        elif rank1 < rank2:
            return -1
        else:
            # Same rank, compare tiebreakers
            if tiebreakers1 > tiebreakers2:
                return 1
            elif tiebreakers1 < tiebreakers2:
                return -1
            else:
                return 0
    
    @staticmethod
    def find_winner(players_hands: Dict[str, List[Card]]) -> List[str]:
        """
        Find winner(s) from multiple players' hands.
        
        Args:
            players_hands: Dictionary mapping player names to their 5-7 card hands
            
        Returns:
            List of winning player names (multiple if tie)
        """
        if not players_hands:
            return []
        
        evaluations = {}
        for player, hand in players_hands.items():
            rank, tiebreakers, name = HandEvaluator.evaluate_hand(hand)
            evaluations[player] = (rank, tiebreakers, name)
        
        # Find the best hand
        best_rank = max(eval[0] for eval in evaluations.values())
        best_tiebreakers = max(
            eval[1] for eval in evaluations.values() if eval[0] == best_rank
        )
        
        # Find all players with the best hand
        winners = [
            player for player, eval in evaluations.items()
            if eval[0] == best_rank and eval[1] == best_tiebreakers
        ]
        
        return winners
    
    @staticmethod
    def get_hand_strength(cards: List[Card]) -> float:
        """
        Get a numeric hand strength value (0-1) for AI/comparison purposes.
        
        Args:
            cards: Hand to evaluate
            
        Returns:
            Float between 0 and 1 representing hand strength
        """
        rank, tiebreakers, _ = HandEvaluator.evaluate_hand(cards)
        
        # Base strength from hand rank (0-9 mapped to 0.0-0.9)
        strength = rank * 0.1
        
        # Add fine-grained strength from tiebreakers (up to 0.1 more)
        if tiebreakers:
            # Normalize first tiebreaker (2-14 -> 0.0-0.08)
            strength += (tiebreakers[0] / 14.0) * 0.08
        
        return min(strength, 1.0)

