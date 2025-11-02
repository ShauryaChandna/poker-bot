from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

import sys
import os

# Add project root to path to import engine
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(ROOT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pypokerengine.engine import Game
from pypokerengine.engine.player import Player
from pypokerengine.engine.action_manager import ActionManager
from pypokerengine.engine.round import Street


class StartGameRequest(BaseModel):
    player_name: str = "You"
    bot_name: str = "Computer"
    starting_stack: int = 1000
    small_blind: int = 10
    big_blind: int = 20


class PlayerActionRequest(BaseModel):
    session_id: str
    action: str
    amount: int = 0


class NextHandRequest(BaseModel):
    session_id: str


class SessionState:
    def __init__(self, game: Game, human_name: str, bot_name: str):
        self.game = game
        self.awaiting_player: Optional[str] = None  # name
        self.human_name = human_name
        self.bot_name = bot_name
        self.action_log = []  # list[str]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # Allow any dev origin (handles localhost, 127.0.0.1, LAN IPs, etc.)
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSIONS: Dict[str, SessionState] = {}


def _acting_order(round_obj) -> list:
    if round_obj.street == Street.PREFLOP:
        return [round_obj.dealer_position, 1 - round_obj.dealer_position]
    return [1 - round_obj.dealer_position, round_obj.dealer_position]


def _acted_names_nonblind(round_obj) -> set:
    """Return set of player names who have taken a non-blind action on this street."""
    actions_this_street = round_obj.street_actions.get(round_obj.street, [])
    return set(
        a["player"]
        for a in actions_this_street
        if a.get("action") not in ("small_blind", "big_blind")
    )


def _find_next_to_act(round_obj) -> Optional[Player]:
    players = round_obj.players
    current_bet = round_obj.current_bet
    acting_order = _acting_order(round_obj)

    # Get active players (including all-in players who are still active)
    active_players = [p for p in players if p.is_active]
    if len(active_players) <= 1:
        return None

    # Get players who can still act (not all-in)
    can_act_players = [p for p in active_players if p.can_act()]
    
    # Track who has acted this street (exclude blinds)
    acted_names = _acted_names_nonblind(round_obj)

    # If there are no players who can act (all all-in), check if bets need to be matched
    if not can_act_players:
        # All players are all-in - no one can act anymore
        return None

    # Iterate acting order to find someone who needs to act
    for pos in acting_order:
        p = players[pos]
        # Skip if not active
        if not p.is_active:
            continue
        # Skip all-in players (they can't act, but check if others need to match their bet)
        if not p.can_act():
            continue
        if current_bet == 0:
            # No outstanding bet: player acts if they haven't acted yet this street
            if p.name not in acted_names:
                return p
        else:
            # There is a bet; act if not matched OR if they haven't acted yet (e.g., BB option preflop)
            if p.current_bet < current_bet:
                return p
            if p.name not in acted_names:
                return p
    
    # If no one can act but there's a bet and someone hasn't matched it, 
    # check if an all-in player raised and the other player needs to match
    if current_bet > 0 and len(can_act_players) == 0:
        # All players are all-in, no one can act
        return None
    
    return None


def _legal_actions_for(round_obj, player: Player) -> Dict[str, Any]:
    return ActionManager.get_legal_actions(
        player,
        round_obj.players,
        round_obj.current_bet,
        round_obj.pot,
        round_obj.big_blind,
    )


def _apply_action(round_obj, player: Player, action: str, amount: int, session: Optional[SessionState] = None) -> None:
    legal = _legal_actions_for(round_obj, player)
    ok, err = ActionManager.validate_action(player, action, amount, legal)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Invalid action: {err}")
    added = ActionManager.apply_action(player, action, amount, round_obj.current_bet)
    round_obj.pot += added
    if action.lower() in ["raise", "bet"]:
        round_obj.current_bet = amount
    # Record action into round history so turn logic can see who acted
    try:
        round_obj._record_action(player.name, action, amount)  # type: ignore[attr-defined]
    except Exception:
        # Fallback: append minimal record
        round_obj.action_history.append({"player": player.name, "action": action, "amount": amount, "street": round_obj.street.value})
        round_obj.street_actions.setdefault(round_obj.street, []).append({"player": player.name, "action": action, "amount": amount, "street": round_obj.street.value})
    # Log action
    if session is not None:
        desc = ActionManager.get_action_description(action, amount, player.name)
        session.action_log.append(desc)


def _maybe_advance(round_obj, session: Optional[SessionState] = None):
    # Advance street if betting round appears complete
    active_players = [p for p in round_obj.players if p.is_active]
    if len(active_players) <= 1:
        return
    can_act = [p for p in active_players if p.can_act()]
    
    # If no one can act (all-in situation), deal remaining cards and go to showdown
    if not can_act:
        # All players are all-in - deal remaining community cards if needed, then go to showdown
        while round_obj.street != Street.SHOWDOWN and round_obj.street != Street.RIVER:
            round_obj.advance_street()
            if session is not None:
                if round_obj.street == Street.FLOP and round_obj.community_cards:
                    board = " ".join(str(c) for c in round_obj.community_cards)
                    session.action_log.append(f"Flop dealt: {board}")
                elif round_obj.street == Street.TURN and round_obj.community_cards:
                    session.action_log.append(f"Turn dealt: {str(round_obj.community_cards[-1])}")
        
        # If we're at river and all-in, go to showdown
        if round_obj.street == Street.RIVER:
            round_obj.advance_street()
            if session is not None and round_obj.community_cards:
                session.action_log.append(f"River dealt: {str(round_obj.community_cards[-1])}")
        return
    
    # All players must have acted at least once this street (excluding blinds) AND bets must be equal
    acted_names = _acted_names_nonblind(round_obj)
    all_acted_once = all(p.name in acted_names for p in can_act)
    bets_equal = len(set(p.current_bet for p in can_act)) == 1
    
    # Also check if bets are equal across ALL active players (including all-ins)
    all_bets_equal = len(set(p.current_bet for p in active_players)) == 1
    
    if all_acted_once and bets_equal and all_bets_equal:
        # Check if all players are all-in - if so, deal remaining cards and go to showdown
        all_all_in = all(not p.can_act() for p in active_players)
        if all_all_in:
            # Deal remaining cards up to river, then go to showdown
            while round_obj.street != Street.SHOWDOWN:
                prev_street = round_obj.street
                round_obj.advance_street()
                if session is not None:
                    if round_obj.street == Street.FLOP and round_obj.community_cards:
                        board = " ".join(str(c) for c in round_obj.community_cards)
                        session.action_log.append(f"Flop dealt: {board}")
                    elif round_obj.street == Street.TURN and round_obj.community_cards:
                        session.action_log.append(f"Turn dealt: {str(round_obj.community_cards[-1])}")
                    elif round_obj.street == Street.RIVER and round_obj.community_cards:
                        session.action_log.append(f"River dealt: {str(round_obj.community_cards[-1])}")
                    elif round_obj.street == Street.SHOWDOWN:
                        if prev_street == Street.RIVER:
                            session.action_log.append("All-in: Going to showdown")
                if round_obj.street == Street.SHOWDOWN:
                    break
        else:
            # Normal advance to next street
            round_obj.advance_street()
            if session is not None:
                if round_obj.street == Street.FLOP and round_obj.community_cards:
                    board = " ".join(str(c) for c in round_obj.community_cards)
                    session.action_log.append(f"Flop dealt: {board}")
                elif round_obj.street == Street.TURN and round_obj.community_cards:
                    session.action_log.append(f"Turn dealt: {str(round_obj.community_cards[-1])}")
                elif round_obj.street == Street.RIVER and round_obj.community_cards:
                    session.action_log.append(f"River dealt: {str(round_obj.community_cards[-1])}")


def _maybe_finish_hand(session: SessionState):
    game = session.game
    round_obj = game.current_round
    if not round_obj:
        return
    
    # Check if only one player is active (fold case)
    active_players = [p for p in round_obj.players if p.is_active]
    if len(active_players) == 1 and not round_obj.is_complete:
        # Someone folded - determine winner immediately
        round_obj.street = Street.SHOWDOWN
        result = round_obj.determine_winner()
        winners = ", ".join(result.get("winners", []))
        session.action_log.append(f"{winners} wins — {result.get('winning_hand', 'opponent folded')}; Pot: {result.get('pot')}")
    
    # Handle showdown case
    if round_obj.street == Street.SHOWDOWN and not round_obj.is_complete:
        # Determine winners and award pot
        result = round_obj.determine_winner()
        winners = ", ".join(result.get("winners", []))
        session.action_log.append(f"Showdown — Winner(s): {winners}; Pot: {result.get('pot')}")


def _state_dict(session: SessionState) -> Dict[str, Any]:
    game = session.game
    round_obj = game.current_round
    # Compute current actor live to avoid stale session flag
    awaiting = None
    if round_obj:
        next_actor = _find_next_to_act(round_obj)
        awaiting = next_actor.name if next_actor else None
    state = {
        "hand_number": game.hand_number,
        "dealer_position": game.dealer_position,
        "dealer_name": game.players[game.dealer_position].name,
        "street": round_obj.street.value if round_obj else None,
        "pot": round_obj.pot if round_obj else 0,
        "current_bet": round_obj.current_bet if round_obj else 0,
        "community_cards": [str(c) for c in (round_obj.community_cards if round_obj else [])],
        "players": [p.to_dict() for p in game.players],
        "awaiting_player": awaiting,
        "is_complete": round_obj.is_complete if round_obj else False,
        "action_log": session.action_log,
        "big_blind": round_obj.big_blind if round_obj else game.big_blind,
    }
    # Include legal actions for the human when it's their turn
    if round_obj and awaiting == session.human_name:
        # Find the human player object
        human = next((p for p in game.players if p.name == session.human_name), None)
        if human is not None:
            state["legal_actions"] = _legal_actions_for(round_obj, human)
    if round_obj and round_obj.is_complete:
        state["winners"] = getattr(round_obj, "winners", [])
        state["winning_hand"] = getattr(round_obj, "winning_hand", "")
        # Build simple hands dict for UI (names and hole cards only)
        state["hands"] = {p.name: {"hole_cards": [str(c) for c in p.hole_cards]} for p in round_obj.players}
    return state


def _auto_play_bots(session: SessionState):
    game = session.game
    round_obj = game.current_round
    if not round_obj:
        return
    while True:
        actor = _find_next_to_act(round_obj)
        if not actor:
            # No one needs to act - advance/finish
            _maybe_advance(round_obj, session)
            _maybe_finish_hand(session)
            actor = _find_next_to_act(round_obj)
            if not actor:
                # Hand is complete or no one can act
                break
        # Stop if it's human turn
        if actor.name == session.human_name:
            break
        # Bot acts with simple policy
        amount_to_call = round_obj.current_bet - actor.current_bet
        
        # Handle forced all-in FIRST: if bot can't match bet but has chips, call with all chips
        if amount_to_call > 0 and actor.stack < amount_to_call and actor.stack > 0 and actor.can_act():
            # Forced all-in: call with remaining chips (player.call will handle this)
            # We need to call with the full current_bet amount, player.call will handle going all-in
            _apply_action(round_obj, actor, "call", round_obj.current_bet, session)
            print(f"Bot {actor.name} forced all-in: called {round_obj.current_bet} with stack {actor.stack}")
        else:
            # Normal action logic
            legal = _legal_actions_for(round_obj, actor)
            print(f"Bot {actor.name} acting: legal={legal}, street={round_obj.street.value}, current_bet={round_obj.current_bet}, actor.current_bet={actor.current_bet}, stack={actor.stack}")
            
            if legal.get("check"):
                _apply_action(round_obj, actor, "check", 0, session)
                print(f"Bot {actor.name} checked")
            elif legal.get("call"):
                _apply_action(round_obj, actor, "call", round_obj.current_bet, session)
                print(f"Bot {actor.name} called {round_obj.current_bet}")
            else:
                # If fold is the only option, but player can still act (has chips), 
                # and there's a bet they can't match, they should go all-in instead of folding
                if amount_to_call > 0 and actor.stack > 0 and actor.can_act():
                    # Forced all-in instead of folding
                    _apply_action(round_obj, actor, "call", round_obj.current_bet, session)
                    print(f"Bot {actor.name} forced all-in instead of folding: called {round_obj.current_bet} with stack {actor.stack}")
                else:
                    _apply_action(round_obj, actor, "fold", 0, session)
                    print(f"Bot {actor.name} folded")
        # After bot action, check if hand finished or if we need to advance
        _maybe_finish_hand(session)
        if round_obj.is_complete:
            break
        # Check if betting round is complete after bot action
        next_actor = _find_next_to_act(round_obj)
        if not next_actor:
            # Betting round complete - advance/finish
            _maybe_advance(round_obj, session)
            _maybe_finish_hand(session)
            if round_obj.is_complete:
                break
            # Check again after advancing
            next_actor = _find_next_to_act(round_obj)
            if not next_actor:
                # No one needs to act
                break
            # If it's now human's turn, stop
            if next_actor.name == session.human_name:
                break
        elif next_actor.name == session.human_name:
            # Bot acted, now it's human's turn
            break
        # Otherwise, loop continues for another bot action if needed


@app.post("/start_game")
def start_game(req: StartGameRequest) -> Dict[str, Any]:
    game = Game(
        req.player_name,
        req.bot_name,
        req.starting_stack,
        req.small_blind,
        req.big_blind,
        seed=None,
    )
    game.start_new_hand()
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = SessionState(game, req.player_name, req.bot_name)
    # Initial log
    SESSIONS[session_id].action_log.append(f"Hand #{game.hand_number} started. Dealer: {game.players[game.dealer_position].name}")
    # Don't auto-play bots here - let the frontend timer control bot actions
    # Check who should act first and set awaiting_player accordingly
    round_obj = game.current_round
    if round_obj:
        next_actor = _find_next_to_act(round_obj)
        if next_actor and next_actor.name != req.player_name:
            # Bot acts first - frontend will handle the timer
            pass
    return {"session_id": session_id, "state": _state_dict(SESSIONS[session_id])}


@app.get("/state")
def get_state(session_id: str) -> Dict[str, Any]:
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _state_dict(session)


@app.post("/player_action")
def player_action(req: PlayerActionRequest) -> Dict[str, Any]:
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    game = session.game
    round_obj = game.current_round
    if not round_obj:
        raise HTTPException(status_code=400, detail="No active hand")
    player_to_act = _find_next_to_act(round_obj)
    # Only allow action when it's human's turn
    if not player_to_act or player_to_act.name != session.human_name:
        raise HTTPException(status_code=400, detail="Not waiting for player action")
    _apply_action(round_obj, player_to_act, req.action, req.amount, session)
    # Check if fold ended the hand immediately
    _maybe_finish_hand(session)
    # After action, check if there's a next actor
    # IMPORTANT: Only advance if NO ONE needs to act (not even the bot)
    # If bot needs to act, return state with awaiting_player set to bot name
    next_actor = _find_next_to_act(round_obj)
    
    if not next_actor:
        # No one needs to act - betting round is complete, advance/finish
        _maybe_advance(round_obj, session)
        _maybe_finish_hand(session)
    # Don't auto-play bots here - let the frontend timer control bot actions
    # The frontend will call bot_action endpoint after the timer expires
    # Make sure we finish the hand if it's complete after advancing
    _maybe_finish_hand(session)
    
    # Return state - _state_dict will compute awaiting_player from _find_next_to_act
    # This ensures awaiting_player is always correct based on current game state
    state = _state_dict(session)
    return state


@app.get("/bot_action")
def bot_action(session_id: str) -> Dict[str, Any]:
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    game = session.game
    round_obj = game.current_round
    if not round_obj:
        raise HTTPException(status_code=400, detail="No active hand")

    # Debug: Check who should act before bot action
    next_before = _find_next_to_act(round_obj)
    if next_before:
        print(f"Bot action called: Next to act is {next_before.name} on {round_obj.street.value}, current_bet={round_obj.current_bet}")
        for p in round_obj.players:
            print(f"  {p.name}: current_bet={p.current_bet}, can_act={p.can_act()}, is_active={p.is_active}")
    else:
        print(f"Bot action called: No one to act on {round_obj.street.value}")

    # Let bot act - this will handle the action and advance/finish as needed
    _auto_play_bots(session)
    # Make sure we finish the hand if it's complete
    _maybe_finish_hand(session)
    # Return updated state
    return _state_dict(session)


@app.get("/")
def root():
    return {"ok": True}


@app.post("/next_hand")
def next_hand(req: NextHandRequest) -> Dict[str, Any]:
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    game = session.game
    # Start a new hand
    # Rotate dealer button heads-up
    game.dealer_position = 1 - game.dealer_position
    game.start_new_hand()
    # Reset and log new hand start
    session.action_log = [
        f"Hand #{game.hand_number} started. Dealer: {game.players[game.dealer_position].name}"
    ]
    # Don't auto-play bots - let the frontend timer control bot actions
    return _state_dict(session)


