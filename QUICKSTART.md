# Quick Start Guide

## 🎯 100% Custom Built - No External Dependencies

This poker engine is **completely built from scratch** using only Python standard library. Every line of code is custom - no external poker libraries used!

## Installation & Running

### Option 1: Quick Run (Recommended)

```bash
cd /Users/shauryachandna/pokerbot

# Set Python path
export PYTHONPATH=/Users/shauryachandna/pokerbot:$PYTHONPATH

# Run examples directly
python examples/simple_game.py           # Watch AI vs AI
python examples/hand_evaluation_demo.py  # See hand rankings
python examples/interactive_cli.py       # Play vs AI!
```

### Option 2: Use the Run Script

```bash
chmod +x run_example.sh
./run_example.sh 1  # AI vs AI game
./run_example.sh 2  # Hand evaluation demo  
./run_example.sh 3  # API usage examples
./run_example.sh 4  # Interactive play
```

### Option 3: Install as Package (Optional)

```bash
pip install -e .
# Then you can import from anywhere:
# from pypokerengine.engine import Game
```

## Simple Usage Example

```python
from pypokerengine.engine import Game

# Create game
game = Game(
    player1_name="Alice",
    player2_name="Bob",
    starting_stack=1000,
    small_blind=10,
    big_blind=20
)

# Define AI strategy
def simple_ai(player, legal_actions, street):
    if legal_actions['check']:
        return 'check', 0
    if legal_actions['call']:
        return 'call', legal_actions['call']['amount']  
    return 'fold', 0

# Play a hand
result = game.play_hand(simple_ai)
print(f"Winner: {result['winners']}")
print(f"Pot: {result['pot']}")
```

## What's Included

All custom-built modules:

- **Card & Deck** (`card.py`) - Full 52-card deck management
- **Player** (`player.py`) - Stack, betting, action tracking
- **Hand Evaluator** (`hand_evaluator.py`) - Complete 7-card evaluation
- **Action Manager** (`action_manager.py`) - Pot-limit betting validation
- **Round** (`round.py`) - Betting round flow
- **Game** (`game.py`) - Multi-hand game controller
- **CLI** (`poker_cli.py`) - Interactive interface

## Core Features

✅ **Pot-Limit Hold'em Rules**
- Official pot-limit betting formula
- Min/max raise calculations
- All-in handling

✅ **Complete Game Flow**
- Preflop → Flop → Turn → River → Showdown
- Automatic blind rotation
- Hand history tracking

✅ **Hand Evaluation**
- All 10 poker hand rankings
- 7-card best-hand selection
- Tiebreaker logic

✅ **Clean API**
- `get_state()` for AI/UI integration
- Simple action callbacks
- Comprehensive logging

## Next Steps

1. **Play interactively:** `python examples/interactive_cli.py`
2. **Read the docs:** `POKER_ENGINE_DOCS.md`
3. **Build your AI:** Use the API examples
4. **Integrate with web:** See FastAPI integration patterns

## Dependencies

**Core Engine:** NONE - Pure Python only!

**Optional (for development):**
- pytest (testing)
- black (formatting)
- mypy (type checking)

## Need Help?

- Full documentation: `POKER_ENGINE_DOCS.md`
- Example scripts: `examples/` directory
- Code comments: Every class/function documented

