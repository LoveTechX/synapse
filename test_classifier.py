from ai.content_engine import extract_content
from ai.semantic_classifier import classify_document

file = input("Enter file path: ")

chunks = extract_content(file)

category = classify_document(chunks, file)

print("Predicted category:", category)
