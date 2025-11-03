"""
Opponent Modeling Demo

Demonstrates both rule-based and ML-based opponent modeling approaches.
Shows how to track player stats, estimate ranges, and predict opponent behavior.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pypokerengine.opponent_modeling import (
    PlayerProfile, PlayerArchetype,
    HandHistory, ActionRecord, Street,
    RuleBasedRangeEstimator,
    RangePredictor, HybridRangeEstimator,
    extract_features
)


def demo_player_profile():
    """Demonstrate player profile tracking."""
    print("=" * 80)
    print("DEMO 1: PLAYER PROFILE TRACKING")
    print("=" * 80)
    print("\nTracking opponent statistics across hands...\n")
    
    # Create profile
    profile = PlayerProfile(player_id="villain_1")
    
    # Simulate 50 hands
    for hand_num in range(50):
        # Randomly decide if player enters pot
        import random
        enters_pot = random.random() < 0.25  # 25% VPIP
        raises = random.random() < 0.20  # 20% PFR
        
        if enters_pot:
            profile.update_preflop_action(
                action="raise" if raises else "call",
                is_raise=raises,
                is_voluntary=True
            )
        else:
            profile.update_preflop_action(
                action="fold",
                is_raise=False,
                is_voluntary=False
            )
        
        # Add some postflop actions
        if enters_pot and random.random() < 0.7:  # See flop 70% of time
            action_type = random.choice(["bet", "call", "check", "fold"])
            profile.update_postflop_action(
                action=action_type,
                is_bet=action_type == "bet",
                is_call=action_type == "call",
                is_fold=action_type == "fold"
            )
    
    # Display results
    print(f"Player ID: {profile.player_id}")
    print(f"Hands Played: {profile.hands_played}")
    print(f"\nKey Statistics:")
    print(f"  VPIP: {profile.vpip:.1%}")
    print(f"  PFR:  {profile.pfr:.1%}")
    print(f"  Aggression Factor: {profile.aggression_factor:.2f}")
    print(f"  Fold to C-Bet: {profile.fold_to_cbet:.1%}")
    print(f"\nPlayer Archetype: {profile.get_archetype().value.upper().replace('_', ' ')}")
    print(f"\n{profile}")


def demo_hand_history():
    """Demonstrate hand history tracking."""
    print("\n\n" + "=" * 80)
    print("DEMO 2: HAND HISTORY TRACKING")
    print("=" * 80)
    print("\nRecording complete hand histories...\n")
    
    history = HandHistory()
    
    # Record a sample hand
    history.start_new_hand(
        hand_id="hand_001",
        button_player="hero",
        small_blind=50,
        big_blind=100
    )
    
    # Preflop actions
    history.record_action("villain", Street.PREFLOP, "raise", 300, pot_size=150, position="BTN")
    history.record_action("hero", Street.PREFLOP, "call", 300, pot_size=450, position="BB")
    
    # Flop actions
    history.record_action("hero", Street.FLOP, "check", 0, pot_size=600, position="BB")
    history.record_action("villain", Street.FLOP, "bet", 400, pot_size=600, position="BTN")
    history.record_action("hero", Street.FLOP, "call", 400, pot_size=1000, position="BB")
    
    # Turn actions
    history.record_action("hero", Street.TURN, "check", 0, pot_size=1400, position="BB")
    history.record_action("villain", Street.TURN, "bet", 800, pot_size=1400, position="BTN")
    history.record_action("hero", Street.TURN, "fold", 0, pot_size=2200, position="BB")
    
    history.finish_hand(
        board=["As", "Kh", "Qd", "Jc"],
        pot_size=2200,
        winner="villain"
    )
    
    print(f"Hands recorded: {len(history)}")
    print(f"\nHand #{history.hands[0].hand_id}:")
    print(f"  Board: {', '.join(history.hands[0].board)}")
    print(f"  Winner: {history.hands[0].winner}")
    print(f"  Total actions: {len(history.hands[0].actions)}")
    print(f"\n  Action sequence:")
    for i, action in enumerate(history.hands[0].actions, 1):
        print(f"    {i}. {action.street.value:8s} - {action.player_id:8s} {action.action_type:6s} ${action.amount:4d}")


def demo_rule_based_estimation():
    """Demonstrate rule-based range estimation."""
    print("\n\n" + "=" * 80)
    print("DEMO 3: RULE-BASED RANGE ESTIMATION")
    print("=" * 80)
    print("\nEstimating ranges using hand-crafted heuristics...\n")
    
    # Create different player profiles
    profiles = {
        "TAG": PlayerProfile(player_id="TAG", hands_played=100),
        "LAG": PlayerProfile(player_id="LAG", hands_played=100),
        "Nit": PlayerProfile(player_id="Nit", hands_played=100),
    }
    
    # TAG player
    profiles["TAG"].vpip_count = 20
    profiles["TAG"].pfr_count = 18
    profiles["TAG"].postflop_bets = 30
    profiles["TAG"].postflop_raises = 20
    profiles["TAG"].postflop_calls = 10
    
    # LAG player
    profiles["LAG"].vpip_count = 40
    profiles["LAG"].pfr_count = 32
    profiles["LAG"].postflop_bets = 40
    profiles["LAG"].postflop_raises = 30
    profiles["LAG"].postflop_calls = 15
    
    # Nit player
    profiles["Nit"].vpip_count = 12
    profiles["Nit"].pfr_count = 10
    profiles["Nit"].postflop_bets = 10
    profiles["Nit"].postflop_raises = 5
    profiles["Nit"].postflop_calls = 15
    
    # Estimate ranges for each
    for name, profile in profiles.items():
        estimator = RuleBasedRangeEstimator(player_profile=profile)
        
        # Preflop raise range
        raise_range = estimator.estimate_preflop_range(action="raise")
        
        print(f"\n{name} Player (VPIP={profile.vpip:.1%}, PFR={profile.pfr:.1%}, AF={profile.aggression_factor:.1f}):")
        print(f"  Archetype: {profile.get_archetype().value.replace('_', ' ').title()}")
        print(f"  Preflop Raise Range: {len(raise_range.hands)} hand combos")
        print(f"  Sample hands: {', '.join(list(raise_range.hands)[:10])}...")


def demo_feature_extraction():
    """Demonstrate feature extraction for ML."""
    print("\n\n" + "=" * 80)
    print("DEMO 4: FEATURE EXTRACTION FOR ML")
    print("=" * 80)
    print("\nExtracting features from game state...\n")
    
    # Create sample profile
    profile = PlayerProfile(player_id="villain", hands_played=100)
    profile.vpip_count = 25
    profile.pfr_count = 20
    profile.postflop_bets = 30
    profile.postflop_raises = 20
    profile.postflop_calls = 25
    
    # Extract features
    features = extract_features(
        player_profile=profile,
        action="bet",
        street=Street.FLOP,
        board=["As", "Kh", "Qd"],
        position="BTN",
        amount=75,
        pot_size=100,
        effective_stack=1000,
        facing_bet=0
    )
    
    print(f"Feature vector shape: {features.shape}")
    print(f"Number of features: {len(features)}")
    print(f"\nSample feature values:")
    
    from pypokerengine.opponent_modeling.features import get_feature_names
    feature_names = get_feature_names()
    
    for i in range(min(15, len(features))):
        print(f"  {feature_names[i]:25s}: {features[i]:.4f}")
    print(f"  ... ({len(features) - 15} more features)")


def demo_ml_prediction():
    """Demonstrate ML-based range prediction (if model exists)."""
    print("\n\n" + "=" * 80)
    print("DEMO 5: ML-BASED RANGE PREDICTION")
    print("=" * 80)
    
    model_path = "models/range_model.pkl"
    
    if not os.path.exists(model_path):
        print("\n⚠️  ML model not found!")
        print(f"\nTo train the model:")
        print(f"  1. Generate training data: python scripts/generate_training_data.py")
        print(f"  2. Train model: python scripts/train_range_model.py")
        print(f"\nSkipping ML demo for now.")
        return
    
    print("\nUsing trained ML model to predict ranges...\n")
    
    # Load model
    predictor = RangePredictor.load(model_path)
    
    # Create sample profile
    profile = PlayerProfile(player_id="villain", hands_played=100)
    profile.vpip_count = 25
    profile.pfr_count = 20
    profile.postflop_bets = 30
    profile.postflop_raises = 20
    profile.postflop_calls = 25
    
    # Predict range
    prediction = predictor.predict(
        player_profile=profile,
        action="raise",
        street=Street.PREFLOP,
        position="BTN"
    )
    
    print(f"Predicted Range: {prediction.range_string}")
    print(f"Confidence: {prediction.confidence:.1%}")
    
    if prediction.range_probs:
        print(f"\nRange Category Probabilities:")
        for category, prob in sorted(prediction.range_probs.items(), key=lambda x: -x[1])[:5]:
            print(f"  {category:15s}: {prob:.1%}")


def demo_hybrid_approach():
    """Demonstrate hybrid rule-based + ML approach."""
    print("\n\n" + "=" * 80)
    print("DEMO 6: HYBRID APPROACH (Rules + ML)")
    print("=" * 80)
    print("\nCombining rule-based and ML for best results...\n")
    
    # Create profile
    profile = PlayerProfile(player_id="villain", hands_played=100)
    profile.vpip_count = 25
    profile.pfr_count = 20
    profile.postflop_bets = 30
    profile.postflop_raises = 20
    profile.postflop_calls = 25
    
    # Try to load ML model
    model_path = "models/range_model.pkl"
    ml_predictor = None
    
    if os.path.exists(model_path):
        ml_predictor = RangePredictor.load(model_path)
        print("✓ ML model loaded")
    else:
        print("⚠️  ML model not found - using rule-based fallback only")
    
    # Create hybrid estimator
    hybrid = HybridRangeEstimator(
        ml_predictor=ml_predictor,
        confidence_threshold=0.7
    )
    
    # Estimate range
    hand_range, method = hybrid.estimate_range(
        player_profile=profile,
        action="raise",
        street=Street.PREFLOP,
        position="BTN"
    )
    
    print(f"\nEstimated Range: {len(hand_range.hands)} hand combos")
    print(f"Method Used: {method.upper()}")
    print(f"Sample hands: {', '.join(list(hand_range.hands)[:10])}...")
    
    if method == "ml":
        print("\n✓ ML model was confident enough to use")
    else:
        print("\n✓ Fell back to rule-based estimation")


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "OPPONENT MODELING SYSTEM DEMO" + " " * 29 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  Phase 3: Track opponents, estimate ranges, predict behavior" + " " * 16 + "║")
    print("╚" + "═" * 78 + "╝")
    
    demo_player_profile()
    demo_hand_history()
    demo_rule_based_estimation()
    demo_feature_extraction()
    demo_ml_prediction()
    demo_hybrid_approach()
    
    print("\n\n" + "=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  1. PlayerProfile tracks opponent stats (VPIP, PFR, aggression)")
    print("  2. HandHistory records all actions for analysis")
    print("  3. Rule-based estimator works immediately with player stats")
    print("  4. ML model trained on equity-based synthetic data")
    print("  5. Hybrid approach combines both methods for best results")
    print("\nNext Steps:")
    print("  • Generate training data: python scripts/generate_training_data.py")
    print("  • Train ML model: python scripts/train_range_model.py")
    print("  • Integrate with bot: Update backend/app.py")
    print()


if __name__ == '__main__':
    main()

