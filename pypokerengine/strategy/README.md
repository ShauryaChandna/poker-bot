# Strategy Module

Intelligent poker bot strategy using opponent modeling and equity calculations.

## Architecture

```
strategy/
├── opponent_tracker.py    # Tracks opponent stats (VPIP, PFR, AF)
├── bet_sizing.py         # Dynamic bet sizing with randomization
├── equity_strategy.py    # Equity-based decision making
└── bot_strategy.py       # Main orchestrator
```

## Quick Start

```python
from pypokerengine.strategy import BotStrategy
from pypokerengine.engine.card import Card
from pypokerengine.engine.round import Street

# Initialize bot
bot = BotStrategy(
    bot_name="MyBot",
    opponent_name="Opponent",
    aggression_level=1.0,  # 0.5-2.0 range
    n_simulations=5000     # Equity calculations
)

# Make a decision
hero_hand = [Card.from_string("Ah"), Card.from_string("Kd")]
board = [Card.from_string("As"), Card.from_string("Kc"), Card.from_string("2h")]

action, amount = bot.decide_action(
    hero_hand=hero_hand,
    board=board,
    pot=100,
    current_bet=50,
    hero_current_bet=0,
    hero_stack=950,
    street=Street.FLOP,
    position="BTN",
    legal_actions={...},
    big_blind=20,
    opponent_last_action="bet"
)

# Record opponent action for tracking
bot.record_action(
    player_name="Opponent",
    action="bet",
    amount=50,
    street=Street.FLOP,
    current_bet=50,
    position="BB"
)

# End hand and update profile
bot.end_hand(winner="MyBot", showdown=True)

# Get opponent stats
stats = bot.get_opponent_stats()
print(f"Opponent VPIP: {stats['vpip']:.1%}")
print(f"Opponent PFR: {stats['pfr']:.1%}")
```

## Components

### OpponentTracker

Tracks opponent statistics across hands:

- **VPIP** (Voluntarily Put $ In Pot)
- **PFR** (Pre-Flop Raise)
- **Aggression Factor** (Bets+Raises / Calls)
- **Fold to C-Bet**
- **3-Bet Percentage**
- **Showdown Stats**

Classifies opponents into archetypes:
- Tight-Aggressive (TAG)
- Loose-Aggressive (LAG)
- Tight-Passive (Nit)
- Loose-Passive (Calling Station)

### BetSizer

Dynamic bet sizing with randomization:

```python
from pypokerengine.strategy import BetSizer, BetType

sizer = BetSizer()

# Value bet
amount = sizer.get_bet_size(
    pot=100,
    stack=900,
    bet_type=BetType.VALUE,
    street="flop"
)
# Returns: ~60-75 (60-75% pot with randomization)

# Bluff
amount = sizer.get_bet_size(
    pot=100,
    stack=900,
    bet_type=BetType.BLUFF,
    street="river"
)
# Returns: ~60-80 (more on river)
```

### EquityStrategy

Core decision-making logic:

1. **Estimate opponent range** based on action + profile
2. **Calculate equity** vs range (Monte Carlo)
3. **Calculate pot odds**
4. **Decide** (value bet, call, bluff, fold)

Decision thresholds:
- `equity > 60%` → Value bet
- `equity > 53%` → Thin value bet (60% frequency)
- `equity > pot_odds + 8%` → Profitable call
- `Low equity` → Bluff (18% base, adjusts vs opponent)

### BotStrategy

High-level orchestrator that ties everything together.

## Tuning Parameters

### Aggression Level (0.5 - 2.0)

Controls overall aggression:

```python
bot = BotStrategy(
    bot_name="AggroBot",
    opponent_name="Opponent",
    aggression_level=1.5  # 50% more aggressive
)
```

- `0.5` = Passive (bluffs 9%, tight ranges)
- `1.0` = Balanced (bluffs 18%, standard)
- `1.5` = Aggressive (bluffs 27%, wider ranges)
- `2.0` = Very Aggressive (bluffs 36%, LAG)

### Equity Simulations (1000 - 10000)

Trade-off between speed and accuracy:

```python
bot = BotStrategy(
    bot_name="FastBot",
    opponent_name="Opponent",
    n_simulations=2000  # Faster decisions
)
```

- `1000` = Very fast (~20ms), ±2% accuracy
- `5000` = Balanced (~100ms), ±1% accuracy (default)
- `10000` = Accurate (~200ms), ±0.5% accuracy

### Strategy Thresholds

Modify in `equity_strategy.py`:

```python
class EquityStrategy:
    VALUE_BET_THRESHOLD = 0.60      # Bet with > 60% equity
    THIN_VALUE_THRESHOLD = 0.53     # Thin value at 53%
    CALL_THRESHOLD_BONUS = 0.08     # Call if equity > pot_odds + 8%
    BLUFF_FREQUENCY = 0.18          # Bluff 18% of time
    AGGRESSIVE_BLUFF_FREQ = 0.25    # Vs tight players
```

## Extending the Strategy

### Add New Bet Type

1. Add to `BetType` enum in `bet_sizing.py`:

```python
class BetType(Enum):
    VALUE = "value"
    BLUFF = "bluff"
    SEMI_BLUFF = "semi_bluff"  # NEW
```

2. Add sizing logic in `BetSizer._get_base_pot_fraction()`:

```python
elif bet_type == BetType.SEMI_BLUFF:
    return random.uniform(0.55, 0.70)
```

### Add New Decision Factor

Extend `EquityStrategy.decide_action()`:

```python
def decide_action(self, ...):
    # Existing logic...
    
    # Add new factor: implied odds
    implied_odds = self._calculate_implied_odds(
        hero_stack, opponent_stack, pot
    )
    
    if equity + implied_odds > pot_odds:
        return Action.CALL, current_bet
```

### Custom Opponent Model

Create custom range estimator:

```python
from pypokerengine.opponent_modeling import RuleBasedRangeEstimator

class MyCustomEstimator(RuleBasedRangeEstimator):
    def estimate_preflop_range(self, action, position, facing_raise):
        # Custom logic
        if position == "BTN" and action == "raise":
            return HandRange.from_string("22+,A2s+,K5s+,...")
        return super().estimate_preflop_range(action, position, facing_raise)
```

## Performance Tips

### 1. Reduce Simulations for Speed

```python
bot = BotStrategy(n_simulations=2000)  # 2x faster
```

### 2. Use Equity Cache

The EquityCalculator automatically caches results (LRU, 2000 entries).

### 3. Simplify Range Estimation

For very fast play, use simpler ranges:

```python
# In equity_strategy.py, modify _estimate_opponent_range()
def _estimate_opponent_range(self, ...):
    # Simple: always assume tight range
    return HandRange.from_string("JJ+,AQs+,AKo")
```

## Testing

Run comprehensive tests:

```bash
python test_bot_strategy.py
```

Test specific component:

```python
from pypokerengine.strategy import BetSizer, BetType

sizer = BetSizer(seed=42)  # Reproducible
amount = sizer.get_bet_size(100, 900, BetType.VALUE, "flop")
print(f"Bet: {amount} ({amount/100:.0%} pot)")
```

## Integration with Backend

The bot is automatically integrated in `backend/app.py`:

1. **SessionState** initializes `BotStrategy`
2. **_apply_action()** records all actions
3. **_auto_play_bots()** calls `bot.decide_action()`
4. **_maybe_finish_hand()** calls `bot.end_hand()`

No additional setup needed!

## Debugging

Enable debug output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all equity calculations and decisions are logged
```

Check opponent stats:

```python
stats = bot.get_opponent_stats()
print(stats)
# {
#   'player_id': 'Opponent',
#   'hands_played': 25,
#   'vpip': 0.32,
#   'pfr': 0.20,
#   'aggression_factor': 2.5,
#   'archetype': 'loose_aggressive'
# }
```

## Common Issues

### "Equity calculation failed"

If you see this error, the bot falls back to 50% equity assumption.

Causes:
- Invalid card format
- Range has no valid combinations (blockers removed all)

Fix: Check that Card objects are properly formatted.

### Bot too aggressive/passive

Tune aggression level:

```python
bot = BotStrategy(aggression_level=0.7)  # More passive
```

### Slow decisions

Reduce simulations:

```python
bot = BotStrategy(n_simulations=2000)  # Faster
```

## Roadmap

Future enhancements:

- [ ] Pre-computed equity tables (10x faster)
- [ ] Multi-street planning (turn/river strategy)
- [ ] ICM calculations (tournament mode)
- [ ] GTO baseline strategies
- [ ] Hand history analysis
- [ ] Exploitative learning (ML-based adaptation)

## Contributing

To add features:

1. Create new module in `pypokerengine/strategy/`
2. Add tests to `test_bot_strategy.py`
3. Update this README
4. Ensure no linter errors

## License

Same as project root.

