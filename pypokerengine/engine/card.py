"""
Card and Deck Management

This module provides Card and Deck classes for poker game management.
"""

import random
from typing import List, Optional
from enum import IntEnum


class Suit(IntEnum):
    """Card suits with ordinal values."""
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3


class Rank(IntEnum):
    """Card ranks with ordinal values (2=2, ..., A=14)."""
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Card:
    """
    Represents a single playing card.
    
    Attributes:
        rank (Rank): The rank of the card (2-14, where 14 is Ace)
        suit (Suit): The suit of the card (0-3)
    """
    
    RANK_SYMBOLS = {
        2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8',
        9: '9', 10: 'T', 11: 'J', 12: 'Q', 13: 'K', 14: 'A'
    }
    
    SUIT_SYMBOLS = {
        Suit.CLUBS: '♣',
        Suit.DIAMONDS: '♦',
        Suit.HEARTS: '♥',
        Suit.SPADES: '♠'
    }
    
    def __init__(self, rank: int, suit: int):
        """
        Initialize a card.
        
        Args:
            rank: Card rank (2-14, where 14 is Ace)
            suit: Card suit (0-3)
        """
        self.rank = rank
        self.suit = suit
    
    def __str__(self) -> str:
        """Return string representation like 'A♠' or 'K♥'."""
        return f"{self.RANK_SYMBOLS[self.rank]}{self.SUIT_SYMBOLS[self.suit]}"
    
    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"Card({self.rank}, {self.suit})"
    
    def __eq__(self, other) -> bool:
        """Check equality based on rank and suit."""
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self) -> int:
        """Hash based on rank and suit."""
        return hash((self.rank, self.suit))
    
    @classmethod
    def from_string(cls, card_str: str) -> 'Card':
        """
        Create a card from string representation like 'AS' or 'Kh'.
        
        Args:
            card_str: String like 'AS', 'Kh', 'Td', '2c'
            
        Returns:
            Card instance
        """
        if len(card_str) != 2:
            raise ValueError(f"Invalid card string: {card_str}")
        
        rank_char, suit_char = card_str[0].upper(), card_str[1].lower()
        
        # Parse rank
        rank_map = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
                    '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        if rank_char not in rank_map:
            raise ValueError(f"Invalid rank: {rank_char}")
        rank = rank_map[rank_char]
        
        # Parse suit
        suit_map = {'c': Suit.CLUBS, 'd': Suit.DIAMONDS, 'h': Suit.HEARTS, 's': Suit.SPADES}
        if suit_char not in suit_map:
            raise ValueError(f"Invalid suit: {suit_char}")
        suit = suit_map[suit_char]
        
        return cls(rank, suit)


class Deck:
    """
    Represents a standard 52-card deck.
    
    Supports shuffling, dealing, and resetting.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize a deck with all 52 cards.
        
        Args:
            seed: Optional random seed for reproducible shuffling
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        self.cards: List[Card] = []
        self.dealt_cards: List[Card] = []
        self.reset()
    
    def reset(self):
        """Reset the deck to contain all 52 cards in order."""
        self.cards = [
            Card(rank, suit)
            for suit in range(4)
            for rank in range(2, 15)
        ]
        self.dealt_cards = []
    
    def shuffle(self):
        """Shuffle the deck randomly."""
        random.shuffle(self.cards)
    
    def deal(self, num_cards: int = 1) -> List[Card]:
        """
        Deal a specified number of cards from the top of the deck.
        
        Args:
            num_cards: Number of cards to deal
            
        Returns:
            List of dealt cards
            
        Raises:
            ValueError: If not enough cards remain in deck
        """
        if num_cards > len(self.cards):
            raise ValueError(f"Cannot deal {num_cards} cards, only {len(self.cards)} remain")
        
        dealt = self.cards[:num_cards]
        self.cards = self.cards[num_cards:]
        self.dealt_cards.extend(dealt)
        return dealt
    
    def deal_one(self) -> Card:
        """
        Deal a single card from the top of the deck.
        
        Returns:
            The dealt card
        """
        return self.deal(1)[0]
    
    def cards_remaining(self) -> int:
        """Return the number of cards remaining in the deck."""
        return len(self.cards)
    
    def __len__(self) -> int:
        """Return the number of cards remaining in the deck."""
        return len(self.cards)
    
    def __str__(self) -> str:
        """Return string representation showing number of cards."""
        return f"Deck({len(self.cards)} cards remaining)"

