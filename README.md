# Financial Dashboard & Document Summarizer

## Overview

The **Financial Document Summarizer** is a Streamlit application that leverages AWS services and language models to analyze and summarize financial documents. The app allows users to upload PDF documents, processes them using AI, and generates structured summaries focusing on key financial metrics, business performance, risks, and strategic initiatives.

## Features

- **Document Upload**: Users can upload PDF documents for analysis.
- **AI-Powered Summarization**: Utilizes AWS Foundation Models for generating summaries.
- **Interactive Dashboard**: A user-friendly interface built with Streamlit & chat options.

## Technologies Used

- **Streamlit**: For building the web application.
- **Boto3**: AWS SDK for Python to interact with AWS services.
- **LangChain**: For managing language model interactions and document processing.
- **Chroma**: For vector storage and retrieval of documents.
- **Amazon Bedrock**: For accessing the Titan models for summarization and embeddings.
- **PyPDFLoader**: For loading and processing PDF documents.
