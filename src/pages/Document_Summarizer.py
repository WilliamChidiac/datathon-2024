import streamlit as st
import boto3
import yfinance as yf
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_aws import BedrockEmbeddings, BedrockLLM
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
import tempfile
import os

class DocumentSummarizer:
    def __init__(self, session):
        self.session = session
        
        # Create bedrock-runtime client from session
        self.bedrock_client = self.session.client(
            service_name='bedrock-runtime',
            region_name=self.session.region_name
        )
        # Initialize LLM and embeddings
        self.llm = BedrockLLM(
            model_id="amazon.titan-text-express-v1",
            client=self.bedrock_client,
            model_kwargs={"maxTokenCount": 4096}
        )
        
        self.embeddings = BedrockEmbeddings(
            client=self.bedrock_client,
            model_id="amazon.titan-embed-text-v1"
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

        # Create a temporary directory for Chroma
        self.persist_directory = tempfile.mkdtemp()

    def process_document(self, file):
        """Process uploaded document and create vector store"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(file.getvalue())
                tmp_file_path = tmp_file.name

            # Load and split document
            loader = PyPDFLoader(tmp_file_path)
            pages = loader.load()
            splits = self.text_splitter.split_documents(pages)
            
            # Create vector store
            vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            return vectorstore

        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")

    def generate_summary(self, vectorstore):
        """Generate financial document summary"""
        try:

            summary_prompt = PromptTemplate(
                template="""You are a financial analyst. Please provide a comprehensive summary of the following financial document. 
                Focus on key financial metrics, business performance, risks, and strategic initiatives.
                
                Document content: {context}
                
                Please structure the summary as follows:
                1. Financial Highlights
                2. Business Performance
                3. Key Risks
                4. Strategic Initiatives
                5. Outlook
                
                Summary:""",
                input_variables=["context"]
            )

            summary_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=summary_prompt
            )

            relevant_docs = vectorstore.similarity_search(
                "What are the main financial highlights and business performance?",
                k=5
            )
            
            summary = summary_chain.invoke({
                "context": relevant_docs
            })

            return summary
        except Exception as e:
            raise Exception(f"Error generating summary: {str(e)}")

    def __del__(self):
        """Cleanup temporary directory when object is destroyed"""
        try:
            import shutil
            shutil.rmtree(self.persist_directory, ignore_errors=True)
        except:
            pass

class DocumentAnalysisDashboard:
    def __init__(self):
        st.set_page_config(page_title="Document Summarizer", layout="wide")
        
        # Initialize AWS session
        self.aws_session = boto3.Session()
        
        # Initialize document summarizer
        self.summarizer = DocumentSummarizer(self.aws_session)
        
        # Custom styling
        st.markdown("""
            <style>
            .upload-box {
                border: 2px dashed #00ff00;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                margin: 20px 0;
            }
            </style>
        """, unsafe_allow_html=True)

    def run(self):
        st.title("Financial Document Analyzer")
        
        # Document upload section
        st.markdown("### Upload Your Financial Documents")
        st.markdown("Upload annual reports, financial statements, or other financial documents for AI-powered analysis.")
        
        uploaded_file = st.file_uploader("Drop your document here", type="pdf")
        
        if uploaded_file:
            try:
                with st.spinner("Processing document..."):
                    # Process document
                    vectorstore = self.summarizer.process_document(uploaded_file)
                    
                    # Generate summary
                    summary = self.summarizer.generate_summary(vectorstore)
                    
                    # Display results
                    st.success("Document processed successfully!")
                    
                    # Display summary in a nice format
                    st.markdown("### Document Summary")
                    st.markdown(summary)
                    
                    # Add download button for summary
                    st.download_button(
                        label="Download Summary",
                        data=summary,
                        file_name="document_summary.txt",
                        mime="text/plain"
                    )
                    
            except Exception as e:
                st.error(f"Error processing document: {str(e)}")
        
        # Add some helpful information
        with st.expander("📌 Tips for best results"):
            st.markdown("""
            - Upload clear, text-searchable PDFs
            - Ensure documents are in English
            - Larger documents may take longer to process
            - For best results, use official financial documents
            """)

if __name__ == "__main__":
    dashboard = DocumentAnalysisDashboard()
    dashboard.run()