from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import pickle

# ===== MODEL =====

model = SentenceTransformer("all-mpnet-base-v2")

# ===== STORAGE =====

VECTOR_DB = "D:/AUTOMATION/vector_store.pkl"

# ===== INIT =====


def load_db():
    if os.path.exists(VECTOR_DB):
        with open(VECTOR_DB, "rb") as f:
            return pickle.load(f)
    return {"vectors": [], "metadata": []}


def save_db(db):
    with open(VECTOR_DB, "wb") as f:
        pickle.dump(db, f)


# ===== ADD DOCUMENT =====


def add_chunks(chunks, file_path):

    db = load_db()

    embeddings = model.encode(chunks)

    for emb, chunk in zip(embeddings, chunks):
        db["vectors"].append(emb)
        db["metadata"].append({"file": file_path, "text": chunk[:200]})

    save_db(db)
    print("Stored embeddings:", len(chunks))


# ===== SEARCH =====


def semantic_search(query, top_k=5):

    db = load_db()

    if len(db["vectors"]) == 0:
        print("No data yet.")
        return

    vectors = np.array(db["vectors"]).astype("float32")

    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    query_vec = model.encode([query]).astype("float32")

    distances, indices = index.search(query_vec, top_k)

    print("\nResults:\n")

    for i in indices[0]:
        print(db["metadata"][i]["file"])
        print(db["metadata"][i]["text"])
        print("-" * 50)


# ===== TEST =====

if __name__ == "__main__":

    while True:
        cmd = input("\n1: Add file  2: Search  3: Exit\n")

        if cmd == "1":
            from ai.content_engine import extract_content

            path = input("File path: ")
            raw = extract_content(path)
            if isinstance(raw, dict):
                chunks = raw.get("chunks", [])
            else:
                chunks = raw
            add_chunks(chunks, path)

        elif cmd == "2":
            q = input("Query: ")
            semantic_search(q)

        else:
            break
