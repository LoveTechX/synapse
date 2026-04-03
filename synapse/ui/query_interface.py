"""
Conversational CLI interface for querying the memory system.

Provides an interactive prompt for users to search stored files with
conversational context, filtering, and result refinement. Supports
follow-up queries that refine previous results without new searches.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from synapse.models.file_model import FileModel
from synapse.storage.memory import get_memory


# Configure logging
logger = logging.getLogger(__name__)

# Exit commands
EXIT_COMMANDS = {"exit", "quit", "q"}

# Display settings
SEPARATOR = "=" * 80
RESULT_SEPARATOR = "-" * 80
MAX_EXPLANATION_LENGTH = 100
TOP_RESULTS_FOR_IMPORTANCE = 5

# Query type keywords
RECENT_KEYWORDS = {"recent", "latest", "new", "recent"}
CATEGORY_KEYWORDS = {"only", "filter", "category"}
EXPAND_KEYWORDS = {"more", "expand", "show more"}


# ============================================================================
# QUERY CONTEXT: Maintains state across multiple queries
# ============================================================================

@dataclass
class QueryContext:
    """
    Maintain conversational context across multiple queries.
    
    Stores:
    - Last search query and results
    - Applied filters (category, date range, etc.)
    - Allows follow-up queries to refine previous results
    """
    
    last_query: str = ""
    last_results: List[FileModel] = field(default_factory=list)
    applied_filters: Dict[str, str] = field(default_factory=dict)
    
    def reset(self) -> None:
        """Reset context for new search."""
        self.last_query = ""
        self.last_results = []
        self.applied_filters.clear()
    
    def update(self, query: str, results: List[FileModel]) -> None:
        """
        Update context with new search results.
        
        Args:
            query: The search query
            results: List of FileModel results
        """
        self.last_query = query
        self.last_results = results
        self.applied_filters.clear()
    
    def has_results(self) -> bool:
        """Check if context has previous results."""
        return len(self.last_results) > 0


# ============================================================================
# FORMATTING UTILITIES
# ============================================================================

def _truncate_text(text: str, max_length: int) -> str:
    """
    Truncate text to max_length, preserving word boundaries.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including ellipsis
        
    Returns:
        Truncated text with ... appended if needed
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length - 3].rsplit(' ', 1)[0]
    return truncated + "..."


def _format_result(result: FileModel, index: int) -> str:
    """
    Format a single search result for display.
    
    Args:
        result: FileModel to display
        index: Result number (1-indexed)
        
    Returns:
        Formatted result string
    """
    # Get score (default to 0.0 if not set)
    score = getattr(result, 'score', 0.0)
    
    # Build the output lines
    lines = [
        f"\n[{index}] {result.name}",
        f"    Category: {result.category}",
        f"    Relevance: {score:.2f}",
    ]
    
    # Add explanation if available
    if result.explanation:
        explanation = _truncate_text(result.explanation, MAX_EXPLANATION_LENGTH)
        lines.append(f"    Summary: {explanation}")
    
    return "\n".join(lines)


def _format_results_list(results: List[FileModel], applied_filters: Optional[Dict[str, str]] = None) -> str:
    """
    Format multiple search results for display.
    
    Args:
        results: List of FileModel objects
        applied_filters: Dict of filters that were applied (for display)
        
    Returns:
        Formatted results string ready for printing
    """
    if not results:
        return "No files found. Try a different query."
    
    lines = [f"\nFound {len(results)} file(s):\n"]
    
    # Show applied filters if any
    if applied_filters:
        filter_text = " + ".join([f"{k}: {v}" for k, v in applied_filters.items()])
        lines.append(f"(Filters applied: {filter_text})\n")
    
    for idx, result in enumerate(results, 1):
        lines.append(_format_result(result, idx))
    
    return "\n".join(lines)


def _format_welcome() -> str:
    """
    Format welcome message.
    
    Returns:
        Welcome message
    """
    return (
        f"\n{SEPARATOR}\n"
        f"Synapse Memory Query Interface (Conversational)\n"
        f"{SEPARATOR}\n"
        f"Commands:\n"
        f"  [query]  - Search for files (e.g., 'Python security bug')\n"
        f"  recent   - Show recent files\n"
        f"  only [category] - Filter by category (use with previous search)\n"
        f"  more     - Expand previous results\n"
        f"  exit     - Exit the interface\n"
        f"\n"
    )


# ============================================================================
# QUERY TYPE DETECTION
# ============================================================================

def _detect_query_type(query: str, context: QueryContext) -> str:
    """
    Detect the type of query (new search, filter, expand, etc.).
    
    Args:
        query: User query string
        context: Current query context
        
    Returns:
        Query type: 'new', 'recent', 'category', 'expand', or 'refine'
    """
    query_lower = query.lower()
    
    # Check for recent/latest query
    if any(keyword in query_lower for keyword in RECENT_KEYWORDS):
        return "recent"
    
    # Check for category/filter query
    if any(keyword in query_lower for keyword in CATEGORY_KEYWORDS):
        return "category"
    
    # Check for expand/more query
    if any(keyword in query_lower for keyword in EXPAND_KEYWORDS):
        return "expand"
    
    # Default: new search
    return "new"


# ============================================================================
# FILTERING LOGIC
# ============================================================================

def _filter_by_recent(results: List[FileModel], limit: int = 10) -> tuple[List[FileModel], Dict[str, str]]:
    """
    Filter results to show most recent files.
    
    Args:
        results: List of FileModel objects
        limit: Maximum number to return
        
    Returns:
        Tuple of (filtered_results, applied_filters_dict)
    """
    try:
        # Sort by created_at in descending order (newest first)
        sorted_results = sorted(
            results,
            key=lambda f: f.created_at,
            reverse=True
        )
        
        filtered = sorted_results[:limit]
        filters = {"recent": f"top {len(filtered)}"}
        
        logger.debug("Filtered by recent: %d results", len(filtered))
        return filtered, filters
    except Exception as e:
        logger.warning("Failed to filter by recent: %s", str(e))
        return results, {}


def _filter_by_category(results: List[FileModel], category: str) -> tuple[List[FileModel], Dict[str, str]]:
    """
    Filter results by category.
    
    Args:
        results: List of FileModel objects
        category: Category to filter by (case-insensitive)
        
    Returns:
        Tuple of (filtered_results, applied_filters_dict)
    """
    category_lower = category.lower()
    
    filtered = [
        r for r in results
        if r.category.lower() == category_lower
    ]
    
    filters = {"category": category} if filtered else {}
    logger.debug("Filtered by category '%s': %d results", category, len(filtered))
    return filtered, filters


def _filter_by_type(results: List[FileModel], file_type: str) -> tuple[List[FileModel], Dict[str, str]]:
    """
    Filter results by file extension.
    
    Args:
        results: List of FileModel objects
        file_type: Extension to filter by (e.g., '.py', 'py')
        
    Returns:
        Tuple of (filtered_results, applied_filters_dict)
    """
    # Normalize extension
    if not file_type.startswith("."):
        file_type = f".{file_type}"
    
    file_type = file_type.lower()
    
    filtered = [
        r for r in results
        if Path(r.name).suffix.lower() == file_type
    ]
    
    filters = {"type": file_type} if filtered else {}
    logger.debug("Filtered by type '%s': %d results", file_type, len(filtered))
    return filtered, filters


def _extract_category_from_query(query: str) -> Optional[str]:
    """
    Extract category name from query like 'only SOURCE_CODE' or 'category: REFERENCE'.
    
    Args:
        query: User query string
        
    Returns:
        Category name if found, None otherwise
    """
    words = query.split()
    
    # Look for patterns like "only SOURCE_CODE" or "filter REFERENCE"
    for i, word in enumerate(words):
        if word.lower() in {"only", "filter", "category"} and i + 1 < len(words):
            return words[i + 1].upper()
    
    return None


# ============================================================================
# QUERY EXECUTION
# ============================================================================

def _execute_search(query: str) -> List[FileModel]:
    """
    Execute a search query and return results.
    
    Args:
        query: User search query
        
    Returns:
        List of FileModel results (ranked by relevance)
    """
    memory = get_memory()
    
    try:
        results = memory.search(query)
        logger.info("Query executed: '%s' → %d results", query, len(results))
        return results
    except Exception as e:
        logger.error("Search failed for query '%s': %s", query, str(e))
        return []


def _update_result_importance(results: List[FileModel]) -> None:
    """
    Update importance scores for top returned files.
    
    Only updates the top N results to avoid noise from lower-ranked results.
    Called after user sees results to track which files are being
    accessed through search.
    
    Args:
        results: List of FileModel objects from search
    """
    memory = get_memory()
    
    # Only update top results
    top_results = results[:TOP_RESULTS_FOR_IMPORTANCE]
    
    for result in top_results:
        if result.id is not None:
            try:
                memory.update_importance(result.id)
                logger.debug("Updated importance for file ID %d", result.id)
            except Exception as e:
                logger.warning("Failed to update importance for file ID %d: %s", result.id, str(e))


# ============================================================================
# INTERACTIVE PROMPT
# ============================================================================

def run_query_interface() -> None:
    """
    Run the interactive conversational query interface.
    
    Continuously prompts user for search queries and displays results.
    Maintains context across queries to support conversational refinement:
    
    - NEW QUERY: User enters a search term → calls memory.search()
    - RECENT: Sorts previous results by date
    - FILTER: Applies category/type filter to previous results
    - EXPAND: Shows more results from previous search
    
    Type 'exit' or 'quit' to stop.
    
    Features:
    - Conversational context across multiple queries
    - Result filtering without new searches
    - Ranked results with relevance scores
    - File categories and brief explanations
    - Automatic importance tracking for top results
    - Error handling for invalid input
    - Clean, readable output formatting
    
    Example:
        >>> run_query_interface()
        
        Query: authentication failure
        Found 2 file(s):
        [1] login_handler.py (Category: SOURCE_CODE, Relevance: 0.87)
        [2] security_audit.md (Category: REFERENCE, Relevance: 0.62)
        
        Query: only SOURCE_CODE
        Found 1 file(s):
        (Filters applied: category: SOURCE_CODE)
        [1] login_handler.py (Category: SOURCE_CODE, Relevance: 0.87)
        
        Query: exit
        Goodbye!
    """
    logger.info("Query interface started (conversational mode)")
    print(_format_welcome())
    
    context = QueryContext()
    
    try:
        while True:
            try:
                # Prompt for input
                query = input("Query: ").strip()
                
                # Check for exit commands
                if query.lower() in EXIT_COMMANDS:
                    print("Goodbye!")
                    logger.info("User exited query interface")
                    break
                
                # Validate input
                if not query:
                    print("Please enter a search query.\n")
                    continue
                
                # Detect query type
                query_type = _detect_query_type(query, context)
                results = []
                applied_filters = {}
                
                # Process based on query type
                if query_type == "new":
                    # New search: call memory.search()
                    logger.info("New search: '%s'", query)
                    results = _execute_search(query)
                    context.update(query, results)
                    applied_filters = {}
                
                elif query_type == "recent":
                    # Recent filter: apply to last results
                    if not context.has_results():
                        print("No previous search. Please enter a search query first.\n")
                        continue
                    
                    logger.info("Filtering recent: %d results", len(context.last_results))
                    results, applied_filters = _filter_by_recent(context.last_results)
                    context.applied_filters.update(applied_filters)
                
                elif query_type == "category":
                    # Category filter: extract category and filter
                    if not context.has_results():
                        print("No previous search. Please enter a search query first.\n")
                        continue
                    
                    category = _extract_category_from_query(query)
                    if category:
                        logger.info("Filtering by category: '%s'", category)
                        results, applied_filters = _filter_by_category(context.last_results, category)
                        context.applied_filters.update(applied_filters)
                    else:
                        print("Could not parse category. Try: 'only SOURCE_CODE' or 'filter REFERENCE'\n")
                        continue
                
                elif query_type == "expand":
                    # Expand: show more results (return more than initial limit)
                    if not context.has_results():
                        print("No previous search. Please enter a search query first.\n")
                        continue
                    
                    logger.info("Expanding results: %d available", len(context.last_results))
                    results = context.last_results
                    applied_filters = {"expand": "showing all"}
                
                # No results after processing
                if not results:
                    print("No files found. Try a different query.\n")
                    continue
                
                # Display results with applied filters
                print(_format_results_list(results, applied_filters if applied_filters else None))
                print()
                
                # Update importance for top results
                if results:
                    _update_result_importance(results)
                
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                print("\n\nInterrupted. Goodbye!")
                logger.info("Query interface interrupted by user")
                break
            except Exception as e:
                # Catch any unexpected errors and continue
                logger.error("Error processing query: %s", str(e))
                print(f"Error: {str(e)}\nPlease try again.\n")
                
    except EOFError:
        # Handle end of input (e.g., piped input)
        print("\nEnd of input. Goodbye!")
        logger.info("Query interface ended (EOF)")


# ============================================================================
# ENTRY POINT FOR TESTING
# ============================================================================

if __name__ == "__main__":
    # Configure basic logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    run_query_interface()
