from pillar1_ingestor.document_classifier import DocumentClassifier
import os

print(f"API key loaded: {bool(os.getenv('GEMINI_API_KEY'))}")
c = DocumentClassifier(os.getenv('GEMINI_API_KEY'))
print(f"Classifier API key set: {bool(c.api_key)}")

file_path = '../downloads/infosys-ar-24.pdf'
print(f"File ends with .pdf: {file_path.endswith('.pdf')}")

doc_type, conf = c.classify(file_path, 'infosys-ar-24.pdf')
print(f"Type: {doc_type}, Confidence: {conf}")
