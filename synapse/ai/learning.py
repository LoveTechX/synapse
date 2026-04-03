"""
Simple learning system for incremental classifier improvement.

Tracks user feedback and adjusts keyword weights based on corrections.
Allows the system to improve from misclassifications without retraining.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Set

from synapse.models.file_model import FileModel
from synapse.storage.memory import extract_keywords


# Configure logging
logger = logging.getLogger(__name__)

# Default weight adjustment increment
WEIGHT_INCREMENT = 0.5
MAX_WEIGHT = 5.0  # Cap on keyword weights to prevent runaway growth
LEARNING_FILE = "learning_adjustments.json"


# ============================================================================
# LEARNING STATE: Track weight adjustments
# ============================================================================

class WeightLearner:
    """
    Manage incremental weight adjustments based on user feedback.
    
    Stores adjustments as:
        {category: {keyword: adjustment_value}}
    
    These are applied ON TOP of base weights, not replacing them.
    """

    def __init__(self, learning_file: str = LEARNING_FILE):
        """
        Initialize learner, optionally loading from disk.
        
        Args:
            learning_file: Path to JSON file for persistence
        """
        self.learning_file = learning_file
        # Adjustments: {category: {keyword: weight_delta}}
        self.adjustments: Dict[str, Dict[str, float]] = {}
        
        # Load saved adjustments if file exists
        self._load_adjustments()
    
    def _load_adjustments(self) -> None:
        """Load adjustments from JSON file if it exists."""
        learning_path = Path(self.learning_file)
        
        if learning_path.exists():
            try:
                with open(learning_path, 'r') as f:
                    data = json.load(f)
                    self.adjustments = data.get("adjustments", {})
                    logger.info("Loaded %d categories with adjustments", len(self.adjustments))
            except Exception as e:
                logger.warning("Failed to load adjustments: %s", str(e))
                self.adjustments = {}
    
    def _save_adjustments(self) -> None:
        """Save adjustments to JSON file for persistence."""
        try:
            learning_path = Path(self.learning_file)
            with open(learning_path, 'w') as f:
                json.dump({"adjustments": self.adjustments}, f, indent=2)
            logger.debug("Saved adjustments to %s", self.learning_file)
        except Exception as e:
            logger.warning("Failed to save adjustments: %s", str(e))
    
    def apply_feedback(
        self,
        file_model: FileModel,
        correct_category: str
    ) -> None:
        """
        Apply user feedback to improve weights.
        
        When user corrects a misclassification:
        1. Extract keywords from the file that should match the correct category
        2. Increase weights for those keywords in the correct category
        3. Optionally decrease weights in wrong category (not implemented for simplicity)
        
        Args:
            file_model: The file that was misclassified
            correct_category: The category it should have been classified into
        """
        # Extract keywords from content and tags
        keywords = extract_keywords(file_model.content, file_model.tags)
        
        logger.info(
            "Feedback: file '%s' should be %s (extracted %d keywords)",
            file_model.name,
            correct_category,
            len(keywords)
        )
        
        # Update weights for correct category
        self.update_weights(keywords, correct_category)
        
        # Save to disk for persistence
        self._save_adjustments()
    
    def update_weights(
        self,
        keywords: List[str],
        category: str,
        increment: float = WEIGHT_INCREMENT
    ) -> None:
        """
        Increase weights for keywords in a category.
        
        Args:
            keywords: List of keywords to boost
            category: Category to boost keywords for
            increment: How much to increase each keyword weight
        """
        # Initialize category if not present
        if category not in self.adjustments:
            self.adjustments[category] = {}
        
        # Increase weight for each keyword
        for keyword in keywords:
            current = self.adjustments[category].get(keyword, 0.0)
            new_value = min(current + increment, MAX_WEIGHT)
            self.adjustments[category][keyword] = new_value
            
            logger.debug(
                "Updated weight: %s.%s = %.2f",
                category,
                keyword,
                new_value
            )
    
    def decrease_weights(
        self,
        keywords: List[str],
        category: str,
        decrement: float = WEIGHT_INCREMENT / 2
    ) -> None:
        """
        Decrease weights for keywords in a category.
        
        Useful when a category is over-predicted.
        
        Args:
            keywords: List of keywords to reduce
            category: Category to reduce keywords for
            decrement: How much to decrease (capped at 0)
        """
        if category not in self.adjustments:
            self.adjustments[category] = {}
        
        for keyword in keywords:
            current = self.adjustments[category].get(keyword, 0.0)
            new_value = max(current - decrement, 0.0)
            self.adjustments[category][keyword] = new_value
            
            logger.debug(
                "Decreased weight: %s.%s = %.2f",
                category,
                keyword,
                new_value
            )
    
    def get_adjusted_weights(
        self,
        base_weights: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Merge adjustments with base weights.
        
        Returns a new dictionary with:
        - Original base weights
        - PLUS any learned adjustments
        
        Args:
            base_weights: Original weights from classifier (CATEGORY_KEYWORDS, etc)
            
        Returns:
            New weight dictionary with adjustments applied
        """
        # Deep copy base weights
        adjusted = {}
        for category, keywords in base_weights.items():
            adjusted[category] = dict(keywords)  # Copy the keyword dict
        
        # Apply adjustments on top
        for category, keyword_adjustments in self.adjustments.items():
            if category not in adjusted:
                adjusted[category] = {}
            
            for keyword, adjustment in keyword_adjustments.items():
                current = adjusted[category].get(keyword, 0.0)
                adjusted[category][keyword] = current + adjustment
        
        return adjusted
    
    def reset(self) -> None:
        """Reset all adjustments (useful for testing)."""
        self.adjustments.clear()
        self._save_adjustments()
        logger.info("Adjustments reset")
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about learned adjustments."""
        stats = {}
        for category, keywords in self.adjustments.items():
            stats[category] = len(keywords)
        return stats
    
    def explain_adjustment(self, category: str, keyword: str) -> float:
        """
        Get the adjustment value for a specific keyword in a category.
        
        Args:
            category: Category name
            keyword: Keyword name
            
        Returns:
            Adjustment value (0.0 if none)
        """
        return self.adjustments.get(category, {}).get(keyword, 0.0)


# ============================================================================
# GLOBAL LEARNER INSTANCE
# ============================================================================

_learner: WeightLearner = None


def get_learner() -> WeightLearner:
    """Get or create the global learner instance."""
    global _learner
    if _learner is None:
        _learner = WeightLearner()
    return _learner


def reset_learner() -> None:
    """Reset the global learner (useful for testing)."""
    global _learner
    _learner = None


# ============================================================================
# PUBLIC API
# ============================================================================

def learn_from_feedback(
    file_model: FileModel,
    correct_category: str
) -> None:
    """
    Apply feedback to improve classifier weights.
    
    Call this when a misclassification is detected and corrected.
    
    Args:
        file_model: The file that was misclassified
        correct_category: The correct category it should belong to
        
    Example:
        >>> # User corrects misclassification
        >>> from synapse.ai.learning import learn_from_feedback
        >>> learn_from_feedback(file_model, "SOURCE_CODE")
    """
    learner = get_learner()
    learner.apply_feedback(file_model, correct_category)


def get_learned_weights(
    base_weights: Dict[str, Dict[str, float]]
) -> Dict[str, Dict[str, float]]:
    """
    Get weights with learned adjustments applied.
    
    Used by classifier to get improved weights.
    
    Args:
        base_weights: Original weights from CATEGORY_KEYWORDS or TAG_KEYWORDS
        
    Returns:
        Adjusted weights incorporating learning
    """
    learner = get_learner()
    return learner.get_adjusted_weights(base_weights)


def get_learning_stats() -> Dict[str, int]:
    """Get statistics about current learning state."""
    learner = get_learner()
    return learner.get_stats()
