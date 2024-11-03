import boto3
import json
from botocore.exceptions import ClientError
from langchain.text_splitter import RecursiveCharacterTextSplitter

def create_bedrock_client():
    """Create a Bedrock Runtime client."""
    return boto3.client("bedrock-runtime", region_name="us-west-2")

def read_document(file_path):
    """Read content from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def summarize_chunk(client, text):
    """Summarize a single chunk of text using Amazon Titan."""
    prompt = f"""Please provide a concise summary of this section of a financial document, 
    focusing on key financial metrics, business performance, and significant developments:

    Text:
    {text}

    Summary:"""

    request_body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 4096,
            "temperature": 0,
            "topP": 1,
            "stopSequences": []
        }
    }

    try:
        response = client.invoke_model(
            modelId="amazon.titan-text-express-v1",
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body.get('results')[0].get('outputText')
    
    except ClientError as e:
        print(f"AWS Error: {e.response['Error']['Message']}")
        return None
    except Exception as e:
        print(f"Error during summarization: {e}")
        return None

def main():
    # Initialize the Bedrock client
    client = create_bedrock_client()
    
    # Specify the path to your test document
    file_path = r"C:\Users\akobe\OneDrive\PolyFinance24\datathon-2024\src\data\Consommation de Base\Couche-Tard\2023-ACT_Annual-Report_FR.txt"
    
    # Read the document
    print("Reading document...")
    document_text = read_document(file_path)
    
    if document_text:
        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=30000,  # Characters per chunk
            chunk_overlap=200,  # Overlap between chunks
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Split text into chunks
        chunks = text_splitter.split_text(document_text)
        print(chunks)
        print(f"\nSplit document into {len(chunks)} chunks")
        
        # Summarize each chunk
        summaries = []
        for i, chunk in enumerate(chunks, 1):
            print(f"\nProcessing chunk {i}/{len(chunks)}...")
            summary = summarize_chunk(client, chunk)
            if summary:
                summaries.append(summary)
                print(f"Completed chunk {i}")
        
        # Combine all summaries
        if summaries:
            print("\nAll chunks processed. Saving results...")
            full_summary = "\n\n=== Next Section ===\n\n".join(summaries)
            
            # Save the combined summaries
            with open("document_summary.txt", "w", encoding='utf-8') as f:
                f.write(full_summary)
            print("\nSummary saved to document_summary.txt")

if __name__ == "__main__":
    main()