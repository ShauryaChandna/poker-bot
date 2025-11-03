"""
Range Prediction Model

ML-based range prediction using player features and action sequences.
Trained on equity-based synthetic data.
"""

from typing import Optional, Dict, List, Any, Tuple
import numpy as np
import pickle
import os
from dataclasses import dataclass

from .player_profile import PlayerProfile
from .hand_history import Street
from .features import extract_features, get_feature_names
from ..simulation.hand_range import HandRange


@dataclass
class PredictionResult:
    """
    Result of range prediction.
    
    Attributes:
        range_string: Predicted range in string format
        confidence: Model confidence (0-1)
        range_probs: Probability distribution over hand categories (if available)
    """
    range_string: str
    confidence: float
    range_probs: Optional[Dict[str, float]] = None
    
    def to_hand_range(self) -> HandRange:
        """Convert to HandRange object."""
        return HandRange.from_string(self.range_string)


class RangePredictor:
    """
    Machine learning model for predicting opponent ranges.
    
    Uses player statistics, action type, position, board texture, etc.
    to predict likely hand ranges.
    
    Supports sklearn models (RandomForest, LogisticRegression, etc.)
    """
    
    def __init__(self, model: Optional[Any] = None, model_type: str = "random_forest"):
        """
        Initialize range predictor.
        
        Args:
            model: Pre-trained sklearn model (optional)
            model_type: Type of model ("random_forest", "logistic_regression")
        """
        self.model = model
        self.model_type = model_type
        self.feature_names = get_feature_names()
        self.is_trained = model is not None
        
        # Range categories for classification
        # Each category represents a range class
        # Note: Actual categories used depend on training data
        self.range_categories = [
            "ultra_tight",    # Top 5%: QQ+,AKs
            "tight",          # Top 10%: JJ+,AQs+,AKo
            "tight_medium",   # Top 15%: TT+,ATs+,AJo+,KQs
            "medium",         # Top 20%: 99+,A9s+,ATo+,KJs+,KQo
            "medium_wide",    # Top 30%: 77+,A2s+,A9o+,KTs+,QJs+
            "wide",           # Top 40%: 55+,A2s+,A5o+,K5s+,K9o+,QTs+
            "very_wide",      # Top 50%: 22+,A2s+,A2o+,K2s+,Q8s+,J9s+
        ]
        
        # Mapping from category to actual range string
        self.category_to_range = {
            "ultra_tight": "QQ+,AKs",
            "tight": "JJ+,AQs+,AKo",
            "tight_medium": "TT+,ATs+,AJo+,KQs",
            "medium": "99+,A9s+,ATo+,KJs+,KQo",
            "medium_wide": "77+,A2s+,A9o+,KTs+,QJs+",
            "wide": "55+,A2s+,A5o+,K5s+,K9o+,QTs+",
            "very_wide": "22+,A2s+,A2o+,K2s+,Q8s+,J9s+",
        }
        
        # Will be set after training to match actual model classes
        self.actual_categories = None
    
    def predict(
        self,
        player_profile: PlayerProfile,
        action: str,
        street: Street,
        board: Optional[List[str]] = None,
        position: Optional[str] = None,
        amount: int = 0,
        pot_size: int = 0,
        effective_stack: int = 0,
        facing_bet: int = 0
    ) -> PredictionResult:
        """
        Predict opponent's range based on context.
        
        Args:
            player_profile: Player statistics
            action: Action taken
            street: Current street
            board: Community cards
            position: Player position
            amount: Bet amount
            pot_size: Pot size
            effective_stack: Stack remaining
            facing_bet: Bet facing
            
        Returns:
            PredictionResult with range and confidence
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() or load() first.")
        
        # Extract features
        features = extract_features(
            player_profile=player_profile,
            action=action,
            street=street,
            board=board,
            position=position,
            amount=amount,
            pot_size=pot_size,
            effective_stack=effective_stack,
            facing_bet=facing_bet
        )
        
        # Reshape for sklearn (expects 2D array)
        features_2d = features.reshape(1, -1)
        
        # Predict
        if hasattr(self.model, 'predict_proba'):
            # Classification model with probabilities
            probs = self.model.predict_proba(features_2d)[0]
            predicted_class = np.argmax(probs)
            confidence = float(probs[predicted_class])
            
            # Get actual classes from model (may be subset of all categories)
            actual_classes = self.model.classes_
            
            # Map class index to range category
            category = self.range_categories[actual_classes[predicted_class]]
            range_string = self.category_to_range[category]
            
            # Build probability distribution (only for classes the model knows)
            range_probs = {
                self.range_categories[actual_classes[i]]: float(probs[i])
                for i in range(len(probs))
            }
        else:
            # Simple prediction without probabilities
            predicted_class = self.model.predict(features_2d)[0]
            category = self.range_categories[int(predicted_class)]
            range_string = self.category_to_range[category]
            confidence = 0.7  # Default confidence
            range_probs = None
        
        return PredictionResult(
            range_string=range_string,
            confidence=confidence,
            range_probs=range_probs
        )
    
    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Train the model on training data.
        
        Args:
            X_train: Training features (N x D)
            y_train: Training labels (N,) - range category indices
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            
        Returns:
            Dictionary of training metrics
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.metrics import accuracy_score, f1_score
        except ImportError:
            raise ImportError("scikit-learn is required for training. Install with: pip install scikit-learn")
        
        # Initialize model if not already set
        if self.model is None:
            if self.model_type == "random_forest":
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=10,
                    random_state=42,
                    n_jobs=-1
                )
            elif self.model_type == "logistic_regression":
                self.model = LogisticRegression(
                    max_iter=1000,
                    random_state=42,
                    n_jobs=-1
                )
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")
        
        # Train
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        train_preds = self.model.predict(X_train)
        train_acc = accuracy_score(y_train, train_preds)
        train_f1 = f1_score(y_train, train_preds, average='weighted')
        
        metrics = {
            'train_accuracy': train_acc,
            'train_f1': train_f1,
        }
        
        if X_val is not None and y_val is not None:
            val_preds = self.model.predict(X_val)
            val_acc = accuracy_score(y_val, val_preds)
            val_f1 = f1_score(y_val, val_preds, average='weighted')
            metrics['val_accuracy'] = val_acc
            metrics['val_f1'] = val_f1
        
        return metrics
    
    def save(self, filepath: str):
        """
        Save trained model to disk.
        
        Args:
            filepath: Path to save model (e.g., 'models/range_model.pkl')
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model.")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save model and metadata
        model_data = {
            'model': self.model,
            'model_type': self.model_type,
            'feature_names': self.feature_names,
            'range_categories': self.range_categories,
            'category_to_range': self.category_to_range,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    @classmethod
    def load(cls, filepath: str) -> 'RangePredictor':
        """
        Load trained model from disk.
        
        Args:
            filepath: Path to model file
            
        Returns:
            RangePredictor instance with loaded model
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        predictor = cls(
            model=model_data['model'],
            model_type=model_data['model_type']
        )
        predictor.feature_names = model_data['feature_names']
        predictor.range_categories = model_data['range_categories']
        predictor.category_to_range = model_data['category_to_range']
        predictor.is_trained = True
        
        return predictor


class HybridRangeEstimator:
    """
    Hybrid estimator that combines rule-based and ML approaches.
    
    Uses rule-based estimation as fallback and ML when confident.
    """
    
    def __init__(
        self,
        ml_predictor: Optional[RangePredictor] = None,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize hybrid estimator.
        
        Args:
            ml_predictor: Trained ML model (optional)
            confidence_threshold: Minimum confidence to use ML prediction
        """
        from .range_estimator import RuleBasedRangeEstimator
        
        self.ml_predictor = ml_predictor
        self.rule_based_estimator = RuleBasedRangeEstimator()
        self.confidence_threshold = confidence_threshold
    
    def estimate_range(
        self,
        player_profile: PlayerProfile,
        action: str,
        street: Street,
        board: Optional[List[str]] = None,
        position: Optional[str] = None,
        **kwargs
    ) -> Tuple[HandRange, str]:
        """
        Estimate range using hybrid approach.
        
        Args:
            player_profile: Player statistics
            action: Action taken
            street: Current street
            board: Community cards
            position: Player position
            **kwargs: Additional parameters for ML model
            
        Returns:
            Tuple of (HandRange, method_used)
            method_used is "ml" or "rule_based"
        """
        # Try ML first if available
        if self.ml_predictor is not None and self.ml_predictor.is_trained:
            try:
                prediction = self.ml_predictor.predict(
                    player_profile=player_profile,
                    action=action,
                    street=street,
                    board=board,
                    position=position,
                    **kwargs
                )
                
                # Use ML if confident
                if prediction.confidence >= self.confidence_threshold:
                    return prediction.to_hand_range(), "ml"
            except Exception as e:
                # Fall back to rule-based on error
                pass
        
        # Use rule-based as fallback
        self.rule_based_estimator.player_profile = player_profile
        
        if street == Street.PREFLOP:
            hand_range = self.rule_based_estimator.estimate_preflop_range(
                action=action,
                position=position
            )
        else:
            # For postflop, need preflop range - use default
            preflop_range = HandRange.from_string("22+,A2s+,A5o+")
            hand_range = self.rule_based_estimator.estimate_postflop_range(
                preflop_range=preflop_range,
                street=street,
                action=action,
                board=board or []
            )
        
        return hand_range, "rule_based"

