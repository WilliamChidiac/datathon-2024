import boto3
import os
import fitz  # PyMuPDF

# Initialize the AWS client for the Titan model
titan_client = boto3.client('titan')

def summarize_report(report_text):
    response = titan_client.invoke_model(
        ModelId='titan-model-id',  # Replace with your specific Titan model ID
        Body=report_text,
        ContentType='text/plain'
    )
    return response['Body'].read().decode('utf-8')  # Adjust based on response format

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    text = ""
    with fitz.open(file_path) as pdf_document:
        for page in pdf_document:
            text += page.get_text()
    return text

def process_reports(directory):
    summaries = {}
    for sector in os.listdir(directory):
        sector_path = os.path.join(directory, sector)
        summaries[sector] = []
        
        for filename in os.listdir(sector_path):
            if filename.endswith('.pdf'):
                file_path = os.path.join(sector_path, filename)
                report_text = extract_text_from_pdf(file_path)  # Extract text from PDF
                summary = summarize_report(report_text)  # Summarize the extracted text
                summaries[sector].append({
                    'filename': filename,
                    'summary': summary
                })
    
    return summaries

if __name__ == "__main__":
    reports_directory = 'src/data'  # Path to your reports directory
    all_summaries = process_reports(reports_directory)
    
    for sector, reports in all_summaries.items():
        print(f"Sector: {sector}")
        for report in reports:
            print(f"File: {report['filename']}\nSummary: {report['summary']}\n")
