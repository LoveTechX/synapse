import os
import warnings
from pypdf import PdfReader
from docx import Document

# ======== CONFIG ========

CHUNK_SIZE = 500
OVERLAP = 50


# ======== TEXT CLEANING ========


def clean_text(text):
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    return text


# ======== CHUNKING ========


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks


# ======== PDF READER ========


def read_pdf(file_path):
    try:
        # suppress warnings and any stdout/stderr emitted by PdfReader internals
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
            import contextlib, io, sys

            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                reader = PdfReader(file_path)
                text = ""

                for page in reader.pages:
                    text += page.extract_text() or ""

        return clean_text(text)

    except Exception as e:
        # return empty string but let caller know via status
        return ""


# ======== DOCX READER ========


def read_docx(file_path):
    try:
        from contextlib import redirect_stdout, redirect_stderr
        import io

        # silence any underlying library output
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            doc = Document(file_path)
            text = ""

            for para in doc.paragraphs:
                text += para.text + " "

        return clean_text(text)

    except Exception:
        return ""


# ======== TXT / CODE ========


def read_txt(file_path):
    try:
        with open(file_path, "r", errors="ignore") as f:
            return clean_text(f.read())
    except:
        return ""


# ======== MAIN EXTRACTOR ========


def extract_content(file_path):
    """Extract text content from a file and return structured result.

    The return value is a dict containing:
      - chunks: list of text chunks (empty list on failure)
      - status: "success", "partial", or "failed"
      - error: optional error message when failure occurs

    Extraction is performed quietly; any stdout/stderr from underlying
    libraries is suppressed.
    """

    result = {"chunks": [], "status": "failed", "error": None}
    ext = file_path.split(".")[-1].lower()

    try:
        if ext == "pdf":
            text = read_pdf(file_path)
        elif ext == "docx":
            text = read_docx(file_path)
        else:
            text = read_txt(file_path)
    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        return result

    if not text:
        # could be a file with no readable text or an extraction error
        result["status"] = "failed"
        return result

    chunks = chunk_text(text)

    if chunks:
        result["chunks"] = chunks
        result["status"] = "success"
    else:
        result["status"] = "partial"  # maybe text present but chunking yielded nothing

    return result


# ======== TEST ========

if __name__ == "__main__":

    test_file = input("Enter file path: ")

    chunks = extract_content(test_file)

    print("\nTotal chunks:", len(chunks))

    for i, c in enumerate(chunks[:3]):
        print(f"\nChunk {i+1}:\n", c[:300])
