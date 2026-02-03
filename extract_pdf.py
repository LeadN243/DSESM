import PyPDF2
import sys

pdf_path = 'assignment-4-group-work.pdf'
try:
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        print(f'Total pages: {len(pdf.pages)}\n')
        for i, page in enumerate(pdf.pages):
            print(f'--- PAGE {i+1} ---')
            text = page.extract_text()
            print(text)
            print('\n')
except FileNotFoundError:
    print(f"Error: File '{pdf_path}' not found")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
