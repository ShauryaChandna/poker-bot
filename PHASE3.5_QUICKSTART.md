# Phase 3.5 Quick Start Guide

## What Was Built

Phase 3.5 integrated opponent modeling and equity calculations into the poker bot, transforming it from a naive "calling station" into an intelligent, equity-based decision maker.

## Files Created

```
pypokerengine/strategy/
├── __init__.py                # Module exports
├── opponent_tracker.py        # 181 lines - Tracks opponent stats
├── bet_sizing.py             # 235 lines - Dynamic bet sizing
├── equity_strategy.py        # 480 lines - Core decision logic
├── bot_strategy.py           # 276 lines - Main orchestrator
└── README.md                 # 400+ lines - Module documentation

test_bot_strategy.py          # 427 lines - Comprehensive tests
PHASE3.5_SUMMARY.md          # This file - Complete summary
PHASE3.5_QUICKSTART.md       # Quick reference guide
```

Modified:
- `backend/app.py` - Integrated BotStrategy into game loop
- `README.md` - Updated project status

## How to Use

### Play Against the Bot

```bash
# Terminal 1: Start backend
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

Visit http://localhost:5173 and play!

### Run Tests

```bash
python test_bot_strategy.py
```

Expected output:
```
✓ Preflop decisions working
✓ Postflop equity calculations (70% pot avg on strong hands)
✓ Facing bet: raises with overpair
✓ Opponent tracking operational
✓ Bluff frequency adjusts vs tight players
✓ Bet sizing randomized (58-84% pot)
```

### Check Opponent Stats

The bot tracks your statistics. After playing several hands, check backend logs:

```
Opponent Stats:
  Hands Played: 25
  VPIP: 32.0%
  PFR: 20.0%
  Aggression Factor: 2.5
  Archetype: loose_aggressive
```

## Bot Behavior

### What the Bot Does

1. **Tracks Your Actions**
   - Records every fold, check, call, raise
   - Updates VPIP, PFR, aggression factor
   - Builds your player profile

2. **Estimates Your Range**
   - Based on your action + profile
   - "This player raised → likely has JJ+, AQ+"

3. **Calculates Equity**
   - Bot's hand vs your estimated range
   - 5,000 Monte Carlo simulations

4. **Makes Decision**
   - Equity > 60% → Value bet (60-75% pot)
   - Equity > pot_odds + 8% → Call
   - Low equity → Bluff (18% frequency)
   - Otherwise → Fold

5. **Sizes Bets Dynamically**
   - Randomizes ±10% to avoid patterns
   - Adjusts for board texture
   - Larger bets on wet boards

### Example Hand

```
Scenario: Bot has A♥K♥, board is A♠K♦2♣

Bot's thought process:
1. "I have top two pair"
2. "Opponent checked → estimate range 22-JJ, AT-KJ"
3. Calculate equity → 88%
4. "88% > 60% → value bet!"
5. Bet 70 (70% of 100 pot, randomized)
```

## Tuning the Bot

### Adjust Aggression

Edit `backend/app.py` line 49-54:

```python
self.bot_strategy = BotStrategy(
    bot_name=bot_name,
    opponent_name=human_name,
    aggression_level=1.5,  # Change this: 0.5-2.0
    n_simulations=5000
)
```

- `0.5` = Passive (rarely bluffs, tight)
- `1.0` = Balanced (default)
- `1.5` = Aggressive (bluffs more, wider ranges)
- `2.0` = Very Aggressive (LAG style)

### Adjust Speed vs Accuracy

```python
n_simulations=2000  # Faster (±2% accuracy)
n_simulations=5000  # Balanced (default)
n_simulations=10000 # More accurate (±0.5%)
```

## Bot Intelligence: 6/10

### Strengths
- ✅ Solid preflop ranges (heads-up optimal)
- ✅ Accurate equity calculations
- ✅ Tracks opponent tendencies
- ✅ Exploits tight/loose players
- ✅ Randomized bet sizing
- ✅ Pot odds calculations

### Weaknesses
- ❌ Not GTO-optimal (exploitable by experts)
- ❌ Simple range estimation (rule-based)
- ❌ No multi-street planning
- ❌ Basic bluff frequency (not range-based)
- ❌ Doesn't adjust to meta-game changes

## Common Issues

### Bot Always Checks
- Likely falling back to default equity (50%)
- Check backend logs for "Equity calculation failed"
- Usually caused by range estimation issues

### Bot Too Aggressive
- Reduce aggression_level to 0.7-0.8
- Or adjust thresholds in `equity_strategy.py`

### Bot Too Passive
- Increase aggression_level to 1.3-1.5
- Or lower VALUE_BET_THRESHOLD

### Slow Decisions
- Reduce n_simulations to 2000
- Bot should act within 200ms

## Next Steps (Future Phases)

### Phase 4: GTO Baseline
- Implement CFR solver
- Pre-computed push/fold charts
- Unexploitable baseline strategy

### Phase 4.5: Advanced Features
- Multi-street planning
- Implied odds calculations
- Board texture analysis
- Range-based betting

### Phase 5: Reinforcement Learning
- Self-play training
- Adaptive strategy
- Meta-game awareness

## Architecture Summary

```
Frontend (React)
    ↓
Backend (FastAPI)
    ↓
SessionState.bot_strategy (BotStrategy)
    ↓
    ├── OpponentTracker → Profiles
    ├── EquityCalculator → Equity
    ├── BetSizer → Amounts
    └── EquityStrategy → Decisions
```

## Key Files to Understand

1. **Start Here**: `pypokerengine/strategy/README.md`
   - Complete module documentation
   - Usage examples
   - Tuning guide

2. **Implementation Details**: `PHASE3.5_SUMMARY.md`
   - 500 lines of detailed explanation
   - Design decisions
   - Performance stats

3. **Code Entry Point**: `backend/app.py`
   - Line 49: BotStrategy initialization
   - Line 170: Action recording
   - Line 416: Bot decision making

4. **Core Logic**: `pypokerengine/strategy/equity_strategy.py`
   - Lines 173-212: Equity calculation
   - Lines 210-252: Check or bet decision
   - Lines 254-322: Facing bet decision

## Testing Strategy

Run individual test functions:

```python
from test_bot_strategy import test_preflop_decisions
test_preflop_decisions()
```

Or test specific scenarios:

```python
from pypokerengine.strategy import BotStrategy
from pypokerengine.engine.card import Card
from pypokerengine.engine.round import Street

bot = BotStrategy("Bot", "Human")

# Test strong hand
hand = [Card.from_string("Ah"), Card.from_string("Ad")]
action, amount = bot.decide_action(
    hero_hand=hand,
    board=[],
    pot=30,
    current_bet=0,
    hero_current_bet=10,
    hero_stack=990,
    street=Street.PREFLOP,
    position="BTN",
    legal_actions={'bet': {'min': 20, 'max': 1000}},
    big_blind=20
)

print(f"Aces preflop: {action} {amount}")
# Expected: bet (open-raise)
```

## Resources

- **Full Documentation**: [PHASE3.5_SUMMARY.md](PHASE3.5_SUMMARY.md)
- **Module Docs**: [pypokerengine/strategy/README.md](pypokerengine/strategy/README.md)
- **Project README**: [README.md](README.md)
- **Tests**: [test_bot_strategy.py](test_bot_strategy.py)

## Questions?

The bot is fully integrated and ready to play. Start the backend and frontend, then play some hands!

The bot will:
- Track your playing style
- Calculate equity in real-time
- Make +EV decisions
- Adjust to your tendencies

Have fun! 🃏

