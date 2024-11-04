# Financial Dashboard & Document Summarizer

## Overview

The **Financial Dashboard & Document Summarizer** is a Streamlit application that leverages AWS services and language models to analyze specific stocks and summarize long and complicated financial documents. An initial dashboard allows users to see relevant information about the stock, and allows the user to interact with an AI Agent who is an expert in financial analysis. The app also allows users to upload PDF documents, processes them using AI, and generates structured summaries focusing on key financial metrics, business performance, risks, and strategic initiatives.

## Features

- **Document Upload**: Users can upload PDF documents for analysis.
- **AI-Powered Summarization**: Utilizes AWS Foundation Models for generating summaries.
- **Interactive Dashboard**: A user-friendly interface leveraging various APIs and AWS agents - an interactive chat feature lets financial analysts investing stocks using all the data that's at their fingertips.

## Technologies Used

- **Streamlit**: For building the web application.
- **Boto3**: AWS SDK for Python to interact with AWS services.
- **LangChain**: For managing language model interactions and document processing.
- **Chroma**: For vector storage and retrieval of documents.
- **Amazon Bedrock**: For accessing the Titan models for summarization and embeddings.
- **PyPDFLoader**: For loading and processing PDF documents.

# Instructions  

Before running this code there are two things that need to be done:  
1. Install requirements from requirements.txt
2. Set the AWS credentials in the environment variables, any other Secrets are stored in AWS and will be accesses programmatically by the solution.

Once the two steps above have been done, you can proceed to run our application locally. This is done by navigating to src/ and apply the following command in the cmd:
`streamlit run Home.py`  
This will run the application locally, navigate to the specified url in your browser to visualize our solution.
