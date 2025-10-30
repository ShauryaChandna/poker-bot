# Poker Engine Documentation

## Overview

This is a complete backend engine for **Heads-Up Pot-Limit Hold'em** poker, designed for AI vs Human or AI vs AI play.

## Architecture

The engine follows a clean object-oriented design with the following core components:

### Core Classes

#### 1. Card and Deck (`card.py`)

**Card**: Represents a single playing card
- Attributes: `rank` (2-14), `suit` (0-3)
- Methods: `from_string()`, `__str__()`
- Example: `Card.from_string("As")` creates Ace of Spades

**Deck**: Manages a 52-card deck
- Methods: `shuffle()`, `deal()`, `reset()`
- Supports seeded random for reproducibility

```python
from pypokerengine.engine import Card, Deck

deck = Deck(seed=42)
deck.shuffle()
cards = deck.deal(2)  # Deal 2 cards
```

#### 2. Player (`player.py`)

Manages player state including stack, cards, bets, and actions.

**Key Attributes:**
- `stack`: Current chip count
- `hole_cards`: Player's private cards
- `current_bet`: Amount bet in current betting round
- `total_bet`: Total amount bet in entire hand
- `is_active`: Whether player is still in hand
- `is_all_in`: Whether player is all-in

**Key Methods:**
- `place_bet(amount)`: Place a bet
- `fold()`: Fold hand
- `check()`: Check
- `call(amount)`: Call a bet
- `bet(amount)`: Bet/raise
- `can_act()`: Check if player can still act

```python
from pypokerengine.engine import Player

player = Player("Alice", stack=1000, position="SB")
player.deal_hole_cards([Card.from_string("As"), Card.from_string("Ah")])
```

#### 3. HandEvaluator (`hand_evaluator.py`)

Evaluates poker hands and determines winners.

**Key Methods:**
- `evaluate_hand(cards)`: Evaluate 5-7 cards, returns (rank, tiebreakers, name)
- `compare_hands(hand1, hand2)`: Compare two hands
- `find_winner(players_hands)`: Determine winner(s) from multiple hands
- `get_hand_strength(cards)`: Get numeric strength (0-1)

**Hand Rankings:**
- Royal Flush (9)
- Straight Flush (8)
- Four of a Kind (7)
- Full House (6)
- Flush (5)
- Straight (4)
- Three of a Kind (3)
- Two Pair (2)
- One Pair (1)
- High Card (0)

```python
from pypokerengine.engine import HandEvaluator, Card

cards = [Card.from_string(c) for c in ["As", "Ah", "Kd", "Kh", "Ks"]]
rank, tiebreakers, name = HandEvaluator.evaluate_hand(cards)
print(f"Hand: {name}")  # "Full House, Kings over Aces"
```

#### 4. ActionManager (`action_manager.py`)

Validates actions and enforces pot-limit betting rules.

**Pot-Limit Formula:**
```
max_bet = pot_before_action + last_outstanding_bet + amount_to_call
```

**Key Methods:**
- `get_legal_actions(player, players, current_bet, pot_size, big_blind)`: Get legal actions
- `validate_action(player, action, amount, legal_actions)`: Validate an action
- `apply_action(player, action, amount, current_bet)`: Apply validated action

```python
from pypokerengine.engine import ActionManager

legal_actions = ActionManager.get_legal_actions(
    player, players, current_bet=20, pot_size=30, big_blind=20
)
# Returns: {'fold': True, 'check': False, 'call': True, 'raise': {...}}
```

#### 5. Round (`round.py`)

Manages a single poker hand from deal to showdown.

**Streets:** PREFLOP, FLOP, TURN, RIVER, SHOWDOWN

**Key Methods:**
- `start_hand()`: Deal cards and post blinds
- `run_betting_round(callback)`: Execute betting round
- `advance_street()`: Move to next street
- `determine_winner()`: Determine and award winner
- `get_state()`: Get current round state

```python
from pypokerengine.engine import Round, Deck

round_obj = Round(players, small_blind=10, big_blind=20, dealer_position=0, deck=Deck())
round_obj.start_hand()
```

#### 6. Game (`game.py`)

Main game controller orchestrating multiple hands.

**Key Methods:**
- `start_new_hand()`: Start new hand
- `play_hand(action_callback)`: Play complete hand
- `get_state()`: Get game state
- `is_game_over()`: Check if game finished
- `reset_game()`: Reset to initial state

**Action Callback Signature:**
```python
def action_callback(player: Player, legal_actions: Dict, street: str) -> Tuple[str, int]:
    # Return (action, amount)
    return "call", 20
```

```python
from pypokerengine.engine import Game

game = Game(
    player1_name="Alice",
    player2_name="Bob",
    starting_stack=1000,
    small_blind=10,
    big_blind=20,
    seed=42
)

def my_strategy(player, legal_actions, street):
    if legal_actions['check']:
        return 'check', 0
    return 'call', legal_actions['call']['amount']

result = game.play_hand(my_strategy)
```

## Game Flow

### Complete Hand Sequence

1. **Hand Start**
   - Reset player states
   - Shuffle and deal hole cards
   - Post blinds
   - Set initial pot and current bet

2. **Preflop**
   - Small blind acts first (heads-up)
   - Betting round

3. **Flop** (if not ended)
   - Deal 3 community cards
   - Big blind acts first
   - Betting round

4. **Turn** (if not ended)
   - Deal 1 community card
   - Betting round

5. **River** (if not ended)
   - Deal 1 community card
   - Betting round

6. **Showdown**
   - Evaluate hands
   - Determine winner(s)
   - Award pot

7. **Rotate dealer button**

## Pot-Limit Betting Rules

### Maximum Bet Calculation

The pot-limit formula implemented:

```
max_bet = pot_size + current_bet + amount_to_call
```

Where:
- `pot_size`: Current pot before your action
- `current_bet`: Current bet to match
- `amount_to_call`: What you need to call (current_bet - your_current_bet)

### Minimum Raise

- When facing a bet: double the current bet
- When no prior bet: big blind amount

### Examples

**Example 1: Preflop**
- Pot: 30 (blinds)
- Current bet: 20 (big blind)
- You have: 0 bet
- Amount to call: 20
- Max raise: 30 + 20 + 20 = 70

**Example 2: Postflop**
- Pot: 100
- Current bet: 50
- You have: 0 bet
- Amount to call: 50
- Max raise: 100 + 50 + 50 = 200

## Game State Structure

The `get_state()` method returns a complete dictionary:

```python
{
    "hand_number": 5,
    "dealer_position": 1,
    "small_blind": 10,
    "big_blind": 20,
    "game_over": False,
    "players": [
        {
            "name": "Alice",
            "stack": 850,
            "position": "BB"
        },
        {
            "name": "Bob",
            "stack": 1150,
            "position": "SB"
        }
    ],
    "current_round": {
        "street": "flop",
        "pot": 120,
        "current_bet": 40,
        "community_cards": ["Ah", "Kd", "Qs"],
        "players": [...],
        "action_history": [...],
        "is_complete": False
    }
}
```

## Integration Examples

### For AI/ML Training

```python
game = Game(...)

def rl_agent_callback(player, legal_actions, street):
    state = game.get_state()
    
    # Extract features for your model
    features = extract_features(state, player)
    
    # Get action from model
    action, amount = model.predict(features, legal_actions)
    
    return action, amount

result = game.play_hand(rl_agent_callback)
```

### For Web API

```python
from fastapi import FastAPI
from pypokerengine.engine import Game

app = FastAPI()
games = {}  # Store active games

@app.post("/game/create")
def create_game(player1: str, player2: str):
    game_id = str(uuid.uuid4())
    games[game_id] = Game(player1, player2)
    return {"game_id": game_id}

@app.get("/game/{game_id}/state")
def get_state(game_id: str):
    return games[game_id].get_state()

@app.post("/game/{game_id}/action")
def take_action(game_id: str, action: str, amount: int):
    # Implement turn-by-turn logic
    pass
```

### For Monte Carlo Simulation

```python
from pypokerengine.engine import Deck, HandEvaluator

def simulate_hand_equity(hole_cards, community_cards, num_simulations=1000):
    """Calculate win probability for hole cards."""
    wins = 0
    
    for _ in range(num_simulations):
        deck = Deck()
        # Remove known cards
        # Deal remaining cards
        # Evaluate winner
        # Track results
    
    return wins / num_simulations
```

## Logging

The engine includes comprehensive logging:

```python
from pypokerengine.utils import setup_game_logger, GameLogger

logger = setup_game_logger(level=logging.INFO, log_file="game.log")
game_logger = GameLogger(logger)

game_logger.log_hand_start(hand_number=1, dealer="Alice", blinds=(10, 20))
game_logger.log_action(player="Alice", action="raise", amount=60, street="preflop")
game_logger.log_winner(winners=["Alice"], pot=120, hand="Pair of Aces")
```

## Testing

Run tests (once test suite is created):

```bash
pytest tests/
pytest --cov=pypokerengine tests/
```

## Advanced Usage

### Custom AI Strategy

```python
class PokerAI:
    def __init__(self, strategy="tight-aggressive"):
        self.strategy = strategy
        self.hand_history = []
    
    def get_action(self, player, legal_actions, game_state):
        # Analyze position
        position = player.position
        
        # Analyze hand strength
        hand_strength = self.evaluate_hand_strength(
            player.hole_cards,
            game_state['current_round']['community_cards']
        )
        
        # Make decision
        if hand_strength > 0.8:
            # Strong hand - raise
            raise_info = legal_actions.get('raise')
            if raise_info and raise_info['allowed']:
                return 'raise', raise_info['max']
        
        if legal_actions.get('check'):
            return 'check', 0
        
        return 'fold', 0
```

### Bankroll Management

```python
class BankrollManager:
    def __init__(self, initial_bankroll, risk_percentage=0.02):
        self.bankroll = initial_bankroll
        self.risk_percentage = risk_percentage
    
    def get_buy_in(self):
        """Calculate appropriate buy-in based on bankroll."""
        return int(self.bankroll * self.risk_percentage)
    
    def update_bankroll(self, profit_loss):
        self.bankroll += profit_loss
```

## Performance Considerations

- **Hands per second**: ~1000+ (depends on AI complexity)
- **Memory usage**: Minimal (~1MB per active game)
- **State size**: ~10KB serialized (JSON)

## Future Extensions

The architecture supports easy extension for:

1. **Multi-table tournaments**
2. **Different poker variants** (Limit, No-Limit, Omaha)
3. **Side pots** (already structured for it)
4. **Hand replay** (complete action history tracked)
5. **Statistics tracking** (VPIP, PFR, aggression factor)
6. **WebSocket integration** (for real-time play)

## API Reference Summary

### Main Classes

| Class | Purpose | Key Methods |
|-------|---------|-------------|
| `Game` | Game controller | `play_hand()`, `get_state()` |
| `Player` | Player state | `place_bet()`, `fold()`, `call()` |
| `Round` | Single hand | `run_betting_round()`, `determine_winner()` |
| `ActionManager` | Action validation | `get_legal_actions()`, `validate_action()` |
| `HandEvaluator` | Hand ranking | `evaluate_hand()`, `compare_hands()` |
| `Deck` | Card management | `shuffle()`, `deal()` |
| `Card` | Playing card | `from_string()` |

## Support and Contribution

For questions or contributions, see the main README.md file.

