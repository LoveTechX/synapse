import json
import os
import pickle
import re
import threading
import time
from collections import Counter

from ai.semantic_memory import MEMORY_META_PATH, search_knowledge


SUGGESTION_HISTORY_PATH = "D:/AUTOMATION/jarvis_search_history.json"
FILE_ACCESS_PATH = "D:/AUTOMATION/jarvis_file_access.json"

MAX_HISTORY_ITEMS = 200
MAX_FILE_ITEMS = 200
SEMANTIC_CACHE_TTL = 20
MAX_COMPLETIONS = 12

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "are",
    "was",
    "were",
    "you",
    "your",
    "have",
    "has",
    "had",
    "about",
    "after",
    "before",
    "when",
    "where",
    "while",
    "using",
    "used",
    "use",
    "file",
    "files",
    "document",
    "documents",
    "notes",
}


def _safe_load_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _safe_save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _tokenize(text):
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{2,}", (text or "").lower())
    return [t for t in tokens if t not in STOPWORDS]


def _extract_topic_candidates(text, limit=5):
    counts = Counter(_tokenize(text))
    return [token for token, _ in counts.most_common(limit)]


class SuggestionEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self._search_history = Counter(_safe_load_json(SUGGESTION_HISTORY_PATH))
        self._file_access = Counter(_safe_load_json(FILE_ACCESS_PATH))
        self._topic_counter = Counter()
        self._semantic_cache = {}
        self._topic_loaded = False

    def record_search(self, query):
        normalized = (query or "").strip().lower()
        if not normalized:
            return
        with self._lock:
            self._search_history[normalized] += 1
            self._trim_counter(self._search_history, MAX_HISTORY_ITEMS)
            _safe_save_json(SUGGESTION_HISTORY_PATH, dict(self._search_history))

    def record_file_access(self, file_path):
        if not file_path:
            return
        with self._lock:
            self._file_access[file_path] += 1
            self._trim_counter(self._file_access, MAX_FILE_ITEMS)
            _safe_save_json(FILE_ACCESS_PATH, dict(self._file_access))

    def get_command_suggestions(self, prefix, commands):
        prefix = (prefix or "").strip().lower()
        return [cmd for cmd in commands if cmd.startswith(prefix)][:MAX_COMPLETIONS]

    def get_query_suggestions(self, command, partial_query):
        _ = command  # Reserved for command-specific routing later.
        partial = (partial_query or "").strip().lower()
        self._ensure_topic_index()

        suggestions = []
        suggestions.extend(self._from_search_history(partial))
        suggestions.extend(self._from_frequent_files(partial))
        suggestions.extend(self._from_topics(partial))
        suggestions.extend(self._from_semantic_search(partial))
        return self._dedupe_limit(suggestions, MAX_COMPLETIONS)

    def _from_search_history(self, partial):
        with self._lock:
            items = sorted(
                self._search_history.items(),
                key=lambda kv: kv[1],
                reverse=True,
            )
        if not partial:
            return [q for q, _ in items[:5]]
        return [q for q, _ in items if q.startswith(partial)][:6]

    def _from_frequent_files(self, partial):
        with self._lock:
            items = sorted(
                self._file_access.items(),
                key=lambda kv: kv[1],
                reverse=True,
            )

        suggestions = []
        for file_path, _count in items:
            base = os.path.basename(file_path)
            stem, _ext = os.path.splitext(base)
            candidate = stem.strip().lower()
            if not candidate:
                continue
            if partial and partial not in candidate:
                continue
            suggestions.append(candidate)
            if len(suggestions) >= 5:
                break
        return suggestions

    def _ensure_topic_index(self):
        if self._topic_loaded:
            return

        local_counter = Counter()
        if os.path.exists(MEMORY_META_PATH):
            try:
                with open(MEMORY_META_PATH, "rb") as f:
                    metadata = pickle.load(f)
                if isinstance(metadata, list):
                    for item in metadata[-3000:]:
                        if not isinstance(item, dict):
                            continue
                        chunk = item.get("chunk_text", "")
                        file_path = item.get("file_path", "")
                        for t in _extract_topic_candidates(chunk, limit=3):
                            local_counter[t] += 1
                        for t in _extract_topic_candidates(os.path.basename(file_path), limit=2):
                            local_counter[t] += 1
            except Exception:
                pass

        with self._lock:
            self._topic_counter = local_counter
            self._topic_loaded = True

    def _from_topics(self, partial):
        with self._lock:
            items = self._topic_counter.most_common(200)
        if not partial:
            return [topic for topic, _ in items[:4]]
        return [topic for topic, _ in items if topic.startswith(partial)][:6]

    def _from_semantic_search(self, partial):
        if len(partial) < 2:
            return []

        now = time.time()
        cached = self._semantic_cache.get(partial)
        if cached and now - cached["ts"] < SEMANTIC_CACHE_TTL:
            return cached["items"]

        suggestions = []
        try:
            results = search_knowledge(partial, top_k=6)
            for item in results:
                snippet = item.get("chunk_text", "")
                for candidate in _extract_topic_candidates(snippet, limit=3):
                    if partial and partial not in candidate:
                        continue
                    suggestions.append(candidate)

                file_path = item.get("file_path")
                if file_path:
                    stem = os.path.splitext(os.path.basename(file_path))[0].lower()
                    if stem and (not partial or partial in stem):
                        suggestions.append(stem)
        except Exception:
            suggestions = []

        final_items = self._dedupe_limit(suggestions, 6)
        self._semantic_cache[partial] = {"ts": now, "items": final_items}
        return final_items

    @staticmethod
    def _trim_counter(counter_obj, max_size):
        while len(counter_obj) > max_size:
            key, _ = min(counter_obj.items(), key=lambda kv: kv[1])
            del counter_obj[key]

    @staticmethod
    def _dedupe_limit(items, limit):
        seen = set()
        out = []
        for item in items:
            key = (item or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(item)
            if len(out) >= limit:
                break
        return out
