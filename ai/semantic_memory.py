import os
import pickle
import threading
import traceback

import faiss
import numpy as np

from ai.semantic_classifier import model

# ======== STORAGE ========

MEMORY_INDEX_PATH = "D:/AUTOMATION/semantic_memory.index"
MEMORY_META_PATH = "D:/AUTOMATION/semantic_memory_meta.pkl"

_lock = threading.Lock()


def _embedding_dimension():
    return model.get_sentence_embedding_dimension()


def _create_index():
    return faiss.IndexFlatL2(_embedding_dimension())


def _load_index():
    if os.path.exists(MEMORY_INDEX_PATH):
        return faiss.read_index(MEMORY_INDEX_PATH)
    return _create_index()


def _load_metadata():
    if os.path.exists(MEMORY_META_PATH):
        with open(MEMORY_META_PATH, "rb") as f:
            return pickle.load(f)
    return []


def _save_memory(index, metadata):
    faiss.write_index(index, MEMORY_INDEX_PATH)
    with open(MEMORY_META_PATH, "wb") as f:
        pickle.dump(metadata, f)


def add_document_memory(file_path, chunks, category, subject):
    try:
        if not chunks:
            return 0

        embeddings = model.encode(chunks)
        vectors = np.asarray(embeddings, dtype="float32")

        if vectors.ndim != 2 or vectors.shape[0] == 0:
            return 0

        with _lock:
            print("Creating FAISS index")
            index = _load_index()
            metadata = _load_metadata()

            print("Adding embeddings")
            index.add(vectors)

            for chunk, vector in zip(chunks, vectors):
                metadata.append(
                    {
                        "file_path": file_path,
                        "chunk_text": chunk,
                        "embedding": vector.tolist(),
                        "category": category,
                        "subject": subject,
                    }
                )

            print("Saving index")
            _save_memory(index, metadata)

        return vectors.shape[0]
    except Exception:
        traceback.print_exc()
        raise


def search_knowledge(query, top_k=5):
    if not query:
        return []

    with _lock:
        index = _load_index()
        metadata = _load_metadata()

    if index.ntotal == 0 or len(metadata) == 0:
        return []

    query_vec = model.encode([query]).astype("float32")
    k = min(top_k, index.ntotal)

    distances, indices = index.search(query_vec, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        item = dict(metadata[idx])
        item["distance"] = float(dist)
        results.append(item)

    return results
