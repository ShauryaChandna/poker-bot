"""
Hand Range Module

Represents and manipulates poker hand ranges for equity calculations.
Supports heads-up specific range notation and combo generation.
"""

from typing import List, Set, Tuple, Optional
from itertools import combinations
import re
from ..engine.card import Card, Rank, Suit


class HandRange:
    """
    Represents a range of possible poker hands.
    
    Supports standard range notation:
    - Specific hands: "AA", "KK", "AKs", "AKo"
    - Ranges: "JJ+", "ATs+", "A2s+"
    - Multiple hands: "AA,KK,QQ,AKs"
    - Hand groups: "22-77", "AJs-ATs"
    """
    
    # Rank values for parsing
    RANK_VALUES = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
                   '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, 
                   '4': 4, '3': 3, '2': 2}
    
    def __init__(self, hands: Optional[Set[str]] = None):
        """
        Initialize a hand range.
        
        Args:
            hands: Set of hand strings like {"AA", "KK", "AKs"}
        """
        self.hands: Set[str] = hands or set()
    
    @classmethod
    def from_string(cls, range_string: str) -> 'HandRange':
        """
        Parse a range string into a HandRange object.
        
        Args:
            range_string: Comma-separated range notation like "AA,KK,AKs,22+"
            
        Returns:
            HandRange object containing all specified hands
            
        Examples:
            >>> HandRange.from_string("AA,KK")
            >>> HandRange.from_string("JJ+")  # All pairs JJ and higher
            >>> HandRange.from_string("ATs+")  # All suited aces from T to K
            >>> HandRange.from_string("22-77")  # All pairs from 22 to 77
        """
        hands = set()
        parts = [p.strip() for p in range_string.split(',')]
        
        for part in parts:
            if not part:
                continue
            
            # Handle specific hands with suited/offsuit (e.g., "AKs", "AKo") - check first!
            if len(part) == 3 and part[2] in ['s', 'o', 'S', 'O']:
                hands.add(part.upper())
            
            # Handle pair ranges (e.g., "JJ+", "22-77")
            elif len(part) == 3 and part[0] == part[1] and part[2] == '+':
                hands.update(cls._parse_pair_plus(part[:2]))
            elif '-' in part and len(part) == 5:
                hands.update(cls._parse_pair_range(part))
            
            # Handle suited/offsuit ranges (e.g., "ATs+", "AJo+")
            elif len(part) == 4 and part[3] == '+':
                if part[2] in ['s', 'S']:
                    hands.update(cls._parse_suited_plus(part[:2]))
                elif part[2] in ['o', 'O']:
                    hands.update(cls._parse_offsuit_plus(part[:2]))
            
            # Handle two-card notation
            elif len(part) == 2:
                # If both cards are the same, it's a pair
                if part[0] == part[1]:
                    hands.add(part.upper())
                else:
                    # If different, add both suited and offsuit
                    hands.add(part.upper() + 'S')
                    hands.add(part.upper() + 'O')
            
        return cls(hands)
    
    @classmethod
    def _parse_pair_plus(cls, pair: str) -> Set[str]:
        """Parse pair+ notation like 'JJ+' into all higher pairs."""
        rank_value = cls.RANK_VALUES[pair[0]]
        hands = set()
        for r in range(rank_value, 15):  # Up to Aces (14)
            rank_char = [k for k, v in cls.RANK_VALUES.items() if v == r][0]
            hands.add(f"{rank_char}{rank_char}")
        return hands
    
    @classmethod
    def _parse_pair_range(cls, range_str: str) -> Set[str]:
        """Parse pair range like '22-77' into all pairs in range."""
        low, high = range_str.split('-')
        low_val = cls.RANK_VALUES[low[0]]
        high_val = cls.RANK_VALUES[high[0]]
        
        hands = set()
        for r in range(low_val, high_val + 1):
            rank_char = [k for k, v in cls.RANK_VALUES.items() if v == r][0]
            hands.add(f"{rank_char}{rank_char}")
        return hands
    
    @classmethod
    def _parse_suited_plus(cls, base: str) -> Set[str]:
        """Parse suited+ notation like 'ATs+' into all suited combinations."""
        high_rank = base[0]
        low_rank = base[1]
        high_val = cls.RANK_VALUES[high_rank]
        low_val = cls.RANK_VALUES[low_rank]
        
        hands = set()
        for r in range(low_val, high_val):
            rank_char = [k for k, v in cls.RANK_VALUES.items() if v == r][0]
            hands.add(f"{high_rank}{rank_char}s")
        return hands
    
    @classmethod
    def _parse_offsuit_plus(cls, base: str) -> Set[str]:
        """Parse offsuit+ notation like 'AJo+' into all offsuit combinations."""
        high_rank = base[0]
        low_rank = base[1]
        high_val = cls.RANK_VALUES[high_rank]
        low_val = cls.RANK_VALUES[low_rank]
        
        hands = set()
        for r in range(low_val, high_val):
            rank_char = [k for k, v in cls.RANK_VALUES.items() if v == r][0]
            hands.add(f"{high_rank}{rank_char}o")
        return hands
    
    def get_combinations(self, exclude_cards: Optional[List[Card]] = None) -> List[Tuple[Card, Card]]:
        """
        Generate all possible card combinations for this range.
        
        Args:
            exclude_cards: Cards to exclude (blockers) - already dealt cards
            
        Returns:
            List of (card1, card2) tuples representing hole card combinations
            
        Example:
            >>> range = HandRange.from_string("AA,KK")
            >>> combos = range.get_combinations()
            >>> len(combos)  # 6 AA combos + 6 KK combos = 12
        """
        exclude_set = set(exclude_cards) if exclude_cards else set()
        all_combos = []
        
        for hand in self.hands:
            combos = self._hand_to_combos(hand, exclude_set)
            all_combos.extend(combos)
        
        return all_combos
    
    def _hand_to_combos(self, hand: str, exclude_set: Set[Card]) -> List[Tuple[Card, Card]]:
        """
        Convert a hand string to all possible card combinations.
        
        Args:
            hand: Hand string like "AA", "AKs", "AKo"
            exclude_set: Set of cards to exclude
            
        Returns:
            List of (card1, card2) tuples
        """
        combos = []
        
        if len(hand) == 2:  # Pair (e.g., "AA")
            rank_val = self.RANK_VALUES[hand[0]]
            for suit1, suit2 in combinations(range(4), 2):
                card1 = Card(rank_val, suit1)
                card2 = Card(rank_val, suit2)
                if card1 not in exclude_set and card2 not in exclude_set:
                    combos.append((card1, card2))
        
        elif len(hand) == 3:  # Suited or offsuit (e.g., "AKs", "AKo")
            rank1_val = self.RANK_VALUES[hand[0]]
            rank2_val = self.RANK_VALUES[hand[1]]
            suited = hand[2].upper() == 'S'
            
            if suited:
                # All 4 suits
                for suit in range(4):
                    card1 = Card(rank1_val, suit)
                    card2 = Card(rank2_val, suit)
                    if card1 not in exclude_set and card2 not in exclude_set:
                        combos.append((card1, card2))
            else:  # Offsuit
                # All combinations of different suits
                for suit1 in range(4):
                    for suit2 in range(4):
                        if suit1 != suit2:
                            card1 = Card(rank1_val, suit1)
                            card2 = Card(rank2_val, suit2)
                            if card1 not in exclude_set and card2 not in exclude_set:
                                combos.append((card1, card2))
        
        return combos
    
    def count_combinations(self, exclude_cards: Optional[List[Card]] = None) -> int:
        """
        Count total combinations in this range accounting for blockers.
        
        Args:
            exclude_cards: Cards to exclude from counting
            
        Returns:
            Total number of possible combinations
        """
        return len(self.get_combinations(exclude_cards))
    
    def __len__(self) -> int:
        """Return number of unique hands in range."""
        return len(self.hands)
    
    def __repr__(self) -> str:
        """String representation of the range."""
        return f"HandRange({', '.join(sorted(self.hands))})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return ', '.join(sorted(self.hands))


def parse_hand_to_cards(hand_str: str) -> Tuple[Card, Card]:
    """
    Parse a specific hand string to two Card objects.
    
    Args:
        hand_str: Hand string like "AhKh" or "AsKd"
        
    Returns:
        Tuple of two Card objects
        
    Example:
        >>> card1, card2 = parse_hand_to_cards("AhKh")
    """
    if len(hand_str) != 4:
        raise ValueError(f"Hand string must be 4 characters, got: {hand_str}")
    
    card1 = Card.from_string(hand_str[:2])
    card2 = Card.from_string(hand_str[2:])
    
    return card1, card2

