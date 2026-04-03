"""Modular text classification for Synapse AI with weighted keyword matching and learning."""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


# ============================================================================
# CONFIGURATION: Weighted keywords for better classification
# ============================================================================

CATEGORY_KEYWORDS = {
    "COLLEGE": {
        "assignment": 2.0,
        "semester": 2.0,
        "exam": 2.5,
        "operating system": 2.5,
        "dbms": 2.5,
        "computer networks": 2.0,
        "algorithm": 1.5,
        "lecture": 1.5,
        "syllabus": 2.0,
    },
    "PROGRAMMING": {
        "python": 2.0,
        "java": 2.0,
        "c++": 2.0,
        "javascript": 2.0,
        "function": 1.2,
        "class": 1.0,  # Low weight: too generic
        "api": 1.5,
        "github": 1.8,
        "code": 0.8,  # Low weight: appears everywhere
    },
    "PROJECTS": {
        "project": 1.5,
        "roadmap": 2.5,
        "milestone": 2.0,
        "feature": 1.2,
        "prototype": 2.0,
        "deployment": 1.8,
        "sprint": 2.0,
    },
    "CAREER": {
        "resume": 2.5,
        "cv": 2.5,
        "interview": 2.0,
        "job": 1.5,
        "internship": 2.0,
        "linkedin": 2.0,
        "portfolio": 1.5,
    },
    "REFERENCE": {
        "guide": 1.5,
        "documentation": 2.0,
        "manual": 1.8,
        "reference": 1.5,
        "notes": 0.8,  # Low weight: generic
        "tutorial": 1.5,
        "example": 0.8,
    },
}

TAG_KEYWORDS = {
    "os": {
        "operating system": 2.0,
        "process": 1.5,
        "thread": 1.8,
        "deadlock": 2.0,
        "kernel": 2.0,
    },
    "db": {
        "database": 2.0,
        "dbms": 2.0,
        "sql": 2.0,
        "query": 1.5,
        "schema": 1.5,
    },
    "networks": {
        "network": 1.5,
        "tcp": 2.0,
        "udp": 2.0,
        "http": 1.8,
        "socket": 1.5,
    },
    "coding": {
        "python": 2.0,
        "java": 2.0,
        "c++": 2.0,
        "algorithm": 1.8,
        "api": 1.5,
        "code": 0.5,  # Very low weight
    },
    "career": {
        "resume": 2.0,
        "interview": 1.8,
        "job": 1.5,
        "internship": 1.8,
        "freelance": 1.5,
    },
}

# Classification confidence thresholds
CONFIDENCE_THRESHOLD = 0.5  # Minimum confidence to classify as category
TAG_THRESHOLD = 0.3  # Minimum confidence for tag extraction


# ============================================================================
# CLASSES: Modular pipeline components
# ============================================================================

@dataclass
class ClassificationResult:
    """Result of content classification with confidence score."""
    category: str
    confidence: float
    scores: Dict[str, float]


class TextPreprocessor:
    """Handles text normalization and preparation."""

    @staticmethod
    def preprocess(content: str, file_name: str) -> str:
        """
        Normalize text for keyword matching.
        
        - Combines filename and content (filename carries importance)
        - Converts to lowercase
        - Removes extra whitespace
        """
        combined = f"{file_name} {content}"
        # Normalize whitespace
        combined = re.sub(r'\s+', ' ', combined)
        return combined.lower()

    @staticmethod
    def tokenize_words(text: str) -> List[str]:
        """Extract individual words for word-boundary matching."""
        return re.findall(r'\b\w+\b', text)


class FeatureExtractor:
    """Extracts weighted features from text."""

    def __init__(
        self, 
        keyword_weights: Dict[str, Dict[str, float]],
        match_type: str = "phrase"
    ):
        """
        Initialize extractor.
        
        Args:
            keyword_weights: Dict mapping categories to keyword->weight mappings
            match_type: "phrase" (substring) or "word" (word boundary)
        """
        self.keyword_weights = keyword_weights
        self.match_type = match_type

    def extract_features(self, text: str) -> Dict[str, float]:
        """
        Compute weighted feature scores for each category.
        
        Returns:
            Dict mapping category to total weighted score
        """
        scores: Dict[str, float] = {}
        
        for category, keywords in self.keyword_weights.items():
            score = 0.0
            for keyword, weight in keywords.items():
                matches = self._count_matches(text, keyword)
                score += matches * weight
            scores[category] = score
        
        return scores

    def _count_matches(self, text: str, keyword: str) -> int:
        """
        Count keyword occurrences in text.
        
        Uses phrase matching (substring) but could be upgraded to
        word-boundary matching or embeddings.
        """
        # Simple phrase matching - can be improved
        return text.count(keyword)


class Classifier:
    """Main classifier using modular components."""

    def __init__(
        self,
        preprocessor: TextPreprocessor,
        feature_extractor: FeatureExtractor,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ):
        """Initialize classifier with components."""
        self.preprocessor = preprocessor
        self.feature_extractor = feature_extractor
        self.confidence_threshold = confidence_threshold

    def classify(
        self, 
        content: str, 
        file_name: str
    ) -> ClassificationResult:
        """
        Classify content into a category.
        
        Returns:
            ClassificationResult with category, confidence score, and all scores
        """
        # Step 1: Preprocess input text
        text = self.preprocessor.preprocess(content, file_name)

        # Step 2: Compute raw weighted scores per category
        raw_scores = self.feature_extractor.extract_features(text)

        # Keep only non-negative values for stable confidence math.
        safe_scores = {
            category: max(0.0, float(score))
            for category, score in raw_scores.items()
        }

        # If nothing matched, return a low-confidence GENERAL classification.
        if not safe_scores:
            return ClassificationResult(
                category="GENERAL",
                confidence=0.0,
                scores={},
            )

        total_score = sum(safe_scores.values())
        if total_score <= 0:
            return ClassificationResult(
                category="GENERAL",
                confidence=0.0,
                scores={category: 0.0 for category in safe_scores},
            )

        # Step 3: Select best category from raw scores
        best_category = max(safe_scores, key=safe_scores.get)
        best_score = safe_scores[best_category]

        # Step 4: Build normalized category distribution (sums to ~1.0)
        normalized_scores = {
            category: score / total_score
            for category, score in safe_scores.items()
        }

        # Step 5: Confidence combines dominance and separation from runner-up
        sorted_scores = sorted(safe_scores.values(), reverse=True)
        second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0

        dominance = best_score / total_score
        margin = (best_score - second_score) / best_score if best_score > 0 else 0.0
        confidence = (dominance + margin) / 2.0

        # Step 6: Apply fallback threshold
        category = best_category if confidence >= self.confidence_threshold else "GENERAL"

        return ClassificationResult(
            category=category,
            confidence=confidence,
            scores=normalized_scores,
        )


class TagExtractor:
    """Extract meaningful tags from content using simple score-based filtering."""

    def __init__(
        self,
        feature_extractor: FeatureExtractor,
        tag_threshold: float = TAG_THRESHOLD,
    ):
        """Initialize tag extractor.

        Args:
            feature_extractor: Computes raw weighted scores for configured tags.
            tag_threshold: Minimum normalized score required to keep a tag.
        """
        self.feature_extractor = feature_extractor
        self.tag_threshold = tag_threshold

    def _normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Return per-tag normalized scores in range [0, 1]."""
        max_score = max(scores.values()) if scores else 0.0
        if max_score <= 0:
            return {tag: 0.0 for tag in scores}

        return {
            tag: max(0.0, float(score)) / max_score
            for tag, score in scores.items()
        }

    def _select_tags(self, normalized_scores: Dict[str, float]) -> List[str]:
        """Keep only confident tags and return them in deterministic order."""
        selected = [
            tag
            for tag, confidence in normalized_scores.items()
            # Keep tags that cross the configured confidence threshold.
            if confidence >= self.tag_threshold
        ]
        return sorted(selected)

    def extract_tags(
        self, 
        content: str, 
        file_name: str
    ) -> List[str]:
        """
        Extract tags with confidence threshold.
        
        Only includes tags meeting the confidence threshold.
        """
        # 1) Normalize text once so filename and content both contribute.
        text = TextPreprocessor.preprocess(content, file_name)

        # 2) Compute raw weighted tag scores from keyword matches.
        scores = self.feature_extractor.extract_features(text)

        # 3) Convert raw scores to relative confidence scores.
        normalized_scores = self._normalize_scores(scores)

        # 4) Keep only meaningful tags (above threshold).
        return self._select_tags(normalized_scores)


# ============================================================================
# PUBLIC API: Backward-compatible functions
# ============================================================================

def _get_category_weights() -> Dict[str, Dict[str, float]]:
    """
    Get category weights, with learning adjustments if available.
    
    Falls back to CATEGORY_KEYWORDS if learning module not available.
    """
    try:
        from synapse.ai.learning import get_learned_weights
        return get_learned_weights(CATEGORY_KEYWORDS)
    except Exception:
        # Learning module not available or error loading - use base weights
        return CATEGORY_KEYWORDS


def _get_tag_weights() -> Dict[str, Dict[str, float]]:
    """
    Get tag weights, with learning adjustments if available.
    
    Falls back to TAG_KEYWORDS if learning module not available.
    """
    try:
        from synapse.ai.learning import get_learned_weights
        return get_learned_weights(TAG_KEYWORDS)
    except Exception:
        # Learning module not available or error loading - use base weights
        return TAG_KEYWORDS


# Initialize default classifier and extractors with learned weights
_preprocessor = TextPreprocessor()
_category_extractor = FeatureExtractor(_get_category_weights())
_tag_extractor = FeatureExtractor(_get_tag_weights())

_classifier = Classifier(_preprocessor, _category_extractor)
_tag_extractor_obj = TagExtractor(_tag_extractor)


def refresh_classifier_weights() -> None:
    """
    Refresh classifier extractors with latest learned weights.
    
    Call this after learning from feedback to update classifications.
    
    Example:
        >>> from synapse.ai.classifier import refresh_classifier_weights
        >>> learn_from_feedback(file_model, "SOURCE_CODE")
        >>> refresh_classifier_weights()  # Update classifier with new weights
    """
    global _category_extractor, _tag_extractor, _classifier, _tag_extractor_obj
    
    _category_extractor = FeatureExtractor(_get_category_weights())
    _tag_extractor = FeatureExtractor(_get_tag_weights())
    
    _classifier = Classifier(_preprocessor, _category_extractor)
    _tag_extractor_obj = TagExtractor(_tag_extractor)


def classify_content(content: str, file_name: str) -> str:
    """
    Return the best matching category for the provided content.
    
    This is a simple string interface maintaining backward compatibility.
    For more detail (confidence scores), use the Classifier class directly.
    """
    result = _classifier.classify(content, file_name)
    return result.category


def extract_tags(content: str, file_name: str) -> List[str]:
    """
    Extract lightweight tags based on weighted keyword matches.
    
    Returns only tags with sufficient confidence.
    """
    return _tag_extractor_obj.extract_tags(content, file_name)


def classify_content_detailed(content: str, file_name: str) -> ClassificationResult:
    """
    Return detailed classification with confidence score and all scores.
    
    Useful for debugging, logging, or UI display of classification confidence.
    """
    return _classifier.classify(content, file_name)


# ============================================================================
# REVIEW: What Changed & Why
# ============================================================================
#
# ORIGINAL DESIGN PROBLEMS:
# ========================
#
# 1. Unweighted Keywords
#    - All keywords treated equally (e.g., "class" = "algorithm")
#    - Problem: Common words like "function", "code", "class" create false positives
#    - Impact: Poor classification accuracy, hard to tune
#
# 2. Naive Substring Matching
#    - "class" matches "class", "classify", "classic" (false positives)
#    - No intelligence about word boundaries or term importance
#
# 3. Poor Scalability
#    - Keywords in static lists with no structure
#    - Difficult to prioritize important keywords vs. noise
#    - No confidence scores - just binary presence
#
# 4. Tight Coupling
#    - Preprocessing, feature extraction, and scoring mixed together
#    - Hard to change one aspect without breaking others
#    - Impossible to upgrade to embeddings or better ML without rewrite
#
# 5. No Confidence Confidence Handling
#    - No way to know if classification was confident or uncertain
#    - Threshold handling (checking if score == 0) was brittle
#
#
# IMPROVEMENTS MADE:
# ==================
#
# 1. Weighted Keywords
#    - Keywords now have weights (1.0-2.5 scale)
#    - Important keywords contribute more: "exam" (2.5) vs "code" (0.8)
#    - Added keyword weights to both categories and tags
#    - Result: Smarter, more nuanced classification
#
# 2. Modular Architecture
#    - TextPreprocessor: Handles text normalization
#    - FeatureExtractor: Computes weighted keyword matches
#    - Classifier: Orchestrates pipeline, normalizes scores, handles thresholds
#    - TagExtractor: Separate tag extraction logic
#    - Result: Each component has single responsibility, easy to test/modify
#
# 3. Normalized Confidence Scores
#    - All scores normalized to 0-1 range
#    - Easy to threshold, display, or log
#    - ClassificationResult dataclass provides structured output
#    - Result: Can distinguish high vs. marginal confidence
#
# 4. Configurable Thresholds
#    - CONFIDENCE_THRESHOLD: Fallback to GENERAL if below this
#    - TAG_THRESHOLD: Only extract tags with sufficient confidence
#    - Result: Can adjust precision/recall trade-off
#
# 5. Backward Compatible
#    - classify_content() still works as before
#    - extract_tags() still works as before
#    - New classify_content_detailed() provides confidence info
#    - Result: Drop-in replacement, no code changes needed
#
# 6. Future-Ready
#    - FeatureExtractor.extract_features() is the key abstraction
#    - Can swap in embedding-based features later
#    - Classifier & TagExtractor don't know about keywords
#    - Result: Easy to upgrade to semantic similarity, embeddings, etc.
#
#
# REMAINING LIMITATIONS:
# ======================
#
# 1. Still Phrase-Based
#    - Uses substring matching, not semantic understanding
#    - Can't distinguish "data structure" from "data streaming"
#    - Mitigation: Word boundaries could be added; embeddings later
#
# 2. No Context Awareness
#    - Treats all text equally regardless of position (title vs. body)
#    - "python" in filename vs. casual mention weighted the same
#    - Mitigation: Could weight file_name content higher
#
# 3. Keyword Engineering Required
#    - Still need to manually curate and weight keywords
#    - New domains/categories require manual keyword lists
#    - Mitigation: Future: learn weights from labeled data, or embeddings
#
# 4. No Fuzzy Matching
#    - Typos, misspellings not handled (e.g., "algoritm" won't match)
#    - Mitigation: Could add Levenshtein distance or stemming
#
# 5. Limited Multi-Label
#    - Classification focuses on single best category
#    - Could return multiple categories with confidence (future work)
#
#
# RECOMMENDED NEXT STEPS:
# =======================
#
# 1. Add Word Boundary Matching (Medium Effort)
#    - Replace substring count with regex word boundaries
#    - Avoid "class" matching "classify"
#
# 2. Context-Aware Weighting (Low Effort)
#    - Weight filename keywords higher than body
#    - Example: "python" in filename = 3.0, in body = 2.0
#
# 3. Collect Training Data (High Value)
#    - Log all classifications with user corrections
#    - Learn true weights from data rather than manual tuning
#
# 4. Embedding-Based Alternative (Medium-High Effort)
#    - Create EmbeddingFeatureExtractor subclass
#    - Use sentence-transformers for semantic similarity
#    - Plugs directly into Classifier without changes
#
# 5. Add Explainability (Low Effort)
#    - Return which keywords contributed to classification
#    - Helpful for debugging and user trust
# ============================================================================
