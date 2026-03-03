"""
SMART AUTONOMOUS FILE ORGANIZER - UPGRADED WITH FULL TRANSPARENCY & CONTROL
====================================================================

Phases implemented:
1. ✓ Decision Logging - All decisions logged to JSON
2. ✓ Preview Mode - Review before moving
3. ✓ Explanation Engine - Understand why decisions were made
4. ✓ Confidence Scoring - Trust scores for each decision
5. ✓ Interactive CLI - Control and query the system
6. ✓ Safety Guardrails - Protect critical files

Features:
- Real-time monitoring with semantic classification
- Subject detection with confidence scores
- Deduplication using hash-based comparison
- Semantic memory indexing (FAISS)
- Decision logging and audit trail
- Preview mode (no moves, only show decisions)
- User approval workflow
- Detailed explanations for every decision
- Safety checks (hidden files, build artifacts, project configs)
- Interactive CLI interface
"""

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
from cli_interface import CLIInterface, start_cli_interface
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
        print(f"⚠️  Move history load failed: {e}")
        return []


def _save_move_history(history):
    try:
        with open(move_history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"⚠️  Move history save failed: {e}")


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
                print("⊙ Duplicate detected → skipped")
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
                print(f"❌ Move failed after retries (locked): {e}")
                return False

            print(f"❌ Move failed: {e}")
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
        choice = input("✓ Approve move? (Y/N): ").strip().lower()
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
    print(f"✓ Undo successful: {restore_path}")
    return True


# ======== HANDLER ========


class SmartHandler(FileSystemEventHandler):

    def process(self, file_path):
        """
        Process a file with full transparency, safety checks, and user control.
        Integrated with all 6 phases of the upgrade.
        """

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
        file_lower = file.lower()
        ext = file.split(".")[-1].lower() if "." in file else ""

        # ===== PHASE 6: SAFETY GUARDRAILS CHECK =====
        is_safe, violations = safety_guardrails.check_safety(file_path)
        if not is_safe:
            if not initial_mode:
                print(f"🛡️  {file}: BLOCKED - {violations[0]}")

            log_decision(
                file_path=file_path,
                action="skipped",
                reason=f"Safety guardrail: {violations[0]}",
                category=None,
                subject=None,
                destination=None,
                confidence=None,
                details={"violations": violations},
            )
            return

        # ===== Skip temporary and placeholder files =====
        if file.startswith("~") or file.endswith(".tmp"):
            log_decision(
                file_path=file_path,
                action="skipped",
                reason="Temporary file (starts with ~ or ends with .tmp)",
                details={"file_type": "temporary"},
            )
            return

        if "." not in file:
            log_decision(
                file_path=file_path,
                action="skipped",
                reason="File has no extension - unknown file type",
                details={"file_type": "no_extension"},
            )
            return

        # ===== Build initial explanation =====
        explanation = {
            "detected_keywords": [],
            "semantic_confidence": None,
            "reason": "Using extension-based routing.",
        }

        confidence = 0.0
        decision_signals = []

        # ===== PHASE 3: Keyword Detection =====
        destination = None
        detected_keywords = [
            keyword for keyword in keyword_rules if keyword in file_lower
        ]
        explanation["detected_keywords"] = detected_keywords

        if detected_keywords:
            destination = keyword_rules[detected_keywords[0]]
            keyword_confidence = confidence_scorer.score_keyword_match(
                len(detected_keywords), "high"
            )
            confidence = keyword_confidence
            decision_signals.append(
                explanation_engine.keyword_rule_detected(
                    detected_keywords[0], "filename"
                )
            )
            explanation["reason"] = f"Keyword rule matched: {detected_keywords[0]}"

            if not initial_mode and VERBOSE_MODE:
                print(f"🔑 Keyword detected: {detected_keywords[0]}")

        if destination is None:
            destination = folders.get(ext, default_folder)
            ext_confidence = confidence_scorer.score_extension_rule(ext, False)
            confidence = ext_confidence
            decision_signals.append(
                explanation_engine.extension_rule(ext, get_category(destination))
            )
            explanation["reason"] = (
                f"Extension-based routing: {ext} → {get_category(destination)}"
            )

        skip_ai_classification = False
        if is_build_file(file, file_path):
            destination = "D:/Projects"
            skip_ai_classification = True
            explanation["reason"] = (
                "Build system file detected; forced routing to Projects."
            )
            confidence = 0.85
            decision_signals.append("Build system file detected")

            if not initial_mode and VERBOSE_MODE:
                print("⚙️  Build system file detected → routing to Projects")

        # ===== Check if file is relevant for content analysis =====
        if not skip_ai_classification and not is_relevant_file(file, ext):
            log_decision(
                file_path=file_path,
                action="skipped",
                reason=explanation_engine.skip_reason("non_content"),
                details={"file_type": "non_content", "extension": ext},
            )
            return

        # ===== PHASE 3 + 4: AI Classification with Confidence =====
        if not skip_ai_classification:
            try:
                destination, ai_explanation = classify_destination_with_explanation(
                    file_path, file, ext, destination
                )
                ai_explanation["detected_keywords"] = detected_keywords
                explanation = ai_explanation

                # Get semantic confidence
                semantic_conf = _semantic_confidence(
                    extract_content(file_path) if ext in content_extensions else [],
                    file,
                )
                if semantic_conf is not None:
                    explanation["semantic_confidence"] = semantic_conf
                    decision_signals.append(
                        explanation_engine.semantic_match(
                            get_category(destination), semantic_conf
                        )
                    )

                    # Combine confidence signals
                    combined_conf, conf_reasoning = confidence_scorer.combine_signals(
                        keyword_score=confidence if detected_keywords else None,
                        semantic_score=semantic_conf,
                    )
                    confidence = combined_conf

            except Exception as e:
                if not initial_mode:
                    print(f"⚠️  Category intelligence failed: {str(e)}")
                explanation["reason"] = (
                    f"Category intelligence failed ({str(e)}); using fallback routing."
                )
                log_decision(
                    file_path=file_path,
                    action="skipped",
                    reason=explanation_engine.extraction_failure(str(e)),
                    destination=destination,
                    confidence=confidence,
                    details={"error": str(e)},
                )
                return

        # ===== PHASE 4: Check Confidence Threshold =====
        action_for_confidence, action_description = (
            confidence_scorer.get_action_for_confidence(confidence)
        )

        if action_for_confidence == "skip":
            log_decision(
                file_path=file_path,
                action="skipped",
                reason=explanation_engine.skip_reason(
                    "insufficient_confidence", f"{confidence*100:.0f}% confidence"
                ),
                category=get_category(destination),
                destination=destination,
                confidence=confidence,
                details={"confidence_score": confidence},
            )
            if not initial_mode:
                print(f"⚠️  {file}: Low confidence ({confidence*100:.0f}%) - skipped")
            return

        # ===== Destination + Deduplication =====
        try:
            os.makedirs(destination, exist_ok=True)

            safe_path = get_safe_destination(destination, file_path, file)

            if safe_path is None:
                # Duplicate detected
                log_decision(
                    file_path=file_path,
                    action="duplicate",
                    reason=explanation_engine.duplicate_detected(destination),
                    category=get_category(destination),
                    destination=destination,
                    confidence=confidence,
                )
                if not initial_mode:
                    print(f"⊙ {file}: Duplicate detected → skipped")
                return

            # Logging
            file_size = os.path.getsize(file_path)
            source_folder = os.path.dirname(file_path)
            category = get_category(destination)
            memory_category, memory_subject = get_memory_labels(destination)

            log_event(category, ext, file_size, source_folder)

            # ===== PHASE 2: Preview Mode =====
            if app_mode == "preview" or preview_mode.is_enabled():
                preview_mode.add_to_queue(
                    file_name=file,
                    file_path=file_path,
                    destination=safe_path,
                    category=category,
                    subject=memory_subject,
                    reason=explanation["reason"],
                    confidence=confidence,
                )

                if not initial_mode:
                    print(f"👁️  {file}: Added to preview queue")

                log_decision(
                    file_path=file_path,
                    action="preview",
                    reason="File queued for preview mode review",
                    category=category,
                    subject=memory_subject,
                    destination=safe_path,
                    confidence=confidence,
                    details={"mode": "preview"},
                )
                return

            # ===== SAFE MODE / MANUAL APPROVAL =====
            if app_mode == "manual" or SAFE_MODE:
                if not initial_mode:
                    show_move_explanation(
                        file,
                        safe_path,
                        category,
                        memory_subject,
                        explanation,
                    )

                    approved = confirm_move()
                    if not approved:
                        print("❌ Move skipped by user")
                        log_decision(
                            file_path=file_path,
                            action="skipped",
                            reason="User rejected move in manual mode",
                            category=category,
                            subject=memory_subject,
                            destination=safe_path,
                            confidence=confidence,
                        )
                        return

            # ===== EXECUTE MOVE =====
            if not safe_move(file_path, safe_path):
                log_decision(
                    file_path=file_path,
                    action="error",
                    reason="File move operation failed",
                    category=category,
                    subject=memory_subject,
                    destination=safe_path,
                    confidence=confidence,
                    details={"error_type": "move_failed"},
                )
                return

            # ===== PHASE 1: Log Successful Move =====
            log_decision(
                file_path=file_path,
                action="moved",
                reason=explanation["reason"],
                category=category,
                subject=memory_subject,
                destination=safe_path,
                confidence=confidence,
                details={
                    "signals": decision_signals,
                    "confidence_action": action_for_confidence,
                    "file_size": file_size,
                },
            )

            if not initial_mode:
                print(f"✓ {file} → {category}")
                if VERBOSE_MODE and decision_signals:
                    print(f"  Why: {explanation['reason']}")
                if confidence < CONFIDENCE_THRESHOLD_AUTO:
                    print(f"  Confidence: {confidence*100:.0f}%")

            log_move_history(file_path, safe_path, category, memory_subject)

            # Semantic memory layer (non-blocking for organizer flow).
            if ext in content_extensions:
                try:
                    chunks = extract_content(safe_path)
                    if chunks:
                        if not initial_mode and VERBOSE_MODE:
                            print(f"  📚 Indexing into semantic memory...")
                        add_document_memory(
                            safe_path,
                            chunks,
                            memory_category,
                            memory_subject,
                        )
                except Exception as e:
                    if not initial_mode:
                        print(f"  ⚠️  Semantic indexing failed: {e}")

        except Exception as e:
            log_decision(
                file_path=file_path,
                action="error",
                reason=f"Unexpected error: {str(e)}",
                confidence=confidence,
                details={"error": str(e), "error_type": "processing_error"},
            )
            print(f"❌ Error: {e}")

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

    print("\n🔍 Running initial scan...")
    print("=" * 60)

    handler = SmartHandler()

    for folder in sources:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                full_path = os.path.join(folder, file)
                if os.path.isfile(full_path):
                    handler.process(full_path)

    print("=" * 60)
    print("✓ Initial scan completed")
    print_log_summary()
    initial_mode = False


# ======== MAIN ========

if __name__ == "__main__":

    import sys

    print("\n" + "=" * 70)
    print("🚀 SMART AUTONOMOUS FILE ORGANIZER - UPGRADED EDITION")
    print("=" * 70)
    print("Phases: Logging | Preview | Explanation | Confidence | CLI | Safety")
    print("=" * 70)

    # Check for CLI mode
    if len(sys.argv) > 1 and sys.argv[1].lower() == "cli":
        print("\n📟 Starting Interactive CLI Interface...")
        print("Type 'help' for available commands\n")
        start_cli_interface()
    else:
        # Normal monitoring mode
        initial_scan()

        handler = SmartHandler()
        observer = Observer()

        for folder in sources:
            if os.path.exists(folder):
                observer.schedule(handler, folder, recursive=True)
                print(f"📂 Monitoring: {folder}")

        print("\n✓ Real-time monitoring active")
        print("   Press Ctrl+C to stop\n")

        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Stopping monitor...")
            observer.stop()

        observer.join()
        print("✓ Shutdown complete")
