with open('downloads/infosys-ar-24.pdf', 'rb') as f:
    header = f.read(20)
    print(f'Header bytes: {header}')
    f.seek(0, 2)
    print(f'File size: {f.tell()} bytes')

import fitz
print(f'\nPyMuPDF version: {fitz.__doc__}')
doc = fitz.open('downloads/infosys-ar-24.pdf')
print(f'PyMuPDF pages: {len(doc)}')
print(f'PyMuPDF page_count: {doc.page_count}')
print(f'Is encrypted: {doc.is_encrypted}')
doc.close()

# Try pdfplumber
try:
    import pdfplumber
    pdf = pdfplumber.open('downloads/infosys-ar-24.pdf')
    print(f'\npdfplumber pages: {len(pdf.pages)}')
    pdf.close()
except Exception as e:
    print(f'pdfplumber error: {e}')

# Try pypdf
try:
    from pypdf import PdfReader
    reader = PdfReader('downloads/infosys-ar-24.pdf')
    print(f'\npypdf pages: {len(reader.pages)}')
except Exception as e:
    print(f'pypdf error: {e}')

# Try Gemini with file upload API directly
try:
    import google.generativeai as genai
    import os
    genai.configure(api_key='AIzaSyCILk5XAiAUmyylUZLKcQgTcZnpdSiSAvM')
    
    print('\nTrying Gemini file upload API...')
    uploaded = genai.upload_file('downloads/infosys-ar-24.pdf', display_name='infosys-ar-24.pdf')
    print(f'Uploaded: {uploaded.name}, URI: {uploaded.uri}')
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content([
        uploaded,
        'What company is this annual report for? What is the revenue and net profit in this report? Reply briefly.'
    ])
    print(f'Gemini response: {response.text[:500]}')
except Exception as e:
    print(f'Gemini error: {e}')

