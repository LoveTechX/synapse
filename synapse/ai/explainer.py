"""Intelligent explanations for Synapse AI classification decisions."""

from typing import List, Optional

from synapse.ai.classifier import classify_content_detailed, CATEGORY_KEYWORDS, TAG_KEYWORDS


# ============================================================================
# CATEGORY-SPECIFIC EXPLANATION TEMPLATES
# ============================================================================
# These templates explain WHY each category is meaningful and what signals
# indicate content belongs to that category.

CATEGORY_EXPLANATIONS = {
    "COLLEGE": {
        "description": "Academic coursework and university materials",
        "signals": [
            "course assignments and exams",
            "computer science fundamentals like OS, databases, and networks",
            "structured learning materials",
        ],
    },
    "PROGRAMMING": {
        "description": "Software development and coding projects",
        "signals": [
            "programming languages and code frameworks",
            "software APIs and architecture",
            "development tools and version control",
        ],
    },
    "PROJECTS": {
        "description": "Project planning, roadmaps, and deliverables",
        "signals": [
            "project milestones and features",
            "development roadmaps and sprints",
            "deployment and release planning",
        ],
    },
    "CAREER": {
        "description": "Career development and professional materials",
        "signals": [
            "resume, CV, and portfolio content",
            "job search and interview preparation",
            "professional networking and freelancing",
        ],
    },
    "REFERENCE": {
        "description": "Reference materials and documentation",
        "signals": [
            "guides, manuals, and tutorials",
            "technical documentation and specifications",
            "reference notes and examples",
        ],
    },
    "GENERAL": {
        "description": "General or miscellaneous content",
        "signals": ["content that doesn't strongly match other categories"],
    },
}


# ============================================================================
# KEYWORD MAPPING: Link keywords to human-readable phrases
# ============================================================================
# Used to make explanations more readable than raw keywords

KEYWORD_LABELS = {
    # College keywords
    "assignment": "assignments",
    "semester": "coursework",
    "exam": "exams",
    "operating system": "operating systems",
    "dbms": "database management",
    "computer networks": "networking",
    "algorithm": "algorithms",
    "lecture": "lectures",
    "syllabus": "course structure",
    # Programming keywords
    "python": "Python",
    "java": "Java",
    "c++": "C++",
    "javascript": "JavaScript",
    "function": "code functions",
    "class": "code classes",
    "api": "APIs",
    "github": "GitHub",
    "code": "code",
    # Projects keywords
    "project": "projects",
    "roadmap": "roadmaps",
    "milestone": "milestones",
    "feature": "features",
    "prototype": "prototypes",
    "deployment": "deployment planning",
    "sprint": "sprints",
    # Career keywords
    "resume": "resume",
    "cv": "curriculum vitae",
    "interview": "interview prep",
    "job": "job search",
    "internship": "internships",
    "linkedin": "LinkedIn",
    "portfolio": "portfolio",
    # Reference keywords
    "guide": "guides",
    "documentation": "documentation",
    "manual": "manuals",
    "reference": "reference materials",
    "notes": "notes",
    "tutorial": "tutorials",
    "example": "examples",
    # Tag keywords
    "os": "operating systems",
    "db": "databases",
    "networks": "networking",
    "coding": "coding",
    "career": "career",
}


# ============================================================================
# HELPER FUNCTIONS: Extract matching keywords
# ============================================================================

def _get_matched_keywords(
    content: str,
    file_name: str,
    category: str,
) -> List[str]:
    """
    Find which keywords from the category matched in the content.
    
    Args:
        content: File content (raw text)
        file_name: Original filename
        category: Category classification
        
    Returns:
        List of human-readable labels for matched keywords
    """
    text = f"{file_name} {content}".lower()
    matched = []
    
    # Get keywords for this category
    if category in CATEGORY_KEYWORDS:
        keywords = CATEGORY_KEYWORDS[category]
        for keyword in keywords.keys():
            if keyword in text:
                label = KEYWORD_LABELS.get(keyword, keyword)
                if label not in matched:  # Avoid duplicates
                    matched.append(label)
    
    return matched


def _get_matched_tags(
    content: str,
    file_name: str,
    tags: List[str],
) -> List[str]:
    """
    Get human-readable descriptions for matched tags.
    
    Args:
        content: File content (raw text)
        file_name: Original filename
        tags: List of matched tags
        
    Returns:
        List of human-readable descriptions
    """
    text = f"{file_name} {content}".lower()
    matched = []
    
    for tag in tags:
        if tag in TAG_KEYWORDS:
            tag_keywords = TAG_KEYWORDS[tag]
            for keyword in tag_keywords.keys():
                if keyword in text:
                    label = KEYWORD_LABELS.get(keyword, keyword)
                    if label not in matched:
                        matched.append(label)
                    break  # Only need one match per tag
    
    return matched


# ============================================================================
# MAIN EXPLANATION GENERATOR
# ============================================================================

def generate_explanation(
    file_name: str,
    category: str,
    tags: List[str],
    content: Optional[str] = None,
    confidence: Optional[float] = None,
) -> str:
    """
    Generate an intelligent explanation for classification decision.
    
    The explanation connects to actual classification reasoning by:
    1. Identifying which keywords matched the category
    2. Explaining what the category means
    3. Showing confidence level (if provided)
    4. Referencing specific signals found
    
    Args:
        file_name: Name of the classified file
        category: Assigned category
        tags: Extracted tags
        content: Optional file content (for extracting matched keywords)
        confidence: Optional confidence score (0-1)
        
    Returns:
        Human-readable explanation of the classification
    """
    # Get category information
    cat_info = CATEGORY_EXPLANATIONS.get(
        category,
        CATEGORY_EXPLANATIONS["GENERAL"]
    )
    
    # Build explanation parts
    explanation_parts = []
    
    # Part 1: Main classification statement
    confidence_text = ""
    if confidence is not None:
        if confidence >= 0.8:
            confidence_text = " with high confidence"
        elif confidence >= 0.5:
            confidence_text = " with moderate confidence"
        else:
            confidence_text = " with low confidence"
    
    explanation_parts.append(
        f"File '{file_name}' classified as '{category}'{confidence_text}."
    )
    
    # Part 2: Category meaning
    explanation_parts.append(
        f"\n{cat_info['description'].capitalize()}: "
        f"{', '.join(cat_info['signals'])}."
    )
    
    # Part 3: Signals found (actual matching keywords)
    if content:
        matched_keywords = _get_matched_keywords(content, file_name, category)
        if matched_keywords:
            unique_keywords = list(dict.fromkeys(matched_keywords))  # Remove duplicates
            keywords_text = ", ".join(unique_keywords[:5])  # Show top 5
            explanation_parts.append(
                f"\nMatched signals: {keywords_text}."
            )
    
    # Part 4: Tags found
    if tags:
        if content:
            matched_tag_keywords = _get_matched_tags(content, file_name, tags)
            if matched_tag_keywords:
                tags_text = ", ".join(matched_tag_keywords[:4])  # Show top 4
                explanation_parts.append(
                    f"\nSpecialized topics detected: {tags_text}."
                )
        else:
            # Fallback if no content provided
            tags_text = ", ".join(tags)
            explanation_parts.append(
                f"\nDetected specialized topics: {tags_text}."
            )
    
    return "".join(explanation_parts)


# ============================================================================
# BACKWARD-COMPATIBLE API
# ============================================================================

def generate_explanation_simple(
    file_name: str,
    category: str,
    tags: List[str],
) -> str:
    """
    Simple explanation without content analysis (original behavior).
    
    Used for backward compatibility when content is not available.
    
    Args:
        file_name: Name of the classified file
        category: Assigned category
        tags: Extracted tags
        
    Returns:
        Basic explanation of the classification
    """
    return generate_explanation(file_name, category, tags)


# ============================================================================
# REVIEW: What Changed & Why
# ============================================================================
#
# ORIGINAL DESIGN PROBLEMS:
# ==========================
#
# 1. Generic and Static
#    - Hard-coded template: "[file] classified as [category]"
#    - Same explanation for all files in a category
#    - No variation or personalization
#    - Example: All PROGRAMMING files get: "...matched signals related to [tags]"
#
# 2. No Connection to Classification Logic
#    - Explanation didn't explain WHY it was classified
#    - Didn't reference actual keywords that matched
#    - Didn't show confidence level
#    - Users had no insight into classification reasoning
#
# 3. Limited Information
#    - Only showed tags, not which keywords triggered them
#    - Didn't explain what each category means
#    - Didn't differentiate between high/low confidence
#
# 4. Not Intelligent
#    - Reading explanation didn't help users understand classification
#    - No connection to the signals/keywords actually found
#    - Felt like a robot wrote it (because it was just string concatenation)
#
# 5. Hard to Debug
#    - If classification seemed wrong, explanation didn't help diagnose it
#    - No visibility into why keywords matched
#    - Could only see tags, not the underlying reasoning
#
#
# IMPROVEMENTS MADE:
# ==================
#
# 1. Connected to Classification Logic
#    - Explanation now extracts actual matching keywords from content
#    - Shows specific signals that triggered the classification
#    - Uses _get_matched_keywords() to find what actually matched
#    - Result: User can see the reasoning behind the classification
#
# 2. Category-Specific Explanations
#    - Created CATEGORY_EXPLANATIONS dict with meaningful descriptions
#    - Each category has:
#      * A description: What this category means
#      * Signals: Why files end up in this category
#    - Example: COLLEGE = "Academic coursework and university materials"
#    - Result: Users understand the category context
#
# 3. Intelligent Keyword Labeling
#    - Created KEYWORD_LABELS dict to make keywords readable
#    - "dbms" → "database management" (more human-friendly)
#    - "c++" → "C++" (proper formatting)
#    - "operating system" → "operating systems"
#    - Result: Explanation reads naturally, not like raw keywords
#
# 4. Confidence Level Integration
#    - Shows confidence categorically: "high", "moderate", "low"
#    - Maps 0-1 score to human-understandable levels
#    - Example: confidence 0.85 → "with high confidence"
#    - Result: Users know how certain the classification was
#
# 5. Multi-Part Structured Explanation
#    - Part 1: Main classification statement + confidence
#    - Part 2: What the category means (describes purpose)
#    - Part 3: Which signals were found (actual keywords)
#    - Part 4: Which specialized topics were detected (tags)
#    - Result: Explanation flows logically and explains reasoning
#
# 6. Information From Content
#    - Now accepts optional content parameter
#    - Analyzes content to find matched keywords
#    - Shows exactly which keywords triggered which category/tags
#    - Result: Explanation is grounded in actual file content
#
# 7. Better Readability
#    - Limited to showing top 5 keywords (not overwhelming)
#    - Removed duplicates from keyword lists
#    - Proper punctuation and capitalization
#    - Human-friendly phrasing
#    - Result: Users want to read the explanation
#
#
# EXAMPLES OF IMPROVED EXPLANATIONS:
# ===================================
#
# OLD (Generic):
#   "The file 'os_notes.pdf' was classified as 'COLLEGE' because it
#    matched signals related to: db, os, networks."
#
# NEW (Intelligent):
#   "File 'os_notes.pdf' classified as 'COLLEGE' with high confidence.
#
#    Academic coursework and university materials: course assignments
#    and exams, computer science fundamentals like OS, databases, and
#    networks, structured learning materials.
#
#    Matched signals: operating systems, databases, networking.
#
#    Specialized topics detected: operating systems, databases."
#
# The new explanation:
#   - Shows confidence level (helps user gauge reliability)
#   - Explains what COLLEGE category means
#   - Shows exact keywords that triggered the match
#   - References the tags detected (with human-readable names)
#
#
# CONNECTION TO CLASSIFICATION MODULE:
# =====================================
#
# The explanation now ties directly to classifier.py:
#
# 1. CATEGORY_KEYWORDS dict:
#    - Explainer extracts which keywords matched
#    - Converts raw keywords to readable labels
#    - Shows user which signals triggered classification
#
# 2. Confidence Scores:
#    - Pipeline now passes confidence from ClassificationResult
#    - Explanation shows confidence level
#    - User understands certainty of classification
#
# 3. Tags:
#    - Explainer looks up matched keywords for each tag
#    - Shows which specific keywords triggered each tag
#    - Tags aren't just names, their reasoning is explained
#
#
# IMPROVEMENTS IN PRACTICE:
# =========================
#
# Scenario: File with Python code
# --------------------------------
# Input: content="def fibonacci(n): ...", file_name="algo.py"
#
# OLD: "algo.py classified as PROGRAMMING because matched python."
#
# NEW: "File 'algo.py' classified as 'PROGRAMMING' with high confidence.
#
#       Software development and coding projects: programming languages
#       and code frameworks, software APIs and architecture.
#
#       Matched signals: python.
#
#       Specialized topics detected: coding."
#
# User learns:
#   - Why it matched (python keyword found)
#   - What PROGRAMMING category includes
#   - That code is also detected as a coding topic
#   - The classifier is confident (not guessing)
#
#
# Pipeline Integration:
# ---------------------
# Pipeline updated to pass content and confidence:
#
#   BEFORE:
#     explanation = generate_explanation(file_name, category, tags)
#
#   AFTER:
#     explanation = generate_explanation(
#         file_name, category, tags,
#         content=content,           # Now analyzes actual keywords
#         confidence=confidence      # Shows confidence level
#     )
#
#
# REMAINING LIMITATIONS:
# ======================
#
# 1. Still Keyword-Based
#    - Explanations depend on manual keyword lists
#    - Can't explain semantic/contextual matches
#    - Doesn't understand meaning, just keyword presence
#    - Mitigation: Could upgrade to embeddings later
#
# 2. No Multi-Category Support
#    - Explains only the top category
#    - If file matches multiple categories, only shows top one
#    - Mitigation: Could return top-3 with confidence scores
#
# 3. Keyword List Maintenance
#    - Human must maintain KEYWORD_LABELS mapping
#    - If keywords change, labels must be updated
#    - Not scalable for large keyword lists
#    - Mitigation: Could auto-generate friendly names from keywords
#
# 4. No Reasoning for Thresholds
#    - Doesn't explain why keyword was included/excluded
#    - Doesn't show weights applied to keywords
#    - Mitigation: Could show weight details in debug mode
#
# 5. Limited Language Support
#    - Explanations are English-only
#    - Labels and category descriptions hardcoded
#    - Mitigation: Could use i18n/translation system
#
#
# RECOMMENDED NEXT STEPS:
# =======================
#
# 1. Add Multi-Category Support (Low-Medium Effort)
#    - Show top 3 categories with confidence scores
#    - "Primary: CLASS (0.92), Secondary: PROGRAM (0.45)"
#    - Help users understand close matches
#
# 2. Add Keyword Weight Visibility (Low Effort)
#    - Show which keywords were strong signals
#    - "High-signal keywords: exam (2.5x), algorithm (1.5x)"
#    - Help users understand what was important
#
# 3. Auto-Generate Friendly Labels (Medium Effort)
#    - Convert technical keywords to natural language
#    - "dbms" → "database management systems"
#    - "c++" → "C plus plus"
#    - Reduce maintenance burden
#
# 4. Add Explanation Confidence (Low Effort)
#    - Show if explanation is certain or uncertain
#    - "Confidence in explanation: High (3 matching keywords)"
#    - "Confidence in explanation: Low (only 1 keyword matched)"
#
# 5. Debug Mode Explanations (Medium Effort)
#    - Show all matching keywords, not just top 5
#    - Show keyword weights
#    - Show score calculations
#    - Helpful for troubleshooting misclassifications
#
# 6. Personalized Explanations (High Effort)
#    - Track user feedback on explanations
#    - Learn which keywords are most helpful
#    - Customize explanation based on category
#    - Improve over time
# ============================================================================
