"""
Intelligent memory system for Synapse AI.

Provides STORE, INDEX, and RETRIEVE capabilities for file-based memory.
Uses in-memory indexes with simple ranking based on multiple relevance factors.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from synapse.models.file_model import FileModel


# ============================================================================
# CONSTANTS & CONFIG
# ============================================================================

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "is", "was", "are", "be", "have", "has", "had", "do", "does",
    "did", "will", "would", "could", "should", "may", "might", "must",
    "can", "this", "that", "these", "those", "i", "you", "he", "she", "it",
    "we", "they", "what", "which", "who", "when", "where", "why", "how"
}

SYNONYM_MAP = {
    "file": ["document", "artifact", "resource"],
    "code": ["source", "script", "program"],
    "error": ["bug", "issue", "problem", "exception"],
    "feature": ["functionality", "capability"],
    "test": ["check", "verify", "validation"],
}


# ============================================================================
# MEMORY STATE (Global indexes)
# ============================================================================

class MemorySystem:
    """
    In-memory intelligence system for file storage, indexing, and retrieval.
    
    Maintains multiple indexes for fast lookup and rich ranking:
    - keyword_index: maps keywords to files
    - category_index: maps categories to files
    - tag_index: maps tags to files
    """

    def __init__(self):
        """Initialize empty memory system."""
        self.files: Dict[int, FileModel] = {}  # id -> FileModel
        self.keyword_index: Dict[str, List[FileModel]] = {}
        self.category_index: Dict[str, List[FileModel]] = {}
        self.tag_index: Dict[str, List[FileModel]] = {}
        
        # Track file metadata not in FileModel
        self.importance: Dict[int, float] = {}  # id -> importance score
        self.last_accessed: Dict[int, str] = {}  # id -> ISO timestamp

    def store_memory(self, file_model: FileModel) -> None:
        """
        Store a file in memory and initialize tracking metadata.
        
        Extracts keywords and updates all indexes.
        
        Args:
            file_model: FileModel instance to store
        """
        if file_model.id is None:
            raise ValueError("FileModel must have an id for storage")
        
        # Extract keywords from content and tags
        keywords = extract_keywords(file_model.content, file_model.tags)
        
        # Store extended file model in local dict (simulating persistence)
        file_model.keywords = keywords  # type: ignore
        self.files[file_model.id] = file_model
        
        # Initialize importance and access tracking
        self.importance[file_model.id] = 1.0
        self.last_accessed[file_model.id] = file_model.created_at
        
        # Update indexes
        self._update_indexes(file_model)

    def _update_indexes(self, file_model: FileModel) -> None:
        """
        Internal: Update all indexes when a file is stored or updated.
        
        Args:
            file_model: FileModel to index
        """
        file_id = file_model.id
        
        # Index by keywords
        keywords = getattr(file_model, 'keywords', [])
        for keyword in keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = []
            if file_model not in self.keyword_index[keyword]:
                self.keyword_index[keyword].append(file_model)
        
        # Index by category
        category = file_model.category.lower()
        if category not in self.category_index:
            self.category_index[category] = []
        if file_model not in self.category_index[category]:
            self.category_index[category].append(file_model)
        
        # Index by tags
        for tag in file_model.tags:
            tag_lower = tag.lower()
            if tag_lower not in self.tag_index:
                self.tag_index[tag_lower] = []
            if file_model not in self.tag_index[tag_lower]:
                self.tag_index[tag_lower].append(file_model)

    def build_indexes(self, files: List[FileModel]) -> None:
        """
        Build all indexes from a list of files.
        
        Called during initialization or batch import.
        Clears existing indexes and rebuilds them.
        
        Args:
            files: List of FileModel instances to index
        """
        # Clear existing indexes
        self.keyword_index.clear()
        self.category_index.clear()
        self.tag_index.clear()
        
        # Process each file
        for file_model in files:
            if file_model.id is not None:
                # Extract and store keywords
                keywords = extract_keywords(file_model.content, file_model.tags)
                file_model.keywords = keywords  # type: ignore
                
                # Store in files dict
                self.files[file_model.id] = file_model
                
                # Initialize importance if not present
                if file_model.id not in self.importance:
                    self.importance[file_model.id] = 1.0
                if file_model.id not in self.last_accessed:
                    self.last_accessed[file_model.id] = file_model.created_at
                
                # Update indexes
                self._update_indexes(file_model)

    def search(self, query: str) -> List[FileModel]:
        """
        Search memory with a natural query and return ranked results.
        
        Process:
        1. Normalize query to keywords
        2. Expand query using synonym map
        3. Fetch candidate files from indexes
        4. Rank by relevance
        5. Return sorted results
        
        Args:
            query: Natural language search query
            
        Returns:
            List of FileModel objects, ranked by relevance (highest first)
        """
        if not query.strip():
            return []
        
        # Step 1: Normalize query to keywords
        query_terms = _normalize_query(query)
        
        if not query_terms:
            return []
        
        # Step 2: Expand query with synonyms
        expanded_terms = _expand_query(query_terms)
        
        # Step 3: Fetch candidate files from all indexes
        candidates: Set[int] = set()
        
        # Candidates from keyword matches
        for term in expanded_terms:
            for file_model in self.keyword_index.get(term, []):
                if file_model.id is not None:
                    candidates.add(file_model.id)
        
        # Candidates from tag matches
        for term in query_terms:  # Use original terms for tags
            for file_model in self.tag_index.get(term.lower(), []):
                if file_model.id is not None:
                    candidates.add(file_model.id)
        
        # Candidates from category matches
        for term in query_terms:
            for file_model in self.category_index.get(term.lower(), []):
                if file_model.id is not None:
                    candidates.add(file_model.id)
        
        # Convert to FileModel list
        candidate_files = [self.files[fid] for fid in candidates if fid in self.files]
        
        # Step 4 & 5: Rank and return sorted results
        self.rank_results(candidate_files, query_terms, expanded_terms)
        candidate_files.sort(key=lambda f: f.score, reverse=True)  # type: ignore
        
        return candidate_files

    def rank_results(
        self,
        files: List[FileModel],
        query_terms: List[str],
        expanded_terms: Optional[List[str]] = None
    ) -> None:
        """
        Rank search results by computing relevance score for each file.
        
        Scoring formula:
            score = (keyword_match * 0.5) +
                    (tag_match * 0.2) +
                    (category_match * 0.1) +
                    (importance * 0.1) +
                    (recency * 0.1)
        
        Stores score in file_model.score for sorting.
        
        Args:
            files: List of FileModel candidates to rank
            query_terms: Normalized query keywords
            expanded_terms: Expanded query terms (with synonyms). 
                           If None, uses query_terms.
        """
        if expanded_terms is None:
            expanded_terms = query_terms
        
        for file_model in files:
            if file_model.id is None:
                continue
            
            keywords = getattr(file_model, 'keywords', [])
            
            # 1. Keyword match: overlap count normalized
            keyword_overlap = sum(
                1 for term in expanded_terms
                if term in keywords
            )
            keyword_match = min(keyword_overlap / max(len(expanded_terms), 1), 1.0)
            
            # 2. Tag match: overlap count normalized
            tags_lower = [tag.lower() for tag in file_model.tags]
            tag_overlap = sum(
                1 for term in query_terms
                if term in tags_lower
            )
            tag_match = min(tag_overlap / max(len(query_terms), 1), 1.0)
            
            # 3. Category match: binary (0 or 1)
            category_match = 1.0 if any(
                term in file_model.category.lower()
                for term in query_terms
            ) else 0.0
            
            # 4. Importance: stored value, normalized to [0, 1]
            importance_score = min(
                self.importance.get(file_model.id, 1.0) / 5.0, 1.0
            )
            
            # 5. Recency: how recently was file created
            recency_score = _compute_recency(file_model.created_at)
            
            # Compute final score
            score = (
                keyword_match * 0.5 +
                tag_match * 0.2 +
                category_match * 0.1 +
                importance_score * 0.1 +
                recency_score * 0.1
            )
            
            # Store score on file_model for sorting
            file_model.score = score  # type: ignore

    def update_importance(self, file_id: int, delta: float = 0.1) -> None:
        """
        Increase importance score when a file is accessed or used.
        
        Updates last_accessed timestamp to now.
        
        Args:
            file_id: ID of file to update
            delta: Amount to increase importance (default 0.1)
        """
        if file_id not in self.files:
            return
        
        # Increase importance
        current = self.importance.get(file_id, 1.0)
        self.importance[file_id] = current + delta
        
        # Update access time
        now = datetime.now(timezone.utc).isoformat()
        self.last_accessed[file_id] = now


# ============================================================================
# PUBLIC FUNCTIONS (Used by pipeline)
# ============================================================================

def extract_keywords(content: str, tags: List[str]) -> List[str]:
    """
    Extract meaningful keywords from content and tags.
    
    Process:
    1. Convert to lowercase
    2. Remove stopwords
    3. Split into words
    4. Include all tags
    5. Return unique list
    
    Args:
        content: Raw text content to extract from
        tags: List of existing tags (all included in output)
        
    Returns:
        List of unique, meaningful keywords
    """
    keywords: Set[str] = set()
    
    # Add tags (normalized)
    for tag in tags:
        keywords.add(tag.lower())
    
    # Split content and filter
    words = content.lower().split()
    for word in words:
        # Basic cleanup: remove punctuation
        clean_word = word.strip(".,!?;:()[]{}\"'")
        
        # Skip if empty, stopword, or too short
        if clean_word and clean_word not in STOPWORDS and len(clean_word) > 2:
            keywords.add(clean_word)
    
    return sorted(list(keywords))


def _normalize_query(query: str) -> List[str]:
    """
    Normalize a search query to lowercase keywords.
    
    Args:
        query: Raw query string
        
    Returns:
        List of normalized keywords
    """
    words = query.lower().split()
    terms = []
    
    for word in words:
        clean = word.strip(".,!?;:()[]{}\"'")
        if clean and clean not in STOPWORDS and len(clean) > 1:
            terms.append(clean)
    
    return terms


def _expand_query(query_terms: List[str]) -> List[str]:
    """
    Expand query with synonyms from mapping.
    
    Args:
        query_terms: List of normalized query terms
        
    Returns:
        Expanded list including synonyms
    """
    expanded = list(query_terms)
    
    for term in query_terms:
        if term in SYNONYM_MAP:
            expanded.extend(SYNONYM_MAP[term])
    
    return expanded


def _compute_recency(created_at: str) -> float:
    """
    Compute recency score based on file creation time.
    
    Recent files (< 7 days) score higher.
    Very old files (> 90 days) score lowest.
    
    Args:
        created_at: ISO format timestamp string
        
    Returns:
        Score between 0.0 and 1.0
    """
    try:
        file_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        age_days = (now - file_time).days
        
        # Linear decay: 1.0 at 0 days, 0.0 at 90 days
        recency = max(0.0, 1.0 - (age_days / 90.0))
        return recency
    except (ValueError, AttributeError):
        # Default to medium recency if parsing fails
        return 0.5


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Global memory system instance
_memory: Optional[MemorySystem] = None


def get_memory() -> MemorySystem:
    """Get or create the global memory system instance."""
    global _memory
    if _memory is None:
        _memory = MemorySystem()
    return _memory


def reset_memory() -> None:
    """Reset the global memory system (useful for testing)."""
    global _memory
    _memory = None
