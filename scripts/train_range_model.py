"""
Range Prediction Model Training Script

Trains ML model on equity-based synthetic data to predict opponent ranges.
"""

import sys
import os
import numpy as np
from typing import Tuple
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pypokerengine.opponent_modeling.range_predictor import RangePredictor


def load_training_data(data_dir: str = "data") -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load training data from disk.
    
    Args:
        data_dir: Directory containing training data
        
    Returns:
        Tuple of (X_train, y_train, X_val, y_val)
    """
    print(f"Loading training data from {data_dir}/...")
    
    X = np.load(os.path.join(data_dir, 'X_train.npy'))
    y = np.load(os.path.join(data_dir, 'y_train.npy'))
    
    print(f"✓ Loaded data: X shape={X.shape}, y shape={y.shape}")
    
    # Split into train/val (80/20)
    n_train = int(0.8 * len(X))
    
    indices = np.random.permutation(len(X))
    train_indices = indices[:n_train]
    val_indices = indices[n_train:]
    
    X_train = X[train_indices]
    y_train = y[train_indices]
    X_val = X[val_indices]
    y_val = y[val_indices]
    
    print(f"✓ Split: train={len(X_train)}, val={len(X_val)}")
    
    return X_train, y_train, X_val, y_val


def train_model(
    model_type: str = "random_forest",
    data_dir: str = "data",
    output_path: str = "models/range_model.pkl",
    seed: int = 42
) -> RangePredictor:
    """
    Train range prediction model.
    
    Args:
        model_type: Type of model ("random_forest" or "logistic_regression")
        data_dir: Directory with training data
        output_path: Path to save trained model
        seed: Random seed
        
    Returns:
        Trained RangePredictor
    """
    np.random.seed(seed)
    
    print("=" * 80)
    print("RANGE PREDICTION MODEL TRAINING")
    print("=" * 80)
    print(f"\nModel type: {model_type}")
    print(f"Output path: {output_path}")
    print()
    
    # Load data
    X_train, y_train, X_val, y_val = load_training_data(data_dir)
    
    # Initialize model
    print(f"\nInitializing {model_type} model...")
    predictor = RangePredictor(model_type=model_type)
    
    # Train
    print("\nTraining model...")
    print("-" * 80)
    
    metrics = predictor.train(X_train, y_train, X_val, y_val)
    
    print("\n" + "-" * 80)
    print("Training Results:")
    print("-" * 80)
    for metric_name, metric_value in metrics.items():
        print(f"  {metric_name:20s}: {metric_value:.4f}")
    
    # Save model
    print(f"\nSaving model to {output_path}...")
    predictor.save(output_path)
    print("✓ Model saved successfully")
    
    # Print feature importances (if available)
    if hasattr(predictor.model, 'feature_importances_'):
        print("\nTop 10 Most Important Features:")
        print("-" * 80)
        
        # Load feature names
        with open(os.path.join(data_dir, 'feature_names.json'), 'r') as f:
            feature_names = json.load(f)
        
        importances = predictor.model.feature_importances_
        indices = np.argsort(importances)[::-1][:10]
        
        for i, idx in enumerate(indices, 1):
            print(f"  {i:2d}. {feature_names[idx]:30s}: {importances[idx]:.4f}")
    
    return predictor


def evaluate_model(
    predictor: RangePredictor,
    data_dir: str = "data"
):
    """
    Detailed evaluation of trained model.
    
    Args:
        predictor: Trained model
        data_dir: Directory with data
    """
    print("\n" + "=" * 80)
    print("MODEL EVALUATION")
    print("=" * 80)
    
    # Load validation data
    _, _, X_val, y_val = load_training_data(data_dir)
    
    # Predictions
    y_pred = predictor.model.predict(X_val)
    
    # Confusion matrix
    from sklearn.metrics import confusion_matrix, classification_report
    
    cm = confusion_matrix(y_val, y_pred)
    
    print("\nConfusion Matrix:")
    print("-" * 80)
    print(cm)
    
    # Classification report
    print("\nClassification Report:")
    print("-" * 80)
    
    target_names = [
        "ultra_tight",
        "tight",
        "tight_medium",
        "medium",
        "medium_wide",
        "wide",
        "very_wide",
    ]
    
    report = classification_report(y_val, y_pred, target_names=target_names)
    print(report)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Train range prediction model')
    parser.add_argument('--model', type=str, default='random_forest',
                       choices=['random_forest', 'logistic_regression'],
                       help='Model type to train')
    parser.add_argument('--data-dir', type=str, default='data',
                       help='Directory with training data')
    parser.add_argument('--output', type=str, default='models/range_model.pkl',
                       help='Output path for trained model')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed')
    parser.add_argument('--evaluate', action='store_true',
                       help='Run detailed evaluation after training')
    
    args = parser.parse_args()
    
    # Check if training data exists
    if not os.path.exists(os.path.join(args.data_dir, 'X_train.npy')):
        print("❌ ERROR: Training data not found!")
        print(f"\nPlease run data generation first:")
        print(f"  python scripts/generate_training_data.py --output {args.data_dir}")
        sys.exit(1)
    
    # Train model
    predictor = train_model(
        model_type=args.model,
        data_dir=args.data_dir,
        output_path=args.output,
        seed=args.seed
    )
    
    # Evaluate if requested
    if args.evaluate:
        evaluate_model(predictor, args.data_dir)
    
    print("\n" + "=" * 80)
    print("✅ TRAINING COMPLETE!")
    print("=" * 80)
    print(f"\nTrained model saved to: {args.output}")
    print("\nNext steps:")
    print("  1. Test the model: python examples/opponent_modeling_demo.py")
    print("  2. Integrate with bot: Update backend/app.py to use opponent modeling")

