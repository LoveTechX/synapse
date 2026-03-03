import os
import shutil
import time
import hashlib
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from ai.content_engine import extract_content
import semantic_classifier
from semantic_classifier import classify_document
from subject_classifier import classify_subject
from semantic_memory import add_document_memory

# ======== PHASE IMPORTS ========
from storage.decision_log import log_decision, print_log_summary
from preview_mode import preview_mode
from ai.explanation import explanation_engine
from ai.confidence import confidence_scorer, ConfidenceScorer
from cli_interface import CLIInterface
from safety.guardrails import safety_guardrails

# ======== GLOBAL FLAGS ========

processed_cache = {}
initial_mode = False  # suppress logs during initial scan
SAFE_MODE = False  # Safe mode for preview + manual approval
VERBOSE_MODE = True  # Show detailed explanations
CONFIDENCE_THRESHOLD_AUTO = 0.80  # Auto-move threshold
app_mode = "auto"  # "auto" | "manual" | "preview"

# ======== LOGGING SYSTEM ========

log_file = "D:/AUTOMATION/file_logs.csv"
move_history_file = "D:/AUTOMATION/move_history.json"


def log_event(category, ext, size, source_folder):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = f"{timestamp},{category},{ext},{size},{source_folder}\n"

    if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
        with open(log_file, "w") as f:
            f.write("Timestamp,Category,Extension,Size(Bytes),Source\n")

    with open(log_file, "a") as f:
        f.write(row)


def _load_move_history():
    if not os.path.exists(move_history_file):
        return []
    try:
        with open(move_history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Move history load failed: {e}")
        return []


def _save_move_history(history):
    try:
        with open(move_history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Move history save failed: {e}")


def log_move_history(file_path, destination, category, subject):
    history = _load_move_history()
    history.append(
        {
            "file_path": file_path,
            "destination": destination,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "subject": subject,
        }
    )
    _save_move_history(history)


# ======== CONFIGURATION ========

sources = ["D:/TEST_AI/input"]
default_folder = "D:/04_REFERENCE"

# ======== CATEGORY INTELLIGENCE ========

category_destinations = {
    "COLLEGE": "D:/01_COLLEGE",
    "PROGRAMMING": "D:/02_PROGRAMMING",
    "PROJECTS": "D:/Projects",
    "CAREER": "D:/PERSONAL",
    "REFERENCE": "D:/04_REFERENCE",
}

content_extensions = {
    "pdf",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "txt",
    "rtf",
    "odt",
    "md",
    "csv",
    "xls",
    "xlsx",
    "json",
    "xml",
    "sql",
    "c",
    "cpp",
    "py",
    "js",
    "html",
    "css",
    "ipynb",
}

# ======== FILE RELEVANCE FILTER ========

ignored_extensions = {
    "xml",
    "yaml",
    "yml",
    "ini",
    "lock",
    "stamp",
    "rev",
    "sample",
    "tmp",
    "log",
}

ignored_filename_keywords = {
    "config",
    "template",
    "artifact",
    "snapshot",
    "internal",
    "metadata",
    "cache",
}

ignored_path_keywords = {".git", ".github", "hooks", "node_modules"}

allowed_relevant_extensions = {
    "pdf",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "txt",
    "rtf",
    "md",
    "csv",
    "xlsx",
    "json",
    "sql",
    "c",
    "cpp",
    "py",
    "js",
    "html",
    "css",
    "ipynb",
}

build_file_keywords = {
    "cmake",
    "gradle",
    "makefile",
    "build",
    "package",
    "package.json",
    "pubspec",
    "docker",
}

build_path_keywords = {
    "build",
    ".dart_tool",
    "android",
    "ios",
    "windows",
    "linux",
    "macos",
    "node_modules",
    ".git",
}

# ======== EXTENSION CLASSIFICATION ========

folders = {
    "pdf": "D:/STUDY",
    "doc": "D:/STUDY",
    "docx": "D:/STUDY",
    "ppt": "D:/STUDY",
    "pptx": "D:/STUDY",
    "txt": "D:/STUDY",
    "rtf": "D:/STUDY",
    "odt": "D:/STUDY",
    "md": "D:/STUDY",
    "csv": "D:/04_REFERENCE",
    "xls": "D:/04_REFERENCE",
    "xlsx": "D:/04_REFERENCE",
    "json": "D:/04_REFERENCE",
    "xml": "D:/04_REFERENCE",
    "sql": "D:/04_REFERENCE",
    "c": "D:/02_PROGRAMMING",
    "cpp": "D:/02_PROGRAMMING",
    "py": "D:/02_PROGRAMMING",
    "js": "D:/02_PROGRAMMING",
    "html": "D:/02_PROGRAMMING",
    "css": "D:/02_PROGRAMMING",
    "exe": "D:/SOFTWARE",
    "msi": "D:/SOFTWARE",
    "zip": "D:/SOFTWARE",
    "rar": "D:/SOFTWARE",
    "7z": "D:/SOFTWARE",
    "jpg": "D:/MEDIA",
    "jpeg": "D:/MEDIA",
    "png": "D:/MEDIA",
    "mp4": "D:/MEDIA",
    "mkv": "D:/MEDIA",
    "mp3": "D:/MEDIA",
    "ipynb": "D:/Projects",
}

# ======== KEYWORD INTELLIGENCE ========

keyword_rules = {
    "lab": "D:/01_COLLEGE",
    "assignment": "D:/01_COLLEGE",
    "semester": "D:/01_COLLEGE",
    "os": "D:/01_COLLEGE",
    "dbms": "D:/01_COLLEGE",
    "daa": "D:/01_COLLEGE",
    "research": "D:/04_REFERENCE",
    "paper": "D:/04_REFERENCE",
    "journal": "D:/04_REFERENCE",
    "ieee": "D:/04_REFERENCE",
    "resume": "D:/PERSONAL",
    "cv": "D:/PERSONAL",
    "offer": "D:/PERSONAL",
    "certificate": "D:/PERSONAL",
    "flutter": "D:/Projects",
    "react": "D:/Projects",
    "web": "D:/Projects",
    "app": "D:/Projects",
}

# ======== CATEGORY ENGINE ========


def get_category(destination):
    if "STUDY" in destination:
        return "Study"
    elif "PROGRAMMING" in destination:
        return "Programming"
    elif "SOFTWARE" in destination:
        return "Software"
    elif "MEDIA" in destination:
        return "Media"
    elif "COLLEGE" in destination:
        return "College"
    elif "Projects" in destination:
        return "Projects"
    else:
        return "Reference"


# ======== HASHING ========


def get_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_relevant_file(file_name, ext):
    """
    Returns True only for meaningful user documents.
    Filters system, build, config, and hidden files.
    """
    file_name_lower = file_name.lower()
    ext = ext.lower()

    # A) Hidden files
    if file_name_lower.startswith("."):
        return False

    # B) System/config extensions
    if ext in ignored_extensions:
        return False

    # C) Build/SDK keywords in filename
    if any(keyword in file_name_lower for keyword in ignored_filename_keywords):
        return False

    # D) Version control/package files and folders
    if any(keyword in file_name_lower for keyword in ignored_path_keywords):
        return False

    # E) Allow only meaningful content extensions
    return ext in allowed_relevant_extensions


def is_build_file(file_name, file_path):
    file_name_lower = file_name.lower()
    file_path_lower = file_path.lower().replace("\\", "/")

    if any(keyword in file_name_lower for keyword in build_file_keywords):
        return True

    return any(keyword in file_path_lower for keyword in build_path_keywords)


def normalize_folder_name(name):
    invalid_chars = '<>:"/\\|?*'
    cleaned = "".join("_" if ch in invalid_chars else ch for ch in name).strip()
    return cleaned or "General"


def get_memory_labels(destination):
    destination_lower = destination.lower().replace("\\", "/")

    if "/01_college" in destination_lower:
        category = "COLLEGE"
        destination_base = os.path.basename(destination.rstrip("/\\"))
        if destination_base and destination_base.lower() != "01_college":
            subject = destination_base
        else:
            subject = "GENERAL"
        return category, subject

    if "/02_programming" in destination_lower:
        return "PROGRAMMING", "GENERAL"

    if "/projects" in destination_lower:
        return "PROJECTS", "GENERAL"

    if "/personal" in destination_lower:
        return "CAREER", "GENERAL"

    return "REFERENCE", "GENERAL"


def _semantic_confidence(chunks, file_name):
    try:
        if not hasattr(semantic_classifier, "model"):
            return None
        if not hasattr(semantic_classifier, "category_embeddings"):
            return None
        if not hasattr(semantic_classifier, "cosine_similarity"):
            return None

        text = " ".join(chunks[:5]).lower()
        semantic_input = f"{text} {file_name.lower()}".strip()
        if not semantic_input:
            return None

        doc_embedding = semantic_classifier.model.encode([semantic_input])
        similarities = semantic_classifier.cosine_similarity(
            doc_embedding, semantic_classifier.category_embeddings
        )[0]
        return float(max(similarities))
    except Exception:
        return None


def classify_destination_with_explanation(
    file_path, file_name, ext, fallback_destination
):
    explanation = {
        "detected_keywords": [],
        "semantic_confidence": None,
        "reason": "Using fallback destination.",
    }

    if ext not in content_extensions:
        explanation["reason"] = (
            "Extension is not eligible for content-based classification."
        )
        return fallback_destination, explanation

    chunks = extract_content(file_path)
    if not chunks:
        explanation["reason"] = "No content extracted; using fallback destination."
        return fallback_destination, explanation

    category = classify_document(chunks, file_name)
    destination = category_destinations.get(category, fallback_destination)
    explanation["semantic_confidence"] = _semantic_confidence(chunks, file_name)
    explanation["reason"] = f"Semantic classifier predicted category: {category}."

    if category == "COLLEGE":
        try:
            subject = classify_subject(chunks, file_name)
            subject_folder = normalize_folder_name(subject)
            destination = os.path.join(category_destinations["COLLEGE"], subject_folder)
            explanation["reason"] = (
                f"Semantic classifier predicted COLLEGE and subject classifier selected: {subject_folder}."
            )
        except Exception as e:
            if not initial_mode:
                print(f"Subject detection failed ({e}) → using general COLLEGE")
            destination = category_destinations["COLLEGE"]
            explanation["reason"] = (
                "Semantic classifier predicted COLLEGE; subject detection failed, using general COLLEGE."
            )

    return destination, explanation


def classify_destination(file_path, file_name, ext, fallback_destination):
    destination, _ = classify_destination_with_explanation(
        file_path, file_name, ext, fallback_destination
    )
    return destination


# ======== SMART DESTINATION ========


def get_safe_destination(destination, file_path, filename):

    new_path = os.path.join(destination, filename)

    if os.path.exists(new_path):
        existing_hash = get_file_hash(new_path)
        new_hash = get_file_hash(file_path)

        # Skip duplicates
        if existing_hash == new_hash:
            if not initial_mode:
                print("Duplicate detected → skipped")
            return None

        # Versioning
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(new_path):
            new_filename = f"{base}_v{counter}{ext}"
            new_path = os.path.join(destination, new_filename)
            counter += 1

    return new_path


def safe_move(src, dst, retries=5, delay=2):
    for attempt in range(retries + 1):
        try:
            shutil.move(src, dst)
            if attempt > 0 and not initial_mode:
                print("Move successful after retry")
            return True
        except OSError as e:
            if getattr(e, "winerror", None) == 32:
                if attempt < retries:
                    if not initial_mode:
                        print("File locked, retrying...")
                    time.sleep(delay)
                    continue
                print(f"Move failed after retries (locked): {e}")
                return False

            print(f"Move failed: {e}")
            return False

    return False


def show_move_explanation(file_name, destination, category, subject, explanation):
    print("----- SAFE MODE REVIEW -----")
    print(f"File: {file_name}")
    print(f"Suggested category: {category}")
    if category == "COLLEGE":
        print(f"Suggested subject: {subject}")
    print(f"Destination path: {destination}")
    print("Explanation:")
    detected_keywords = explanation.get("detected_keywords") or []
    if detected_keywords:
        print(f"Detected keywords: {', '.join(detected_keywords)}")
    else:
        print("Detected keywords: None")

    confidence = explanation.get("semantic_confidence")
    if confidence is None:
        print("Semantic similarity confidence: N/A")
    else:
        print(f"Semantic similarity confidence: {confidence:.4f}")

    print(f"Reason: {explanation.get('reason', 'N/A')}")


def confirm_move():
    while True:
        choice = input("Approve move? (Y/N): ").strip().lower()
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no"}:
            return False
        print("Please enter Y or N.")


def undo_last_move():
    history = _load_move_history()
    if not history:
        print("No move history available to undo.")
        return False

    last_entry = history[-1]
    source_path = last_entry.get("file_path")
    moved_path = last_entry.get("destination")

    if not source_path or not moved_path:
        print("Invalid move history entry. Cannot undo.")
        return False

    if not os.path.exists(moved_path):
        print(f"Cannot undo. Moved file not found: {moved_path}")
        return False

    source_dir = os.path.dirname(source_path)
    os.makedirs(source_dir, exist_ok=True)
    restore_path = get_safe_destination(
        source_dir, moved_path, os.path.basename(source_path)
    )
    if restore_path is None:
        print("Undo skipped due to duplicate content at original location.")
        return False

    if not safe_move(moved_path, restore_path):
        print("Undo failed during file restore.")
        return False

    history.pop()
    _save_move_history(history)
    print(f"Undo successful: {restore_path}")
    return True


# ======== HANDLER ========


class SmartHandler(FileSystemEventHandler):

    def process(self, file_path):

        if not os.path.exists(file_path):
            return

        # Debounce events
        current_time = time.time()
        if file_path in processed_cache:
            if current_time - processed_cache[file_path] < 3:
                return
        processed_cache[file_path] = current_time

        time.sleep(2)

        file = os.path.basename(file_path)

        if file.startswith("~") or file.endswith(".tmp"):
            return

        if "." not in file:
            return

        file_lower = file.lower()
        ext = file.split(".")[-1].lower()
        explanation = {
            "detected_keywords": [],
            "semantic_confidence": None,
            "reason": "Using extension-based routing.",
        }

        destination = None
        detected_keywords = [
            keyword for keyword in keyword_rules if keyword in file_lower
        ]
        explanation["detected_keywords"] = detected_keywords
        if detected_keywords:
            destination = keyword_rules[detected_keywords[0]]
            explanation["reason"] = f"Keyword rule matched: {detected_keywords[0]}"
            if not initial_mode:
                print(f"Keyword detected → {detected_keywords[0]}")

        if destination is None:
            destination = folders.get(ext, default_folder)

        skip_ai_classification = False
        if is_build_file(file, file_path):
            destination = "D:/Projects"
            skip_ai_classification = True
            explanation["reason"] = (
                "Build system file detected; forced routing to Projects."
            )
            if not initial_mode:
                print("Build system file detected → routing to Projects")

        if not skip_ai_classification and not is_relevant_file(file, ext):
            if not initial_mode:
                print("Skipping non-relevant file:", file)
            return

        if not skip_ai_classification:
            try:
                destination, ai_explanation = classify_destination_with_explanation(
                    file_path, file, ext, destination
                )
                ai_explanation["detected_keywords"] = detected_keywords
                explanation = ai_explanation
            except Exception as e:
                if not initial_mode:
                    print(
                        f"Category intelligence failed ({e}) → using fallback routing"
                    )
                explanation["reason"] = (
                    f"Category intelligence failed ({e}); using fallback routing."
                )

        try:
            os.makedirs(destination, exist_ok=True)

            safe_path = get_safe_destination(destination, file_path, file)

            if safe_path is None:
                return

            # Logging
            file_size = os.path.getsize(file_path)
            source_folder = os.path.dirname(file_path)
            category = get_category(destination)
            memory_category, memory_subject = get_memory_labels(destination)

            log_event(category, ext, file_size, source_folder)

            if SAFE_MODE:
                show_move_explanation(
                    file,
                    safe_path,
                    memory_category,
                    memory_subject,
                    explanation,
                )
                if not confirm_move():
                    if not initial_mode:
                        print("Move skipped by user.")
                    return

            if not safe_move(file_path, safe_path):
                return

            if not initial_mode:
                print(f"Detected: {file}")
                print("Moved →", safe_path)

            log_move_history(file_path, safe_path, memory_category, memory_subject)

            # Semantic memory layer (non-blocking for organizer flow).
            if ext in content_extensions:
                chunks = extract_content(safe_path)
                if chunks:
                    if not initial_mode:
                        print("Indexing file into semantic memory...")
                    add_document_memory(
                        safe_path,
                        chunks,
                        memory_category,
                        memory_subject,
                    )

        except Exception as e:
            print("Error:", e)

    def on_created(self, event):
        if not event.is_directory:
            self.process(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.process(event.src_path)


# ======== INITIAL SCAN ========


def initial_scan():
    global initial_mode
    initial_mode = True

    print("Running initial scan...")

    handler = SmartHandler()

    for folder in sources:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                full_path = os.path.join(folder, file)
                if os.path.isfile(full_path):
                    handler.process(full_path)

    print("Initial scan completed.")
    initial_mode = False


# ======== MAIN ========

if __name__ == "__main__":

    print("🚀 Smart Autonomous + Analytics + Deduplication System Active")

    initial_scan()

    handler = SmartHandler()
    observer = Observer()

    for folder in sources:
        if os.path.exists(folder):
            observer.schedule(handler, folder, recursive=True)
            print("Monitoring:", folder)

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
