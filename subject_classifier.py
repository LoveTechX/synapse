import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from semantic_classifier import model

# ===== SUBJECT CONFIG =====
# Add new subjects by updating this dictionary:
# "Subject Name": {"keywords": [...], "semantic_hint": "..."}
subjects = {
    "Operating Systems": {
        "keywords": [
            "operating system",
            "os",
            "cpu scheduling",
            "process",
            "thread",
            "deadlock",
            "semaphore",
            "paging",
            "memory management",
        ],
        "semantic_hint": "operating systems, process management, cpu scheduling, deadlock, memory management, synchronization",
    },
    "Computer Networks": {
        "keywords": [
            "computer networks",
            "network",
            "tcp",
            "udp",
            "ip",
            "osi",
            "routing",
            "subnet",
            "dns",
            "http",
        ],
        "semantic_hint": "computer networks, tcp ip, routing, osi model, protocols, network layers",
    },
    "DBMS": {
        "keywords": [
            "dbms",
            "database",
            "sql",
            "normalization",
            "transaction",
            "acid",
            "erd",
            "join",
            "query",
            "indexing",
        ],
        "semantic_hint": "database management systems, sql queries, normalization, transactions, relational databases",
    },
    "DAA": {
        "keywords": [
            "daa",
            "design and analysis of algorithms",
            "algorithm",
            "complexity",
            "big o",
            "dynamic programming",
            "greedy",
            "divide and conquer",
            "graph algorithm",
            "recurrence",
        ],
        "semantic_hint": "design and analysis of algorithms, complexity analysis, dynamic programming, greedy, divide and conquer",
    },
}

subject_names = list(subjects.keys())
subject_embeddings = model.encode(
    [subjects[name]["semantic_hint"] for name in subject_names]
)

MIN_KEYWORD_CONFIDENCE = 2
PROGRAMMING_EXTENSIONS = {"c", "cpp", "py", "js", "html", "css"}
SEMANTIC_FALLBACK_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx"}


def _keyword_scores(text):
    scores = {}
    for subject, config in subjects.items():
        scores[subject] = sum(1 for keyword in config["keywords"] if keyword in text)
    return scores


def _get_extension(file_name):
    if "." not in file_name:
        return ""
    return file_name.rsplit(".", 1)[-1].lower()


def _has_academic_keywords(text):
    all_keywords = []
    for config in subjects.values():
        all_keywords.extend(config["keywords"])
    return any(keyword in text for keyword in all_keywords)


def classify_subject(text_chunks, file_name=""):
    text = " ".join(text_chunks[:5]).lower()
    file_name = file_name.lower()
    keyword_input = f"{text} {file_name}".strip()
    ext = _get_extension(file_name)

    # ===== KEYWORD FIRST =====
    scores = _keyword_scores(keyword_input)
    best_subject = max(scores, key=scores.get)
    best_score = scores[best_subject]
    tied_best = [name for name, score in scores.items() if score == best_score]

    # Guard: skip subject classification for programming files without strong academic signals.
    if ext in PROGRAMMING_EXTENSIONS and best_score < MIN_KEYWORD_CONFIDENCE:
        return "GENERAL"

    if best_score >= MIN_KEYWORD_CONFIDENCE and len(tied_best) == 1:
        return best_subject

    # Low-confidence keyword evidence should not route to a specific subject.
    if best_score < MIN_KEYWORD_CONFIDENCE:
        return "GENERAL"

    # ===== SEMANTIC FALLBACK =====
    if ext not in SEMANTIC_FALLBACK_EXTENSIONS:
        return "GENERAL"

    semantic_input = keyword_input
    doc_embedding = model.encode([semantic_input])
    similarities = cosine_similarity(doc_embedding, subject_embeddings)[0]
    best_index = np.argmax(similarities)
    return subject_names[best_index]


if __name__ == "__main__":
    from ai.content_engine import extract_content

    file_path = input("Enter file path: ")
    raw = extract_content(file_path)
    if isinstance(raw, dict):
        chunks = raw.get("chunks", [])
    else:
        chunks = raw
    subject = classify_subject(chunks, file_path)
    print("Predicted subject:", subject)
