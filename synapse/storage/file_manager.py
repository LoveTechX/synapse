"""Safe file extraction and movement with error handling and validation."""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# File size limits
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
MAX_CONTENT_SIZE = 50 * 1024 * 1024  # 50 MB extracted content

# Supported extensions
TEXT_EXTENSIONS = {"txt", "md", "py", "json", "csv", "log", "yaml", "yml"}


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class FileManagerError(Exception):
    """Base exception for file operations."""
    pass


class FileExtractionError(FileManagerError):
    """Failed to extract content from file."""
    pass


class FileMovementError(FileManagerError):
    """Failed to move file to destination."""
    pass


# ============================================================================
# RESULT STRUCTURES
# ============================================================================

@dataclass
class ExtractionResult:
    """Result of content extraction."""
    success: bool
    content: str
    file_size: int
    extracted_size: int
    error: Optional[str] = None


@dataclass
class MovementResult:
    """Result of file movement."""
    success: bool
    source_path: str
    destination_path: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# CONTENT EXTRACTION
# ============================================================================

def _read_text_file(file_path: Path) -> str:
    """
    Read UTF-8 compatible text files safely.
    
    Args:
        file_path: Path to text file
        
    Returns:
        Extracted text content
        
    Raises:
        FileExtractionError: If reading fails
    """
    try:
        logger.debug("Reading text file: %s", file_path.name)
        with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
            content = handle.read()
        logger.debug("Text extraction successful: %d characters", len(content))
        return content
    except Exception as e:
        logger.error("Failed to read text file %s: %s", file_path.name, str(e))
        raise FileExtractionError(f"Failed to read text file: {str(e)}")


def _read_pdf_file(file_path: Path) -> str:
    """
    Extract text from a PDF document.
    
    Falls back gracefully if pypdf is unavailable.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content (empty string if extraction fails)
    """
    try:
        logger.debug("Extracting text from PDF: %s", file_path.name)
        pypdf_module = __import__("pypdf")
        reader = pypdf_module.PdfReader(str(file_path))
        
        if not reader.pages:
            logger.warning("PDF has no pages: %s", file_path.name)
            return ""
        
        content = " ".join(
            (page.extract_text() or "") for page in reader.pages
        )
        logger.debug("PDF extraction successful: %d characters", len(content))
        return content
        
    except ImportError:
        logger.warning("pypdf not available; skipping PDF extraction for %s", file_path.name)
        return ""
    except Exception as e:
        logger.warning("Failed to extract PDF %s: %s", file_path.name, str(e))
        return ""


def _read_docx_file(file_path: Path) -> str:
    """
    Extract text from a DOCX document.
    
    Falls back gracefully if python-docx is unavailable.
    
    Args:
        file_path: Path to DOCX file
        
    Returns:
        Extracted text content (empty string if extraction fails)
    """
    try:
        logger.debug("Extracting text from DOCX: %s", file_path.name)
        docx_module = __import__("docx")
        document = docx_module.Document(str(file_path))
        
        if not document.paragraphs:
            logger.warning("DOCX has no paragraphs: %s", file_path.name)
            return ""
        
        content = " ".join(paragraph.text for paragraph in document.paragraphs)
        logger.debug("DOCX extraction successful: %d characters", len(content))
        return content
        
    except ImportError:
        logger.warning("python-docx not available; skipping DOCX extraction for %s", file_path.name)
        return ""
    except Exception as e:
        logger.warning("Failed to extract DOCX %s: %s", file_path.name, str(e))
        return ""


def extract_file_content(file_path: str) -> str:
    """
    Extract raw text content from the given file path.
    
    Supports: txt, md, py, json, csv, log, yaml, yml, pdf, docx
    
    Args:
        file_path: Path to file to extract
        
    Returns:
        Extracted text content
        
    Raises:
        FileExtractionError: If file doesn't exist or extraction fails
    """
    path = Path(file_path)
    
    # Validate file exists
    if not path.exists():
        logger.error("File not found: %s", file_path)
        raise FileExtractionError(f"File not found: {file_path}")
    
    if not path.is_file():
        logger.error("Path is not a file: %s", file_path)
        raise FileExtractionError(f"Path is not a file: {file_path}")
    
    # Check file size
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        logger.error("File too large (%d bytes): %s", file_size, file_path)
        raise FileExtractionError(
            f"File too large ({file_size} bytes, max {MAX_FILE_SIZE}): {file_path}"
        )
    
    # Extract based on extension
    extension = path.suffix.lower().lstrip(".")
    
    try:
        if extension in TEXT_EXTENSIONS:
            content = _read_text_file(path)
        elif extension == "pdf":
            content = _read_pdf_file(path)
        elif extension == "docx":
            content = _read_docx_file(path)
        else:
            logger.debug("Unknown extension %s; treating as text: %s", extension, file_path)
            content = _read_text_file(path)
        
        # Check extracted content size
        if len(content) > MAX_CONTENT_SIZE:
            logger.error(
                "Extracted content too large (%d bytes): %s",
                len(content),
                file_path
            )
            raise FileExtractionError(
                f"Extracted content too large ({len(content)} bytes, max {MAX_CONTENT_SIZE})"
            )
        
        return content
        
    except FileExtractionError:
        raise
    except Exception as e:
        logger.error("Unexpected error extracting %s: %s", file_path, str(e))
        raise FileExtractionError(f"Unexpected extraction error: {str(e)}")


# ============================================================================
# FILE MOVEMENT
# ============================================================================

def _validate_source_file(source: Path) -> None:
    """Ensure the source exists and is a regular file."""
    if not source.exists():
        logger.error("Source file not found: %s", source)
        raise FileMovementError(f"Source file not found: {source}")

    if not source.is_file():
        logger.error("Source path is not a file: %s", source)
        raise FileMovementError(f"Source path is not a file: {source}")


def _resolve_unique_destination(destination_dir: Path, source_name: str) -> Path:
    """Return a collision-free destination path by suffixing duplicates."""
    candidate = destination_dir / source_name
    if not candidate.exists():
        return candidate

    stem = Path(source_name).stem
    suffix = Path(source_name).suffix

    # Keep trying simple numbered names: file_1.ext, file_2.ext, ...
    for counter in range(1, 10001):
        candidate = destination_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate

    raise FileMovementError(f"Too many duplicate files for {source_name}")

def move_file_to_category(
    file_path: str,
    destination_root: Path,
    folder_name: str,
) -> str:
    """
    Move a file into a category folder safely.
    
    Handles:
    - Directory creation
    - Duplicate file names (appends _1, _2, etc.)
    - Path validation
    - Error recovery
    
    Args:
        file_path: Path to source file
        destination_root: Root destination directory
        folder_name: Subdirectory name within root
        
    Returns:
        Final path of moved file
        
    Raises:
        FileMovementError: If move operation fails
    """
    source = Path(file_path)
    _validate_source_file(source)

    # Ensure destination root/category directories exist.
    try:
        destination_root.mkdir(parents=True, exist_ok=True)
        destination_dir = destination_root / folder_name
        destination_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error("Failed to prepare destination directories: %s", str(e))
        raise FileMovementError(f"Failed to prepare destination: {str(e)}")

    destination = _resolve_unique_destination(destination_dir, source.name)

    try:
        logger.info("Moving file: %s -> %s", source, destination)
        shutil.move(str(source), str(destination))
        logger.info("File moved successfully: %s", destination)
        return str(destination)
    except PermissionError as e:
        logger.error("Permission denied while moving %s: %s", source, str(e))
        raise FileMovementError(f"Permission denied: {str(e)}")
    except (OSError, shutil.Error) as e:
        logger.error("Failed moving %s to %s: %s", source, destination, str(e))
        raise FileMovementError(f"Move operation failed: {str(e)}")
