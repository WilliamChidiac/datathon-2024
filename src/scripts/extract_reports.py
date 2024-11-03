import os
import fitz  # PyMuPDF

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        with fitz.open(file_path) as pdf_document:
            for page in pdf_document:
                text += page.get_text()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return text

def save_extracted_text(directory):
    for industry in os.listdir(directory):
        industry_path = os.path.join(directory, industry)
        if os.path.isdir(industry_path):
            for company in os.listdir(industry_path):
                company_path = os.path.join(industry_path, company)
                if os.path.isdir(company_path):
                    for filename in os.listdir(company_path):
                        if filename.endswith('.pdf'):
                            file_path = os.path.join(company_path, filename)
                            report_text = extract_text_from_pdf(file_path)
                            text_file_path = file_path.replace('.pdf', '.txt')
                            with open(text_file_path, 'w', encoding='utf-8') as text_file:
                                text_file.write(report_text)

if __name__ == "__main__":
    reports_directory = 'src/data'  # Adjust this path as necessary
    save_extracted_text(reports_directory)
