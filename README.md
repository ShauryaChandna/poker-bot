# PotLimitPokerBot: Heads-Up Poker AI

> 100% Custom Built Engine - Every line written from scratch, zero external poker libraries

## Project Goal

Build a modular poker AI focused on:

- Bot-vs-Human gameplay for Heads-Up Pot-Limit Hold'em
- Self-learning AI using Counterfactual Regret Minimization (CFR) and Reinforcement Learning (RL)
- Interactive web interface built with FastAPI + React for real-time play and strategy visualization

## Project Status

| Component | Status | Lines of Code | Tests |
|-----------|--------|---------------|-------|
| Core Engine (Phase 1) | Complete | ~1,500 | Pass |
| Simulation Layer (Phase 2) | Complete | ~1,000 | 69/69 Pass |
| Web Interface | Complete | ~1,500 | - |
| Opponent Modeling (Phase 3) | Complete | ~2,800 | 44/44 Pass |
| ML Range Predictor | Trained | 10k samples | 87.3% acc |
| Bot Integration (Phase 3.5) | In Progress | ~500 | TBD |
| CFR/RL Training (Phase 4) | Planned | TBD | TBD |

Phase 1-3 Complete: 5,600+ lines, 113 tests passing  
Trained Model: RandomForest (10k equity-based samples, 87.3% validation accuracy)  
Current Capabilities: Equity calculation + Opponent modeling (rule-based & ML) + HU-calibrated predictions  
Next Milestone: Integrate opponent modeling with bot for intelligent decision-making  
End Goal: Near-optimal play through CFR/RL training

Future expansions (multiplayer, rule variants) will be added after AI reaches production-stable.

---

## Gameplay Mode — Bot vs Human

### Overview
- Game Type: Heads-Up Pot-Limit Hold’em  
- Blinds: 10 / 20 (default)  
- Starting Stack: 1000 chips  
- End Condition: Game continues until one player loses all chips  
- Optional Features:
  - Adjustable blinds (constant or increasing)
  - Stack display in big blinds or chips
  - Reveal undealt cards post-hand for analysis/training

---

## AI Core

### Architecture
The AI learns through a hybrid of CFR and RL with opponent modeling and equity simulations.

- Counterfactual Regret Minimization (CFR):
  - Learns near-optimal strategy through iterative self-play  
- Reinforcement Learning (PPO / A2C):
  - Fine-tunes policy and adapts dynamically to player tendencies  
- Opponent Modeling:
  - Tracks VPIP, PFR, Fold%, Aggression Factor, and Showdown win rate  
  - Builds and updates behavioral profiles in real-time  
- Monte Carlo Simulation:
  - Fast rollouts for hand equity estimation  
  - Range-vs-range strength evaluation  

---

## System Overview

**PotLimitPokerBot Architecture**

1. Core Engine
   - Cards, deck, and dealing logic
   - Pot-limit betting and validation
   - Game state management (stacks, pot, blinds)
   - Heads-Up round flow

2. Simulation Layer
   - Monte Carlo rollouts
   - Hand equity and range evaluation
   - Self-play equity approximation

3. Intelligence Layer (AI)
   - CFR implementation
   - RL integration (PPO / A2C)
   - Self-play training loop
   - Opponent adaptation

4. Opponent Modeling
   - Player profiling (VPIP, PFR, AF)
   - Bayesian hand range inference
   - Real-time behavioral adjustments

5. Web Layer
   - FastAPI backend (game state, sockets, REST endpoints)
   - React frontend (table UI, decision visualizations)

6. Data & Persistence
   - Hand histories
   - Model checkpoints
   - Player logs
   - Experiment tracking (MLflow / W&B)

7. Deployment Layer
   - Dockerized services
   - Cloud configs (AWS / Render / GCP)
   - Monitoring & CI/CD


---

## Development Phases

| Phase | Status | Description | Bot Intelligence |
|-------|--------|-------------|------------------|
| 1. Core Engine | Complete | Deck, dealing, pot-limit logic, state management | Can play by rules |
| 2. Simulation Layer | Complete | Monte Carlo equity calculator with caching | Can calculate odds |
| 3. Opponent Modeling | Complete | Player profiling, ML range predictor (87.3% acc), HU-calibrated | Can predict ranges |
| 3.5 Bot Integration | In Progress | Integrate opponent modeling for intelligent decisions | Can think strategically |
| 4. CFR + RL Training | Planned | Self-learning AI, optimal strategy training | Plays near-optimally |
| 5. Web Interface | Complete | FastAPI + React for real-time gameplay | Playable now |
| 6. Deployment | Planned | Production deployment, monitoring, CI/CD | Scale to users |

### Current Bot Status: Check/Call Station (Exploitable)
The bot currently uses a naive strategy (`backend/app.py` lines 356-384):
- Always checks if possible
- Always calls if can't check  
- **Never raises, never bluffs**
- Doesn't consider hand strength or opponent behavior

Phase 3.5 will transform this into an intelligent player that uses equity calculations and opponent modeling.

---

## Phase 3 Complete: Opponent Modeling + ML Predictor

Built a complete opponent modeling system that tracks player behavior and predicts hand ranges using both rule-based heuristics and machine learning.

### Implementation Details

**Files Implemented:**
- `pypokerengine/opponent_modeling/player_profile.py` (280 lines)
  - Tracks VPIP, PFR, Aggression Factor, Fold-to-Cbet, 3-Bet%
  - Classifies players into archetypes (TAG, LAG, Nit, Calling Station)
  - **Heads-up calibrated** (VPIP 48-72%, PFR 25-44%)
  
- `pypokerengine/opponent_modeling/hand_history.py` (300 lines)
  - Records all actions across all streets
  - Query interface for historical analysis
  - Multi-hand lookback support
  
- `pypokerengine/opponent_modeling/range_estimator.py` (350 lines)
  - Rule-based range estimation (works immediately!)
  - Archetype-specific templates for HU play
  - Preflop and postflop range narrowing
  
- `pypokerengine/opponent_modeling/features.py` (280 lines)
  - Extracts 32+ features for ML models
  - Player stats, board texture, pot odds, SPR
  - Numpy-ready feature vectors
  
- `pypokerengine/opponent_modeling/range_predictor.py` (400 lines)
  - sklearn RandomForest model infrastructure
  - 6 range categories (ultra-tight → wide)
  - Hybrid approach (rules + ML)

**Training Pipeline:**
- `scripts/generate_training_data.py` (500 lines)
  - Uses real equity calculations (not random ranges)
  - 4 HU archetypes with equity thresholds
  - Generated 10,000 samples in ~50 minutes
  
- `scripts/train_range_model.py` (200 lines)
  - RandomForest training with evaluation
  - Feature importance analysis
  - Model serialization

**Testing:**
- `tests/opponent_modeling/` - 44 comprehensive tests (100% passing)

### Key Features

- **Player Profiling**: Track 15+ statistics per opponent
- **Range Estimation**: Both rule-based (instant) and ML (87.3% accuracy)
- **Equity-Based Training**: Ranges grounded in poker mathematics, not arbitrary rules
- **HU-Calibrated**: Tuned for heads-up play (VPIP 48-72% vs 6-max's 18-45%)
- **Fast Predictions**: < 5ms per prediction
- **Hybrid System**: Uses ML when confident (>70%), falls back to rules otherwise

### Trained Model Performance

**Model:** RandomForest with 100 trees  
**Training Data:** 10,000 equity-based samples (4 HU archetypes)  
**Accuracy:** 87.3% validation (88.1% training)  
**Size:** 3.7 MB  
**Speed:** < 5ms per prediction  

**Top Features (What the model learned):**
1. Action taken (call, bet, check, raise, fold) - 55%
2. Street (preflop, flop, turn, river) - 15%
3. Bet sizing - 7%
4. Board texture - 5%

**Range Categories Predicted:**
- Ultra-tight: QQ+,AKs
- Tight: JJ+,AQs+,AKo
- Tight-medium: TT+,ATs+,AJo+,KQs
- Medium: 99+,A9s+,ATo+,KJs+,KQo
- Medium-wide: 77+,A2s+,A9o+,KTs+,QJs+
- Wide: 55+,A2s+,A5o+,K5s+,K9o+,QTs+

### How It Works

```python
from pypokerengine.opponent_modeling import (
    PlayerProfile, RangePredictor, EquityCalculator
)

# 1. Track opponent
profile = PlayerProfile(player_id="villain")
profile.update_preflop_action(action="raise", is_raise=True)
# After 100 hands: VPIP=58%, PFR=38% → "Balanced HU player"

# 2. Predict their range
predictor = RangePredictor.load("models/range_model.pkl")
prediction = predictor.predict(profile, action="raise", street=PREFLOP)
# → Range: "JJ+,AQs+,AKo" (Confidence: 99.4%)

# 3. Calculate your equity vs their range
calc = EquityCalculator()
equity = calc.calculate_equity(
    hero_hand="AhKh",
    villain_range=prediction.to_hand_range(),
    board=board
)
# → Your AK has 45% equity vs their range

# 4. Make intelligent decision
if equity > 0.55:
    return "raise"  # Value bet
elif equity > pot_odds:
    return "call"   # Profitable
else:
    return "fold"   # Not enough equity
```

### Outcomes Achieved

- Bot can track: "Opponent has 58% VPIP, 38% PFR → Balanced HU player"  
- Bot can predict: "Given their stats + this raise → JJ+,AQs+,AKo (99% confident)"  
- Bot can calculate: "My AK has 45% equity vs their range"  
- Foundation ready for Phase 3.5 intelligent decision-making  

### Data Quality

**Training Data Characteristics:**
- 10,000 samples balanced across 4 HU archetypes
- Each sample: 32 features + equity value + range category
- Equity mean: 0.498 (realistic distribution)
- Action distribution: 34% check, 22% bet, 17% call, 15% raise, 12% fold
- All based on **real equity calculations** (not random!)

**HU Archetypes (Calibrated for 2-player poker):**
- HU Tight-Aggressive: VPIP=48%, PFR=32%, AF=3.0
- HU Balanced: VPIP=58%, PFR=38%, AF=2.5  
- HU Loose-Aggressive: VPIP=68%, PFR=44%, AF=2.8
- HU Calling Station: VPIP=72%, PFR=25%, AF=1.3

### Quick Demo

```bash
# Run comprehensive demo
python examples/opponent_modeling_demo.py

# Or test specific components
python -c "
from pypokerengine.opponent_modeling import PlayerProfile
profile = PlayerProfile('test', hands_played=100)
profile.vpip_count = 58
profile.pfr_count = 38
print(f'Archetype: {profile.get_archetype()}')
"
```

### 📁 Files Structure

```
pypokerengine/opponent_modeling/
├── __init__.py
├── player_profile.py      # Track opponent stats
├── hand_history.py        # Record action sequences
├── range_estimator.py     # Rule-based estimation
├── features.py            # ML feature engineering
└── range_predictor.py     # ML model + hybrid approach

scripts/
├── generate_training_data.py  # Equity-based data generator
└── train_range_model.py       # Model training

models/
├── range_model.pkl            # Trained HU model (primary)
└── archive/
    └── range_model_6max.pkl   # Old 6-max model (reference)

data/
├── X_train.npy               # 10,000 training samples
├── y_train.npy               # Labels
├── training_data_raw.json    # Full details (6.3 MB)
└── archive/
    └── training_data_6max.json  # Old 6-max data

tests/opponent_modeling/      # 44 tests (100% passing)
examples/opponent_modeling_demo.py  # Complete demo
```

---

## Next: Phase 3.5 - Bot Integration

Transform the bot from "check/call station" to intelligent player by integrating equity calculations + opponent modeling.

### What Needs to Be Built

### Planned Components

**Strategy Module (`strategy/equity_strategy.py`)**
```python
class EquityBasedStrategy:
    def decide_action(self, game_state, opponent_model):
        # 1. Get opponent's estimated range
        villain_range = opponent_model.estimate_range(...)
        
        # 2. Calculate our equity vs their range
        equity = equity_calc.calculate_equity(
            our_hand, 
            villain_range=villain_range,
            board=game_state.board
        )
        
        # 3. Calculate pot odds
        pot_odds = call_amount / (pot + call_amount)
        
        # 4. Make decision
        if equity > 0.70:
            return 'raise'  # Value bet
        elif equity > pot_odds + 0.10:
            return 'call'   # Profitable call
        elif random.random() < 0.15:
            return 'raise'  # Bluff
        else:
            return 'fold'   # Not enough equity
```

**Decision Logic:**
- **Raise for value**: equity > 70%
- **Call**: equity > pot odds + margin
- **Bluff**: Occasionally with medium equity (15% frequency)
- **Fold**: Insufficient equity

### Integration Checklist

**What's Ready to Use:**
- `PlayerProfile` - Track opponent stats across hands
- `HandHistory` - Record all actions
- `RangePredictor` - Trained ML model (87.3% accuracy)
- `EquityCalculator` - Fast equity vs ranges
- `HybridRangeEstimator` - Combined rules + ML

**What Needs Integration:**
- [ ] Add `PlayerProfile` tracking to `backend/app.py`
- [ ] Update opponent profiles after each action
- [ ] Replace check/call bot with equity-based strategy
- [ ] Add SQLite for persistent opponent tracking (optional)
- [ ] Integrate range prediction in decision-making
- [ ] Calculate equity vs predicted ranges
- [ ] Implement intelligent bet sizing

**Integration Points:**
1. **After opponent acts**: Update their `PlayerProfile`
2. **When bot decides**: 
   - Predict opponent range
   - Calculate equity vs range
   - Make decision based on equity + pot odds
3. **After hand ends**: Store hand history, update stats

### Expected Outcomes

After Phase 3.5:
- Bot makes +EV decisions based on equity
- Adapts to opponent tendencies (tight vs loose)
- Can value bet, bluff catch, and fold appropriately
- First truly playable intelligent bot
- Bot intelligence: 6/10 (competent player level)

---

## Upcoming: Phase 4 - CFR/RL Training

Train the bot to play near-optimally through self-play and reinforcement learning.

### Planned Approaches

**4A. Counterfactual Regret Minimization (CFR)**
- Bot plays millions of hands against itself
- At each decision point, uses equity calculator to evaluate outcomes
- Tracks regret for each action
- Converges to Nash equilibrium strategy
- Result: Unexploitable baseline strategy

**4B. Reinforcement Learning (PPO/A2C)**
- Bot learns through trial and error
- State: Hand strength, opponent stats, pot odds, equity
- Actions: Fold, call, raise (with size)
- Rewards: Chips won/lost
- Uses Phase 2 equity + Phase 3 opponent modeling as state features

**4C. Hybrid Approach**
- Start with CFR for optimal baseline
- Fine-tune with RL for opponent exploitation
- Use opponent modeling to identify weaknesses
- Adapt strategy dynamically

### Expected Outcomes

After Phase 4:
- Bot plays near-optimal poker (approaching GTO)
- Can exploit opponent mistakes when detected
- Robust against human exploitation attempts
- Bot intelligence: 9/10 (expert player level)

---

## Phase 2 Complete: Simulation Layer

The Monte Carlo simulation engine is now fully implemented with comprehensive equity calculation capabilities.

### Implementation Details

**Files Added:**
- `pypokerengine/simulation/hand_range.py` (258 lines)
  - `HandRange` class with notation parsing (`"JJ+"`, `"AKs"`, `"22-77"`)
  - Combo generation accounting for blockers
  - Support for pairs, suited, offsuit, and range notation
  
- `pypokerengine/simulation/monte_carlo.py` (369 lines)
  - `MonteCarloSimulator` for fast equity calculations
  - Hand vs hand, hand vs range, range vs range simulations
  - Deterministic seeding for reproducible tests
  
- `pypokerengine/simulation/equity_calculator.py` (402 lines)
  - `EquityCalculator` with LRU caching (76,000x speedup!)
  - `EquityResult` dataclass with confidence intervals
  - Universal API supporting multiple input formats
  
- `tests/simulation/` - 69 comprehensive tests (100% passing)
- `examples/equity_demo.py` - Full demonstration script

### Key Features

- **Hand Range Parser**: Parse and manipulate poker hand ranges (e.g., `"JJ+"`, `"AKs"`, `"22-77"`)
- **Monte Carlo Simulator**: Fast randomized simulations for equity calculation (10,000+ sims/sec)
- **Equity Calculator**: High-level API with LRU caching for performance optimization
- **Comprehensive Testing**: 69 tests with 100% pass rate validating accuracy
- **Range vs Range**: Calculate equity between complex hand ranges
- **Blocker Removal**: Automatically accounts for known cards when generating ranges

### Performance

| Metric | Performance |
|--------|-------------|
| Simulations/sec | 10,000+ |
| Cache hit speedup | 76,000x faster |
| Test coverage | 100% (69 tests) |
| Hand vs hand equity | < 1s for 10k sims |
| Cached lookups | < 0.01ms |

### Quick Demo

```python
from pypokerengine.simulation import EquityCalculator

calc = EquityCalculator(default_simulations=10000)

# Hand vs hand
result = calc.calculate_equity("AhAd", villain_hand="KsKd")
print(f"AA vs KK: {result.equity:.1%}")  # ~82%

# Hand vs range
result = calc.calculate_equity("AhAd", villain_range="JJ+,AKs")
print(f"AA vs JJ+,AKs: {result.equity:.1%}")  # ~83%

# Postflop with board
result = calc.calculate_postflop_equity(
    "AhKc", 
    villain_range="QQ,JJ", 
    board="Ac7d2s"
)
print(f"AK on Ac7d2s vs QQ,JJ: {result.equity:.1%}")  # ~90%
```

Run the full demo:
```bash
python examples/equity_demo.py
```

---

## Phase 1 & 5 Complete: Core Engine + Web UI
 
The core poker engine is fully implemented with a modern web interface for real-time gameplay.

### Implementation Details (Phase 1)

**Files Implemented:**
- `pypokerengine/engine/card.py` - Card & Deck classes with shuffling
- `pypokerengine/engine/player.py` - Player state management
- `pypokerengine/engine/hand_evaluator.py` - 7-card hand evaluation (all rankings)
- `pypokerengine/engine/action_manager.py` - Pot-limit betting validation
- `pypokerengine/engine/round.py` - Round management (preflop → river)
- `pypokerengine/engine/game.py` - Game controller with blind rotation

**Key Achievements:**
- 100% custom-built (zero external poker libraries)
- Accurate pot-limit betting calculations
- Complete hand evaluation (Royal Flush → High Card)
- Comprehensive logging system
- Clean state API for AI/UI integration

### Implementation Details (Phase 5)

**Files Implemented:**
- `backend/app.py` (529 lines) - FastAPI with WebSocket support
- `frontend/src/App.tsx` (973 lines) - React UI with TailwindCSS
- `docker-compose.yml` - Containerized deployment

**Key Features:**
- Real-time gameplay via WebSockets
- Modern poker table UI
- Live action feed and game state updates
- Responsive design for all screen sizes

### Quick Start (Web)

Run locally:

```bash
# Backend
python -m pip install -r backend/requirements.txt
uvicorn backend.app:app --reload

# Frontend (in a new terminal)
cd frontend
npm install
npm run dev

# Open http://localhost:5173
```

Run with Docker:

```bash
docker compose up --build
# Open http://localhost:5173 (backend at http://backend:8000 inside compose)
```

### Quick Start (Engine only)

The engine alone can be used from Python directly.

#### Core Components
- **Card & Deck Management**: Full 52-card deck with shuffling and dealing
- **Player State Management**: Stack tracking, betting, actions, and hand history
- **Hand Evaluator**: Complete 7-card poker hand evaluation (all rankings)
- **Pot-Limit Action Manager**: Official pot-limit betting formula and validation
- **Round Manager**: Complete betting round flow (preflop → river → showdown)
- **Game Controller**: Multi-hand game management with blind rotation

#### Features
- **Heads-Up Gameplay**: Full support for 2-player poker
- **Pot-Limit Rules**: Accurate pot-limit betting calculations
- **Complete Game Flow**: From deal to showdown with all streets
- **State API**: Clean `get_state()` for AI/UI integration
- **Logging System**: Comprehensive game event logging
- **CLI Interface**: Interactive command-line play vs AI

### Quick Start

#### Installation & Quick Start

**This engine is 100% custom-built with ZERO external dependencies!**

```bash
cd /Users/shauryachandna/pokerbot

# Set Python path
export PYTHONPATH=/Users/shauryachandna/pokerbot:$PYTHONPATH

# Run examples
python examples/interactive_cli.py       # Play vs AI!
python examples/simple_game.py          # Watch AI vs AI
python examples/hand_evaluation_demo.py # See hand rankings

# Or use the run script
./run_example.sh 1  # AI vs AI game
./run_example.sh 4  # Interactive play
```

See **docs/QUICKSTART.md** for detailed engine instructions. The full engine API is in **docs/POKER_ENGINE_DOCS.md**.

#### Use in Your Code
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

# Define your AI strategy
def my_ai_strategy(player, legal_actions, street):
    if legal_actions['check']:
        return 'check', 0
    if legal_actions['call']:
        return 'call', legal_actions['call']['amount']
    return 'fold', 0

# Play a hand
result = game.play_hand(my_ai_strategy)
print(f"Winner: {result['winners']}")
```

### Documentation

- **docs/QUICKSTART.md** - Engine quickstart
- **docs/POKER_ENGINE_DOCS.md** - Engine API reference
- **examples/** - Working code examples

### Project Structure

```
pokerbot/
├── pypokerengine/
│   └── pypokerengine/
│       ├── engine/              # Core game engine
│       │   ├── card.py          # Card and Deck classes
│       │   ├── player.py        # Player state management
│       │   ├── hand_evaluator.py # Hand ranking evaluation
│       │   ├── action_manager.py # Pot-limit action validation
│       │   ├── round.py         # Single hand/round management
│       │   └── game.py          # Main game controller
│       ├── cli/                 # Command-line interface
│       │   └── poker_cli.py     # Interactive CLI
│       └── utils/               # Utility modules
│           └── logging_config.py # Logging system
├── examples/                    # Example scripts
│   ├── simple_game.py
│   ├── interactive_cli.py
│   ├── hand_evaluation_demo.py
│   └── api_usage.py
├── requirements.txt
├── POKER_ENGINE_DOCS.md        # Full documentation
└── README.md
```

---

## Testing & Metrics

- **Unit Tests:** For all core components and AI functions  
- **Integration Tests:** Verify full game flow and decision correctness  
- **Performance Metrics:** Games/sec, exploitability, win rate vs baselines  
- **Experiment Tracking:** MLflow / Weights & Biases  

---

## Tech Stack

| Layer | Current | Planned (Phase 4+) |
|--------|---------|-------------------|
| **Core Engine** | Python 3.13, Custom-built | - |
| **Simulation** | Custom Monte Carlo (10k+ sims/sec) | NumPy optimization |
| **AI / Learning** | - | PyTorch, MCCFR, PPO/A2C |
| **Opponent Modeling** | - (Phase 3) | sklearn → PyTorch |
| **API** | FastAPI, Uvicorn, WebSockets | - |
| **Frontend** | React, TailwindCSS, Vite | - |
| **Testing** | pytest (69 tests passing) | Expand coverage |
| **Database** | In-memory (sessions) | PostgreSQL (hand histories) |
| **Deployment** | Docker Compose | Kubernetes, AWS ECS |
| **Experiment Tracking** | - | MLflow / W&B |

**Dependencies:**
- `numpy>=1.24.0` - For Monte Carlo optimizations (Phase 2)
- `scikit-learn>=1.3.0` - For ML models in opponent modeling (Phase 3)
- `fastapi` + `uvicorn` - Backend API (Phase 5)  
- `pytest` - Testing infrastructure
- Future: `torch`, `pandas` (Phase 4)

---

## Development Philosophy

- **Clean modular design:** Each layer isolated and extendable  
- **Strong typing + documentation:** Every class/function includes type hints and docstrings  
- **Test-driven development:** Reliability first, speed second  
- **Transparent AI:** Track every training step, seed, and rollout for reproducibility  

---

## End Goal (Phase 1)

Deliver a **robust, explainable poker AI** that can:
- Play **Heads-Up Pot-Limit Hold’em** against humans in real time  
- Adapt its play style dynamically based on opponent behavior  
- Provide **decision visualizations** and **strategy insights** through the web interface  

---