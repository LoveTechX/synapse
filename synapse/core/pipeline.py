"""Main orchestration pipeline for Synapse AI with robust error handling."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from synapse.ai.classifier import classify_content, extract_tags, classify_content_detailed
from synapse.ai.explainer import generate_explanation
from synapse.config.settings import CATEGORY_FOLDERS, DATABASE_PATH, DEFAULT_CATEGORY, OUTPUT_DIR
from synapse.models.file_model import FileModel
from synapse.storage.database import FileDatabase
from synapse.storage.file_manager import extract_file_content, move_file_to_category
from synapse.storage.memory import get_memory


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# EXCEPTIONS: Custom error types for pipeline failures
# ============================================================================

class PipelineError(Exception):
    """Base exception for all pipeline errors."""
    
    def __init__(self, step: str, message: str, cause: Optional[Exception] = None):
        self.step = step
        self.message = message
        self.cause = cause
        super().__init__(f"[{step}] {message}")


class FileExtractionError(PipelineError):
    """Failed to extract content from file."""
    pass


class ClassificationError(PipelineError):
    """Failed during classification step."""
    pass


class ExplanationError(PipelineError):
    """Failed to generate explanation."""
    pass


class FileMovementError(PipelineError):
    """Failed to move file to category folder."""
    pass


class StorageError(PipelineError):
    """Failed to store metadata in database."""
    pass


# ============================================================================
# RESULT STRUCTURE: Clean, typed output
# ============================================================================

@dataclass
class PipelineResult:
    """Result of successful pipeline execution."""
    
    id: int
    name: str
    path: str
    category: str
    tags: List[str]
    explanation: str
    created_at: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "category": self.category,
            "tags": self.tags,
            "explanation": self.explanation,
            "created_at": self.created_at,
        }


# ============================================================================
# PIPELINE: Orchestrates file processing with separated concerns
# ============================================================================

class SynapsePipeline:
    """
    Execute the MVP flow: extract → classify → explain → move → store.
    
    Each step is clearly separated and can fail independently with
    specific error handling and logging.
    """

    def __init__(self) -> None:
        """Initialize pipeline with database and memory connections."""
        self.database = FileDatabase(DATABASE_PATH)
        self.memory = get_memory()
        logger.info("Pipeline initialized with database: %s", DATABASE_PATH)

    # ========================================================================
    # STEP 1: INPUT VALIDATION
    # ========================================================================

    def _validate_file(self, file_path: str) -> Path:
        """
        Validate that file exists and is accessible.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Path object of validated file
            
        Raises:
            FileNotFoundError: If file doesn't exist or isn't a file
        """
        source = Path(file_path)
        
        if not source.exists():
            logger.error("File not found: %s", file_path)
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not source.is_file():
            logger.error("Path is not a file: %s", file_path)
            raise FileNotFoundError(f"Path is not a file: {file_path}")
        
        logger.debug("File validation passed: %s", source.name)
        return source

    # ========================================================================
    # STEP 2: CONTENT EXTRACTION
    # ========================================================================

    def _extract_content(self, file_path: Path) -> str:
        """
        Extract text content from file.
        
        Args:
            file_path: Path object of file to extract
            
        Returns:
            Extracted text content
            
        Raises:
            FileExtractionError: If extraction fails
        """
        try:
            logger.debug("Extracting content from: %s", file_path.name)
            content = extract_file_content(str(file_path))
            
            if not content or not isinstance(content, str):
                raise ValueError("Extracted content is empty or invalid")
            
            logger.debug("Content extracted: %d characters", len(content))
            return content
            
        except Exception as e:
            logger.error("Content extraction failed for %s: %s", file_path.name, str(e))
            raise FileExtractionError(
                step="EXTRACTION",
                message=f"Failed to extract content from {file_path.name}",
                cause=e
            )

    # ========================================================================
    # STEP 3: CLASSIFICATION
    # ========================================================================

    def _classify_content(self, content: str, file_name: str) -> tuple[str, List[str], float]:
        """
        Classify content into category and extract tags.
        
        Args:
            content: Text content to classify
            file_name: Name of file (helps classifier)
            
        Returns:
            Tuple of (predicted_category, tags_list, confidence_score)
            
        Raises:
            ClassificationError: If classification fails
        """
        try:
            logger.debug("Classifying content from: %s", file_name)
            
            # Classify content with confidence
            detailed_result = classify_content_detailed(content, file_name)
            predicted_category = detailed_result.category
            confidence = detailed_result.confidence
            
            if not predicted_category or not isinstance(predicted_category, str):
                raise ValueError("Invalid classification result")
            
            # Extract tags
            tags = extract_tags(content, file_name)
            if not isinstance(tags, list):
                raise ValueError("Invalid tags result")
            
            logger.debug(
                "Classification result: %s (confidence: %.2f, tags: %s)",
                predicted_category,
                confidence,
                tags
            )
            return predicted_category, tags, confidence
            
        except Exception as e:
            logger.error("Classification failed for %s: %s", file_name, str(e))
            raise ClassificationError(
                step="CLASSIFICATION",
                message=f"Failed to classify content from {file_name}",
                cause=e
            )

    # ========================================================================
    # STEP 4: CATEGORY DECISION
    # ========================================================================

    def _decide_category(self, predicted_category: str, file_name: str) -> str:
        """
        Apply fallback logic when classifier returns an unknown category.
        
        Logic priority:
        1. Use predicted if it exists in configured categories
        2. Check file extension (heuristic)
        3. Fall back to default category
        
        Args:
            predicted_category: Category from classifier
            file_name: Name of file (for extension checking)
            
        Returns:
            Final category to use
        """
        # Validate predicted category
        if predicted_category in CATEGORY_FOLDERS:
            logger.debug("Using predicted category: %s", predicted_category)
            return predicted_category

        # Fallback: check file extension
        extension = Path(file_name).suffix.lower()
        if extension in {".pdf", ".doc", ".docx"}:
            logger.debug("Using extension-based fallback: REFERENCE (ext: %s)", extension)
            return "REFERENCE"
        
        # Final fallback
        logger.warning(
            "Unknown category '%s' for %s; using default: %s",
            predicted_category,
            file_name,
            DEFAULT_CATEGORY
        )
        return DEFAULT_CATEGORY

    # ========================================================================
    # STEP 5: EXPLANATION GENERATION
    # ========================================================================

    def _generate_explanation(
        self,
        file_name: str,
        category: str,
        tags: List[str],
        content: str,
        confidence: float,
    ) -> str:
        """
        Generate a human-readable explanation of the classification.
        
        Connects the explanation to actual classification reasoning by
        analyzing which keywords matched and showing confidence level.
        
        Args:
            file_name: Name of file
            category: Final category assigned
            tags: List of extracted tags
            content: File content (used to identify matched keywords)
            confidence: Classification confidence score (0-1)
            
        Returns:
            Explanation text with reasoning
            
        Raises:
            ExplanationError: If explanation generation fails
        """
        try:
            logger.debug("Generating explanation for: %s", file_name)
            explanation = generate_explanation(
                file_name,
                category,
                tags,
                content=content,
                confidence=confidence,
            )
            
            if not explanation or not isinstance(explanation, str):
                raise ValueError("Generated explanation is empty or invalid")
            
            logger.debug("Explanation generated: %d characters", len(explanation))
            return explanation
            
        except Exception as e:
            logger.error("Explanation generation failed for %s: %s", file_name, str(e))
            raise ExplanationError(
                step="EXPLANATION",
                message=f"Failed to generate explanation for {file_name}",
                cause=e
            )

    # ========================================================================
    # STEP 6: FILE MOVEMENT
    # ========================================================================

    def _move_file(self, source_path: Path, category: str) -> str:
        """
        Move file to appropriate category folder.
        
        Args:
            source_path: Current file path
            category: Target category folder
            
        Returns:
            New file path after move
            
        Raises:
            FileMovementError: If file movement fails
        """
        try:
            logger.debug("Moving file to category: %s", category)
            folder_name = CATEGORY_FOLDERS.get(category, CATEGORY_FOLDERS[DEFAULT_CATEGORY])
            moved_path = move_file_to_category(str(source_path), OUTPUT_DIR, folder_name)
            
            if not moved_path:
                raise ValueError("File movement returned empty path")
            
            logger.info("File moved: %s → %s", source_path.name, moved_path)
            return moved_path
            
        except Exception as e:
            logger.error("File movement failed for %s: %s", source_path.name, str(e))
            raise FileMovementError(
                step="FILE_MOVEMENT",
                message=f"Failed to move file to category {category}",
                cause=e
            )

    # ========================================================================
    # STEP 7: DATABASE STORAGE
    # ========================================================================

    def _store_metadata(
        self,
        file_name: str,
        file_path: str,
        content: str,
        category: str,
        tags: List[str],
        explanation: str,
    ) -> FileModel:
        """
        Store file metadata in database.
        
        Args:
            file_name: Original filename
            file_path: Path after movement
            content: Extracted text content
            category: Classification category
            tags: Extracted tags
            explanation: Generated explanation
            
        Returns:
            FileModel with assigned ID
            
        Raises:
            StorageError: If storage fails
        """
        try:
            logger.debug("Storing metadata in database: %s", file_name)
            
            model = FileModel(
                id=None,
                name=file_name,
                path=file_path,
                content=content,
                category=category,
                tags=tags,
                explanation=explanation,
            )
            
            model.id = self.database.save_file(model)
            
            if not model.id:
                raise ValueError("Database did not return a valid ID")
            
            logger.info("Metadata stored with ID: %d", model.id)
            return model
            
        except Exception as e:
            logger.error("Database storage failed for %s: %s", file_name, str(e))
            raise StorageError(
                step="STORAGE",
                message=f"Failed to store metadata for {file_name}",
                cause=e
            )

    # ========================================================================
    # MAIN ORCHESTRATOR
    # ========================================================================

    def process_file(self, file_path: str) -> PipelineResult:
        """
        Process a single file through the complete pipeline.
        
        Pipeline stages:
        1. Validate file exists
        2. Extract content
        3. Classify into category
        4. Generate explanation
        5. Move to category folder
        6. Store metadata in database
        
        Args:
            file_path: Path to file to process
            
        Returns:
            PipelineResult with all details
            
        Raises:
            PipelineError: If any step fails (see subclasses for specifics)
        """
        logger.info("Starting pipeline for: %s", file_path)
        
        try:
            # Step 1: Validate input
            source = self._validate_file(file_path)
            
            # Step 2: Extract content
            content = self._extract_content(source)
            
            # Step 3: Classify
            predicted_category, tags, confidence = self._classify_content(content, source.name)
            
            # Step 4: Decide final category
            category = self._decide_category(predicted_category, source.name)
            
            # Step 5: Generate explanation
            explanation = self._generate_explanation(source.name, category, tags, content, confidence)
            
            # Step 6: Move file
            moved_path = self._move_file(source, category)
            
            # Step 7: Store metadata
            model = self._store_metadata(
                source.name,
                moved_path,
                content,
                category,
                tags,
                explanation,
            )
            
            # Step 8: Store in memory system
            self.memory.store_memory(model)
            
            # Wrap result
            result = PipelineResult(
                id=model.id,
                name=model.name,
                path=model.path,
                category=model.category,
                tags=model.tags,
                explanation=model.explanation,
                created_at=model.created_at,
            )
            
            logger.info("Pipeline completed successfully for: %s (ID: %d)", source.name, model.id)
            return result
            
        except PipelineError as e:
            # Already logged in the step
            logger.error("Pipeline failed at step '%s': %s", e.step, e.message)
            raise
        except Exception as e:
            # Unexpected error
            logger.exception("Unexpected error in pipeline: %s", str(e))
            raise PipelineError(
                step="UNKNOWN",
                message="An unexpected error occurred during pipeline execution",
                cause=e
            )


# ============================================================================
# MEMORY SEARCH: Query files stored in memory
# ============================================================================

def search_files(query: str) -> List[FileModel]:
    """
    Search for files in memory using a natural language query.
    
    Uses the global memory system singleton for fast, ranked retrieval.
    Results are ranked by relevance (keyword match, tags, recency, etc.).
    
    Args:
        query: Natural language search query (e.g., "Python security bug")
        
    Returns:
        List of FileModel objects ranked by relevance (highest first)
        
    Example:
        >>> results = search_files("authentication failure")
        >>> for file in results:
        ...     print(f"{file.name}: {file.explanation}")
    """
    memory = get_memory()
    return memory.search(query)


# ============================================================================
# REVIEW: What Changed & Why
# ============================================================================
#
# ISSUES FOUND IN ORIGINAL:
# ==========================
#
# 1. Tight Coupling
#    - All logic in one large process_file() method (47 lines)
#    - Hard to test individual steps in isolation
#    - Hard to reuse or modify individual steps
#
# 2. Minimal Error Handling
#    - Only checks if file exists; nothing else validated
#    - No error handling for: extraction, classification, movement, storage
#    - If any step fails, exception bubbles up without context
#    - No logging to understand what went wrong
#
# 3. Unclear Responsibilities
#    - process_file() does validation, extraction, classification, explanation,
#      movement, AND storage in one method
#    - Hard to understand what each piece does
#    - No clear separation of concerns
#
# 4. Poor Return Type
#    - Returns Dict[str, Any] - no type checking
#    - Easy to forget fields or misspell keys
#    - No documentation of fields
#
# 5. Missing Validation
#    - Extracted content not checked (could be empty)
#    - Classification result not validated
#    - Tags not validated
#    - Explanation result not checked
#    - Moved file path not verified
#
# 6. No Observability
#    - No logging at all - can't see what's happening
#    - Impossible to debug in production
#    - No way to track which step failed
#
# 7. Comments Are Vague
#    - "a. extract file content" - not clear what it means
#    - Comments are out of logical order (steps are a,b,c,d,e,f,g but not in order)
#    - Hard to understand the actual pipeline flow
#
#
# IMPROVEMENTS MADE:
# ==================
#
# 1. Separated Concerns (7 Clear Methods)
#    - _validate_file(): Input validation
#    - _extract_content(): Content extraction
#    - _classify_content(): Classification & tagging
#    - _decide_category(): Category fallback logic
#    - _generate_explanation(): Explanation generation
#    - _move_file(): File movement
#    - _store_metadata(): Database storage
#    - Result: Each step independently testable and reusable
#
# 2. Custom Exception Hierarchy
#    - PipelineError: Base class with step info
#    - FileExtractionError, ClassificationError, ExplanationError, etc.
#    - Each includes step name, cause exception, and context
#    - Result: Can catch specific errors and handle them appropriately
#
# 3. Structured Return Type
#    - PipelineResult dataclass with all fields
#    - Type-checked with mypy
#    - to_dict() for API responses
#    - Result: Type-safe, clear what's returned
#
# 4. Comprehensive Logging
#    - DEBUG logs for step entry/detail
#    - INFO logs for important milestones
#    - WARNING logs for fallbacks
#    - ERROR logs with context
#    - EXCEPTION logs for unexpected errors
#    - Result: Full visibility into pipeline execution
#
# 5. Input Validation at Each Step
#    - File existence check
#    - Content validity checks
#    - Classification result validation
#    - Tags result validation
#    - Explanation validity check
#    - File movement result check
#    - Database ID result check
#    - Result: Failures caught early with clear messages
#
# 6. Better Documentation
#    - Each method has docstring with Args/Returns/Raises
#    - Clear step numbers in process_file()
#    - Inline comments explain why decisions are made
#    - Result: Easy to understand and maintain
#
# 7. Explicit Error Handling
#    - try/catch at each step
#    - Specific exceptions for each kind of failure
#    - Fallback logic for category decision
#    - Unexpected errors caught and logged
#    - Result: No surprises, failures are clear
#
#
# IMPROVEMENTS IN DETAIL:
# =======================
#
# Exception Handling
# ------------------
# BEFORE:
#   - Only checks file existence
#   - Any extraction/classification/storage error crashes process
#   - No context about which step failed
#
# AFTER:
#   - Try/catch at every step
#   - Each step has specific exception (FileExtractionError, etc.)
#   - Exception includes: step name, descriptive message, original cause
#   - Can handle different failures differently (e.g., retry extraction but not classification)
#
# Example: If extraction fails
#   BEFORE: Raises generic exception, no idea what step
#   AFTER:  Raises FileExtractionError with context and original cause
#           Logs at ERROR level: "Content extraction failed for file.pdf: [reason]"
#
#
# Return Type
# -----------
# BEFORE:
#   Dict[str, Any] - requires documentation to know fields
#   No validation that ID, name, path, etc. are present
#   Typos in keys hard to detect
#
# AFTER:
#   PipelineResult dataclass with typed fields
#   Type checker catches missing fields
#   to_dict() for API serialization
#   Created_at always present (from FileModel)
#
#
# Logging
# -------
# BEFORE: No logging at all
#   Can't see what's happening in production
#   Can't debug failures
#   No audit trail
#
# AFTER:
#   logger.info("Starting pipeline...") - entry
#   logger.debug("Extracting content...") - step entry
#   logger.debug("Content extracted: 1234 characters") - step detail
#   logger.warning("Unknown category; using default") - fallback
#   logger.error("Content extraction failed...") - step failure
#   logger.exception("Unexpected error...") - unexpected error with traceback
#   logger.info("Pipeline completed successfully") - success
#   Result: Full visibility, can trace execution path
#
#
# Testing
# -------
# BEFORE:
#   Must test the entire pipeline end-to-end
#   Can't test "what if extraction fails"
#   Can't test "what if category is unknown"
#
# AFTER:
#   Can test _validate_file() independently
#   Can test _extract_content() with mock file manager
#   Can test _classify_content() with mock classifier
#   Can test _decide_category() with various inputs
#   Can test each step's error handling
#   Result: Better test coverage, easier to verify behavior
#
#
# REMAINING LIMITATIONS:
# ======================
#
# 1. Single File at a Time
#    - process_file() handles one file
#    - No batch processing
#    - Mitigation: Could add batch_process_files() that calls process_file()
#
# 2. No Retry Logic
#    - If a step fails, it fails immediately
#    - Network failures or temporary issues not retried
#    - Mitigation: Could wrap steps in retry decorator
#
# 3. Database Still a Bottleneck
#    - FileDatabase.save_file() is a black box
#    - If database fails, entire pipeline fails
#    - Mitigation: Could add database health checks; consider async
#
# 4. File Movement Not Atomic
#    - File moved, then metadata stored
#    - If storage fails, file is moved but metadata missing
#    - Mitigation: Could store first, move second; or use transactions
#
# 5. Content Stored in Database
#    - Full file content stored in DB (could be very large)
#    - Slows down queries
#    - Mitigation: Store content separately; reference by ID
#
# 6. No Rollback on Partial Failure
#    - If pipeline fails mid-way, state is inconsistent
#    - File might be moved but not in DB, or in DB but not moved
#    - Mitigation: Add rollback logic or use transaction-like pattern
#
#
# RECOMMENDED NEXT STEPS:
# =======================
#
# 1. Add Batch Processing (Low Effort)
#    - Create batch_process_files(file_paths: List[str]) method
#    - Calls process_file() for each
#    - Returns list of results and errors
#    - Useful for bulk import
#
# 2. Add Retry Logic (Medium Effort)
#    - Use decorator pattern or explicit try/except with exponential backoff
#    - Retry extraction on network failure
#    - Don't retry classification (deterministic)
#    - Result: Better resilience to temporary failures
#
# 3. Separate Large Content (Medium Effort)
#    - Don't store full content in FileMmodel
#    - Store to disk/S3 instead
#    - Store hash or reference in DB
#    - Result: Smaller DB, faster queries
#
# 4. Add Transaction Support (High Effort)
#    - Use database transactions
#    - Move file → Store metadata → Commit
#    - If storage fails, rollback (move file back)
#    - Result: Guaranteed consistency
#
# 5. Add Configuration (Low Effort)
#    - Make thresholds configurable (e.g., confidence threshold for classification)
#    - Make retry count configurable
#    - Make logging level configurable
#    - Result: Flexible deployment to different environments
#
# 6. Add Metrics/Monitoring (Medium Effort)
#    - Track processing time per step
#    - Count successes/failures
#    - Monitor which categories are most common
#    - Result: Better visibility into system behavior
# ============================================================================
