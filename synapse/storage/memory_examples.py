"""
USAGE EXAMPLES: Memory System for Synapse AI

Quick integration guide and practical examples.
"""

from synapse.models.file_model import FileModel
from synapse.storage.memory import get_memory, extract_keywords


# ============================================================================
# BASIC USAGE
# ============================================================================

def example_1_store_and_search():
    """Store files and search with simple queries."""
    memory = get_memory()
    
    # Create sample FileModel
    file1 = FileModel(
        id=1,
        name="api_handler.py",
        path="src/handlers/api_handler.py",
        content="Handles REST API endpoints. Validates requests. Returns JSON responses.",
        category="api",
        tags=["backend", "rest", "handlers"],
        explanation="Module for handling API requests"
    )
    
    file2 = FileModel(
        id=2,
        name="database.py",
        path="src/storage/database.py",
        content="Database connection and query execution. Supports PostgreSQL MySQL.",
        category="database",
        tags=["storage", "database", "sql"],
        explanation="Database access layer"
    )
    
    # Store files
    memory.store_memory(file1)
    memory.store_memory(file2)
    
    # Search
    results = memory.search("REST API handlers")
    print(f"Found {len(results)} results for 'REST API handlers'")
    for file in results:
        print(f"  - {file.name} (score: {getattr(file, 'score', 0):.2f})")
    
    # Expected: file1 ranked higher (more keyword matches)


def example_2_batch_indexing():
    """Build indexes from multiple files at once."""
    memory = get_memory()
    
    files = [
        FileModel(
            id=10 + i,
            name=f"module_{i}.py",
            path=f"src/modules/module_{i}.py",
            content=f"Module {i} handles specific functionality",
            category="module",
            tags=["python", "component"],
            explanation=f"Component {i}"
        )
        for i in range(5)
    ]
    
    # Build all indexes at once
    memory.build_indexes(files)
    print(f"Indexed {len(files)} files successfully")


def example_3_importance_tracking():
    """Track file importance as they're accessed."""
    memory = get_memory()
    
    # Setup
    file_model = FileModel(
        id=100,
        name="utils.py",
        path="src/utils.py",
        content="Utility functions for common operations",
        category="utilities",
        tags=["util"],
        explanation="Utilities"
    )
    memory.store_memory(file_model)
    
    # Simulate access pattern: file is accessed 5 times
    for _ in range(5):
        memory.update_importance(100, delta=0.5)
    
    # Now when searching, this file will score higher
    results = memory.search("utility functions")
    print(f"Importance of utils.py: {memory.importance.get(100, 1.0):.1f}")


def example_4_keyword_extraction():
    """Show how keywords are extracted from content."""
    content = """
    This Python module implements authentication and authorization.
    It validates user credentials and manages permission levels.
    Supports OAuth2 and JWT token authentication methods.
    """
    
    tags = ["security", "auth"]
    
    keywords = extract_keywords(content, tags)
    print("Extracted keywords:")
    print(keywords)
    # Expected: includes "python", "authentication", "authorization", "credentials",
    #           "oauth2", "jwt", plus tag-derived "security", "auth"
    #           Excludes stopwords like "this", "and", "it"


def example_5_advanced_ranking():
    """Show how different file properties affect ranking."""
    memory = get_memory()
    
    # File A: Many keyword matches, low importance
    file_a = FileModel(
        id=201,
        name="old_api.py",
        path="src/old_api.py",
        content="REST API endpoints for user management error handling",
        category="api",
        tags=["deprecated", "api"],
        explanation="Old API"
    )
    
    # File B: Fewer keyword matches, high importance (accessed often)
    file_b = FileModel(
        id=202,
        name="main_api.py",
        path="src/main_api.py",
        content="Main API routing",
        category="api",
        tags=["current", "api"],
        explanation="Main API"
    )
    
    memory.store_memory(file_a)
    memory.store_memory(file_b)
    
    # Make file_b more important
    for _ in range(20):
        memory.update_importance(202, delta=0.2)
    
    # Search: both match "api" but file_b ranks higher due to importance
    results = memory.search("REST API error handling")
    print("\nRanking for 'REST API error handling':")
    for i, file in enumerate(results, 1):
        print(f"{i}. {file.name} (score: {getattr(file, 'score', 0):.3f})")
    # File A likely ranks first (more keywords), but File B's score is boosted


def example_6_no_results_handling():
    """Handle edge case: no results found."""
    memory = get_memory()
    
    file_model = FileModel(
        id=300,
        name="example.py",
        path="src/example.py",
        content="Example code",
        category="examples",
        tags=["demo"],
        explanation="Demo"
    )
    memory.store_memory(file_model)
    
    # Query with no matching keywords
    results = memory.search("obscure query that doesnt exist")
    if not results:
        print("No results found. Consider:")
        print("  - Expanding the query")
        print("  - Checking spelling")
        print("  - Adding more files to memory")


def example_7_integration_with_pipeline():
    """Example: Integration with Synapse AI pipeline."""
    from synapse.core.pipeline import Pipeline
    
    # Pipeline processes files and passes them to memory
    def process_files_with_memory(file_list):
        memory = get_memory()
        
        # Build initial index
        memory.build_indexes(file_list)
        
        # Later in pipeline: accept user query and search
        user_query = "Find files related to authentication"
        
        relevant_files = memory.search(user_query)
        
        # Track that these files were retrieved (increases importance)
        for file in relevant_files:
            if file.id:
                memory.update_importance(file.id, delta=0.1)
        
        return relevant_files
    
    print("Pipeline integration: Memory system accepts search queries")
    print("and returns ranked files for processing downstream")


# ============================================================================
# TESTING THE SYSTEM
# ============================================================================

def test_complete_workflow():
    """End-to-end test: store, search, rank, update."""
    from synapse.storage.memory import reset_memory
    
    # Reset for clean test
    reset_memory()
    memory = get_memory()
    
    # Create diverse file set
    files_to_store = [
        FileModel(
            id=1,
            name="auth.py",
            path="src/auth.py",
            content="Authentication module for user login and verification",
            category="security",
            tags=["auth", "login"],
            explanation="Handles authentication"
        ),
        FileModel(
            id=2,
            name="database.py",
            path="src/database.py",
            content="Database abstraction layer for PostgreSQL MySQL connections",
            category="storage",
            tags=["database", "sql"],
            explanation="Database layer"
        ),
        FileModel(
            id=3,
            name="router.py",
            path="src/router.py",
            content="HTTP routing and request dispatching for API endpoints",
            category="api",
            tags=["routing", "api"],
            explanation="API routing"
        ),
    ]
    
    memory.build_indexes(files_to_store)
    
    # Test 1: Search for authentication
    print("\n=== TEST 1: Search for 'authentication' ===")
    results = memory.search("authentication")
    assert len(results) > 0, "Should find auth.py"
    assert results[0].id == 1, "auth.py should rank first"
    print(f"✓ Found {len(results)} results, auth.py ranked first")
    
    # Test 2: Search for infrastructure
    print("\n=== TEST 2: Search for 'database storage' ===")
    results = memory.search("database storage")
    assert len(results) > 0, "Should find database.py"
    assert results[0].id == 2, "database.py should rank first"
    print(f"✓ Found {len(results)} results, database.py ranked first")
    
    # Test 3: Importance tracking
    print("\n=== TEST 3: Importance tracking ===")
    initial_importance = memory.importance.get(1, 1.0)
    memory.update_importance(1, delta=1.0)
    new_importance = memory.importance.get(1, 1.0)
    assert new_importance > initial_importance, "Importance should increase"
    print(f"✓ Importance increased: {initial_importance:.1f} → {new_importance:.1f}")
    
    # Test 4: Empty query
    print("\n=== TEST 4: Edge case - empty query ===")
    results = memory.search("")
    assert len(results) == 0, "Empty query should return no results"
    print(f"✓ Empty query correctly returns no results")
    
    print("\n=== ALL TESTS PASSED ===")


if __name__ == "__main__":
    # Run examples
    print("Memory System Usage Examples\n")
    print("=" * 60)
    
    print("\nExample 1: Store and Search")
    print("-" * 60)
    example_1_store_and_search()
    
    print("\n\nExample 2: Batch Indexing")
    print("-" * 60)
    example_2_batch_indexing()
    
    print("\n\nExample 3: Importance Tracking")
    print("-" * 60)
    example_3_importance_tracking()
    
    print("\n\nExample 4: Keyword Extraction")
    print("-" * 60)
    example_4_keyword_extraction()
    
    print("\n\nExample 6: No Results Handling")
    print("-" * 60)
    example_6_no_results_handling()
    
    print("\n\nComplete Workflow Test")
    print("-" * 60)
    test_complete_workflow()
