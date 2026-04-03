"""
QUICK START: Memory System Integration Guide

Start Here for Fast Integration with Synapse AI Pipeline
"""

# ============================================================================
# 1. INITIALIZE IN PIPELINE
# ============================================================================

# In synapse/core/pipeline.py or main application startup:

from synapse.storage.memory import get_memory, build_indexes

def initialize_pipeline():
    """Called once at application startup."""
    memory = get_memory()  # Get singleton instance
    
    # If you have initial files to index:
    # memory.build_indexes(initial_files_list)
    # Otherwise, files are indexed as they come in


# ============================================================================
# 2. STORE FILES AS THEY'RE PROCESSED
# ============================================================================

# In your pipeline processing loop:

def process_file(file_model):
    """Process a single file and store in memory."""
    from synapse.storage.memory import get_memory
    
    memory = get_memory()
    
    # Your existing processing...
    file_model = classify(file_model)  # Or your processing steps
    
    # Store in memory (indexes are updated automatically)
    memory.store_memory(file_model)
    
    return file_model


# ============================================================================
# 3. SEARCH FILES (User Query)
# ============================================================================

# In your UI/API endpoint:

def search_files(user_query: str):
    """Find relevant files based on user query."""
    from synapse.storage.memory import get_memory
    
    memory = get_memory()
    
    results = memory.search(user_query)
    
    # Optionally: track access (increases importance)
    for file in results:
        if file.id:
            memory.update_importance(file.id, delta=0.05)
    
    return results


# ============================================================================
# 4. API ENDPOINT EXAMPLE (FastAPI)
# ============================================================================

from fastapi import FastAPI
from typing import List

app = FastAPI()

@app.get("/memory/search")
async def api_search(query: str) -> List[dict]:
    """Search memory system via HTTP."""
    from synapse.storage.memory import get_memory
    
    memory = get_memory()
    results = memory.search(query)
    
    # Convert to JSON-safe format
    return [file.to_dict() for file in results]


# ============================================================================
# 5. COMMON PATTERNS
# ============================================================================

# Pattern A: Search → Process → Report
def search_and_summarize(query: str) -> str:
    from synapse.storage.memory import get_memory
    
    memory = get_memory()
    results = memory.search(query)
    
    if not results:
        return f"No files found for: {query}"
    
    summary = f"Found {len(results)} relevant files:\n"
    for file in results[:5]:  # Top 5
        summary += f"  - {file.name} ({file.category})\n"
    
    return summary


# Pattern B: Batch Import
def import_files_batch(file_list: List) -> None:
    from synapse.storage.memory import get_memory
    
    memory = get_memory()
    
    # Build indexes all at once (better performance)
    memory.build_indexes(file_list)


# Pattern C: Update File
def update_file(file_id: int, updated_model) -> None:
    from synapse.storage.memory import get_memory
    
    memory = get_memory()
    
    # Simply store the updated version (overwrites in dict)
    memory.store_memory(updated_model)


# ============================================================================
# 6. CONFIGURATION & TUNING
# ============================================================================

# Adjust scoring weights in synapse/storage/memory.py
# In MemorySystem.rank_results():

# Current weights:
#   keyword_match * 0.5      ← Increase to 0.6 if keyword precision matters most
#   tag_match * 0.2          ← Decrease to 0.1 if tags are unreliable
#   category_match * 0.1     ← Increase to 0.2 if category is critical
#   importance * 0.1         ← Increase to 0.15 to favor frequently accessed
#   recency * 0.1            ← Increase to 0.2 to prefer recent files

# Example: If you want to prioritize important/frequently-used files:
# Change: importance * 0.1 → importance * 0.2
# Change: keyword_match * 0.5 → keyword_match * 0.4


# ============================================================================
# 7. MONITORING
# ============================================================================

def memory_stats() -> dict:
    """Get memory system statistics."""
    from synapse.storage.memory import get_memory
    
    memory = get_memory()
    
    return {
        "total_files": len(memory.files),
        "total_keywords": len(memory.keyword_index),
        "total_categories": len(memory.category_index),
        "total_tags": len(memory.tag_index),
        "avg_importance": sum(memory.importance.values()) / max(len(memory.importance), 1),
    }


# ============================================================================
# 8. TESTING
# ============================================================================

def test_memory_system():
    """Run basic memory system tests."""
    from synapse.storage.memory import reset_memory, get_memory
    
    reset_memory()
    memory = get_memory()
    
    # Create test file
    test_file = FileModel(
        id=1,
        name="test.py",
        path="test.py",
        content="Test content with keywords",
        category="test",
        tags=["test_tag"],
        explanation="Test"
    )
    
    # Test store
    memory.store_memory(test_file)
    assert len(memory.files) == 1, "File should be stored"
    
    # Test search
    results = memory.search("test keywords")
    assert len(results) > 0, "Should find test file"
    
    # Test importance
    memory.update_importance(1, delta=0.5)
    assert memory.importance[1] > 1.0, "Importance should increase"
    
    print("✓ All memory system tests passed")


# ============================================================================
# 9. TROUBLESHOOTING
# ============================================================================

"""
ISSUE: Search returns no results
  → Check: Did you call memory.store_memory() for the files you're searching?
  → Check: Is your query using words from file content/tags?
  → Solution: Add more files or use broader query terms

ISSUE: Same file appears in every search
  → Problem: File importance is too high
  → Solution: Call memory.importance[file_id] = 1.0 to reset

ISSUE: Results score is always 0.5
  → Problem: Only category is matching
  → Solution: Check keyword extraction (ensure content has meaningful words)

ISSUE: Memory system slow with 10k files
  → Problem: Python dict lookup is O(1) but can have overhead
  → Solution: Consider persistence layer to reduce rebuild time
  → Future: Move to SQLite or Elasticsearch for larger scale
"""

# ============================================================================
# 10. NEXT STEPS
# ============================================================================

"""
After this basic integration:

1. Add persistence (JSON export/import during shutdown/startup)
   See: MEMORY_SYSTEM_REVIEW.md → Near-term improvements

2. Monitor query patterns in logs
   This tells you if searches are working well

3. Add domain-specific synonyms
   Edit SYNONYM_MAP in memory.py based on your AI's vocabulary

4. Consider importance decay
   Prevent old files from staying important forever

5. Optional: Add embeddings later
   Won't break this simple system, just enhance it

For full details, see: MEMORY_SYSTEM_REVIEW.md
For examples, run: python synapse/storage/memory_examples.py
"""
