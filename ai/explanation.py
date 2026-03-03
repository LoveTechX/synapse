"""
PHASE 3: Explanation Engine
Detailed, human-readable explanations for every classification decision.
Shows exactly which signals triggered the decision (keywords, semantics, rules).
"""

from typing import Optional, List, Dict, Any


class ExplanationEngine:
    """Generate detailed explanations for file classification decisions."""

    @staticmethod
    def keyword_rule_detected(keyword: str, source: str = "filename") -> str:
        """
        Generate explanation for keyword-based rule match.

        Args:
            keyword: Matched keyword
            source: "filename" | "content" | "path"

        Returns:
            Human-readable explanation
        """
        sources = {
            "filename": f"Keyword '{keyword}' found in filename",
            "content": f"Keyword '{keyword}' detected in file content",
            "path": f"Keyword '{keyword}' found in file path",
        }
        return sources.get(source, f"Keyword '{keyword}' matched")

    @staticmethod
    def semantic_match(
        category: str,
        confidence: float,
        matched_concepts: Optional[List[str]] = None,
    ) -> str:
        """
        Generate explanation for semantic classifier match.

        Args:
            category: Detected category
            confidence: Match confidence (0-1)
            matched_concepts: List of matching semantic concepts

        Returns:
            Human-readable explanation
        """
        confidence_pct = confidence * 100
        explanation = (
            f"Semantic similarity matched to '{category}' ({confidence_pct:.0f}%)"
        )

        if matched_concepts:
            concepts_str = ", ".join(matched_concepts)
            explanation += f"\n  Matched concepts: {concepts_str}"

        return explanation

    @staticmethod
    def extension_rule(ext: str, category: str) -> str:
        """Generate explanation for extension-based routing."""
        return f"File extension '.{ext}' maps to '{category}' category"

    @staticmethod
    def subject_detection(subject: str, confidence: float) -> str:
        """Generate explanation for subject detection."""
        confidence_pct = confidence * 100
        return f"Subject classifier detected: '{subject}' ({confidence_pct:.0f}% match)"

    @staticmethod
    def skip_reason(reason_code: str, details: Optional[str] = None) -> str:
        """
        Generate explanation for why a file was skipped.

        Args:
            reason_code: "hidden_file" | "system_file" | "build_artifact" |
                        "non_content" | "no_extraction" | "insufficient_confidence"
            details: Additional context

        Returns:
            Human-readable skip reason
        """
        reasons = {
            "hidden_file": "File starts with '.' (hidden file) - skipped for safety",
            "system_file": "System/configuration file - skipped to preserve project structure",
            "build_artifact": "Build system artifact - cannot classify reliably",
            "non_content": "File extension not eligible for content-based classification",
            "no_extraction": "No text content could be extracted from file",
            "insufficient_confidence": "Classification confidence too low for safe automation",
            "already_in_destination": "File already in appropriate destination",
            "lock_file": "File is currently locked by another process",
            "permission_denied": "Permission denied - cannot access or move file",
        }

        explanation = reasons.get(reason_code, "File skipped due to processing rules")

        if details:
            explanation += f" ({details})"

        return explanation

    @staticmethod
    def duplicate_detected(existing_location: str) -> str:
        """Generate explanation for duplicate file detection."""
        return f"Duplicate content detected at '{existing_location}' - skipped"

    @staticmethod
    def conflict_resolution(conflict_type: str, resolution: str) -> str:
        """
        Generate explanation for conflict resolution.

        Args:
            conflict_type: "filename_collision" | "folder_exists" | "version_exists"
            resolution: How the conflict was resolved

        Returns:
            Human-readable explanation
        """
        explanations = {
            "filename_collision": "Filename already exists - creating versioned copy",
            "folder_exists": "Destination folder already exists - proceeding with move",
            "version_exists": "Versioned file already exists - incrementing version number",
        }

        explanation = explanations.get(conflict_type, "Conflict detected and resolved")
        if resolution:
            explanation += f" → {resolution}"

        return explanation

    @staticmethod
    def extraction_failure(reason: str) -> str:
        """Generate explanation for content extraction failure."""
        return f"Content extraction failed: {reason} - using rules-based classification"

    @staticmethod
    def fallback_routing(reason: str) -> str:
        """Generate explanation for fallback routing."""
        return f"Primary classification failed ({reason}) - using fallback destination"

    @staticmethod
    def generate_detailed_report(
        file_name: str,
        decision: str,  # "moved" | "skipped" | "duplicate"
        reason: str,
        category: Optional[str] = None,
        subject: Optional[str] = None,
        destination: Optional[str] = None,
        confidence: Optional[float] = None,
        signals: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a comprehensive explanation report.

        Args:
            file_name: Name of the file
            decision: What action was taken
            reason: Primary reason
            category: Detected category
            subject: Detected subject
            destination: Final destination
            confidence: Semantic confidence
            signals: List of triggering signals

        Returns:
            Formatted multi-line report
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"📋 DECISION REPORT: {file_name}")
        lines.append("=" * 70)

        if decision == "moved":
            lines.append(f"Action:        ✓ MOVED")
        elif decision == "skipped":
            lines.append(f"Action:        ✗ SKIPPED")
        else:
            lines.append(f"Action:        ⊙ {decision.upper()}")

        lines.append(f"Primary Reason: {reason}")

        if category:
            lines.append(f"Category:       {category}")
        if subject and subject.lower() != "general":
            lines.append(f"Subject:        {subject}")
        if destination:
            lines.append(f"Destination:    {destination}")
        if confidence is not None and confidence >= 0:
            confidence_pct = confidence * 100
            lines.append(f"Confidence:     {confidence_pct:.0f}%")

        if signals:
            lines.append("\nDetection Signals:")
            for signal in signals:
                lines.append(f"  • {signal}")

        lines.append("=" * 70)

        return "\n".join(lines)

    @staticmethod
    def print_explanation(explanation: str, verbose: bool = False) -> None:
        """Pretty-print an explanation."""
        if verbose:
            print(explanation)
        else:
            # Abbreviated version
            first_line = explanation.split("\n")[0]
            print(f"ℹ️  {first_line}")


# Global instances
explanation_engine = ExplanationEngine()
