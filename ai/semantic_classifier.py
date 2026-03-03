from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ===== MODEL =====
model = SentenceTransformer("all-mpnet-base-v2")

# ===== CATEGORIES =====
categories = {
    "COLLEGE": "university, academic subjects, operating systems, computer networks, dbms, daa, assignments, lab manuals, semester, exam, theory",
    "PROGRAMMING": "coding, software development, programming languages, python, c, cpp, java, scripts, system design",
    "PROJECTS": "personal projects, flutter apps, web apps, mobile apps, development projects",
    "CAREER": "resume, job, internship, placement, interview, offer letter, certificate",
    "REFERENCE": "ebooks, documentation, manuals, research papers",
}

category_names = list(categories.keys())
category_embeddings = model.encode(list(categories.values()))


# ===== CLASSIFICATION =====
def classify_document(text_chunks, file_name=""):

    text = " ".join(text_chunks[:5]).lower()
    file_name = file_name.lower()

    # ===== STRONG KEYWORD SIGNALS =====
    if any(word in text or word in file_name for word in ["assignment", "lab", "semester", "exam"]):
        return "COLLEGE"

    if any(word in text or word in file_name for word in ["resume", "cv", "offer", "certificate"]):
        return "CAREER"

    if any(word in text or word in file_name for word in ["flutter", "react", "project", "app"]):
        return "PROJECTS"

    # ===== PERSONAL STUDY PATTERN =====
    if any(word in text or word in file_name for word in ["day", "task", "plan", "notes"]):
        return "COLLEGE"

    # ===== ACADEMIC PROGRAMMING DETECTION =====
    has_academic_file_signal = any(word in file_name for word in ["task", "lab", "experiment"])
    has_programming_text_signal = any(
        word in text for word in ["c++", "java", "python", "fstream", "program"]
    )
    if has_academic_file_signal and has_programming_text_signal:
        return "COLLEGE"

    # ===== SUBJECT DETECTION =====
    if any(
        word in text
        for word in ["operating system", "cpu scheduling", "process", "deadlock"]
    ):
        return "COLLEGE"

    if any(word in text for word in ["dbms", "sql", "database"]):
        return "COLLEGE"

    if any(word in text for word in ["computer networks", "tcp", "ip"]):
        return "COLLEGE"
    


    # ===== SEMANTIC FALLBACK =====
    semantic_input = f"{text} {file_name}".strip()
    doc_embedding = model.encode([semantic_input])

    similarities = cosine_similarity(doc_embedding, category_embeddings)[0]

    best_index = np.argmax(similarities)

    return category_names[best_index]
