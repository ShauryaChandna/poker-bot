"""
Logging Configuration for Poker Engine

This module provides centralized logging configuration.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging for the poker engine.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        format_string: Optional custom format string
    
    Returns:
        Configured root logger
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger


def setup_game_logger(
    name: str = "PokerGame",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup a logger specifically for game events.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional file path to write logs to
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Game-specific format
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


class GameLogger:
    """
    Specialized logger for poker game events with structured logging.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize game logger.
        
        Args:
            logger: Optional logger instance (creates new one if None)
        """
        self.logger = logger or setup_game_logger()
    
    def log_hand_start(self, hand_number: int, dealer: str, blinds: tuple):
        """Log the start of a new hand."""
        self.logger.info(f"=" * 60)
        self.logger.info(f"HAND #{hand_number} - Dealer: {dealer}")
        self.logger.info(f"Blinds: {blinds[0]}/{blinds[1]}")
        self.logger.info(f"=" * 60)
    
    def log_action(self, player: str, action: str, amount: int, street: str):
        """Log a player action."""
        if action == "fold":
            msg = f"{player} folds"
        elif action == "check":
            msg = f"{player} checks"
        elif action == "call":
            msg = f"{player} calls {amount}"
        elif action in ["raise", "bet"]:
            msg = f"{player} raises to {amount}"
        elif action in ["small_blind", "big_blind"]:
            msg = f"{player} posts {action.replace('_', ' ')} {amount}"
        else:
            msg = f"{player} {action} {amount}"
        
        self.logger.info(f"[{street.upper()}] {msg}")
    
    def log_street(self, street: str, board: list):
        """Log the start of a new street."""
        self.logger.info("")
        self.logger.info(f"*** {street.upper()} *** {' '.join(str(c) for c in board)}")
    
    def log_showdown(self, players_hands: dict):
        """Log showdown results."""
        self.logger.info("")
        self.logger.info("*** SHOWDOWN ***")
        for player, hand_info in players_hands.items():
            cards = ' '.join(str(c) for c in hand_info.get('cards', []))
            hand_name = hand_info.get('hand_name', '')
            self.logger.info(f"{player}: {cards} - {hand_name}")
    
    def log_winner(self, winners: list, pot: int, hand: str):
        """Log hand winner."""
        self.logger.info("")
        winner_str = " and ".join(winners)
        self.logger.info(f"{winner_str} wins {pot} chips with {hand}")
    
    def log_game_over(self, winner: str, final_stack: int, hands_played: int):
        """Log game completion."""
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info("GAME OVER")
        self.logger.info(f"{winner} wins with {final_stack} chips!")
        self.logger.info(f"Total hands played: {hands_played}")
        self.logger.info("=" * 60)

