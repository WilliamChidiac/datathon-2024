# Financial Dashboard & Document Summarizer

## Overview

The **Financial Dashboard & Document Summarizer** is a Streamlit application that leverages AWS services and language models to analyze specific stocks and summarize long and complicated financial documents. An initial dashboard allows users to see relevant information about the stock, and allows the user to interact with an AI Agent who is an expert in financial analysis. The app also allows users to upload PDF documents, processes them using AI, and generates structured summaries focusing on key financial metrics, business performance, risks, and strategic initiatives.

### Technologies Used

- **Streamlit**: For building the web application.
- **Boto3**: AWS SDK for Python to interact with AWS services.
- **LangChain**: For managing language model interactions and document processing.
- **Chroma**: For vector storage and retrieval of documents.
- **Amazon Bedrock - Foundation models**: For accessing the Titan models for summarization and embeddings.
- **Amazon Bedrock - Agents**: In order to create a financial analysis expert who has access to real-time information.
- **PyPDFLoader**: For loading and processing PDF documents.
- **Tavily**: For searching up relevant real-time information about the stock

### Instructions  

Before running this code there are two things that need to be done:  
1. Install requirements from requirements.txt
2. Set the AWS credentials in the environment variables, any other Secrets are stored in AWS and will be accesses programmatically by the solution.

Once the two steps above have been done, you can proceed to run our application locally. This is done by navigating to src/ and apply the following command in the cmd:
`streamlit run Home.py`  
This will run the application locally, navigate to the specified url in your browser to visualize our solution.

# Details

Our solution aims to solve three inefficiencies for financial analysts:
- **Data aggregation**
- **Data summarization**
- **Data insight**

We have addressed these inefficiencies by creating the following components:
1. **Dashboard** - Performs data aggregation and visualization.
2. **Financial Document Agent** - Provides data summarization and insights on large financial documents.
3. **Financial Analyst Chatbot** - Offers data summarization and insights from various sources.

---

## Dashboard

The Dashboard uses `yfinance-python` to aggregate relevant statistics and visualize them. It includes several tabs:
- **Overview** - Company description with a link to the company's investor website.
- **Historical Price Movement** - Displays OHLC + volume data.
- **Analyst Recommendations** - Buy, hold, or sell recommendations.
- **Company Earnings**
- **Board Members** - Provides a quick Google search link for each board member.

This dashboard enables financial analysts to begin forming ideas about the ticker based on the displayed data.

---

## Financial Document Agent

Utilizes Bedrock foundation models and LangChain for financial document analysis. The structure of the generated analysis includes:
- **Financial Highlights**
- **Business Performance**
- **Key Risks**
- **Strategic Initiatives**
- **Outlook**

This structure gives financial analysts a concise, pertinent overview of the document, allowing them to quickly enhance their understanding. The document parsing is handled through LangChain.

---

## Financial Analyst Chatbot

### Overview
Our chatbot leverages both Bedrock Agents and external API information to assist financial analysts in their analyses. It builds an initial profile on the target company, including:
- Recent innovations
- Quarterly outlook
- Social mentions (positive and negative)
- Competitors
- Industry trends
- Sub-sector trends
- Country of origin trends
- Global economic trends
- Board of directors

After establishing this context, the agent uses RAG and custom actions to respond to user queries in a multi-turn conversation.

### Data Sources
- **yfinance API** - Same data as used in the dashboard.
- **Tavily Search API** - Optimized for LLM usage.

This data is aggregated to create a “profile” of the target ticker, which is then passed to the chatbot at the start of the conversation. This allows the Agent to develop intuition and context about the ticker's outlook.

### Bedrock Agent
The Bedrock Agent includes:
- **RAG**
- **Custom actions**

The agent is tailored for financial analysis, equipped with textbooks on financial analysis and portfolio management to ensure best practices. It can also perform custom web searches for real-time data when relevant. However, this functionality was recently disabled due to permission issues.

---

## Sentiment Analysis

*Details on sentiment analysis were not provided but could be added here.*

---

## Future Development

Key areas for future development include:

### Financial Document Agent
- Adding functionality to handle Excel documents.

### Dashboard
- Expanding the range of graphs and data displayed.

### Financial Analyst Chatbot
- Debugging and re-enabling the custom web search action.
- Adding custom actions for additional financial APIs.
- Add user file upload and file handling

Additional potential developments include a “comparison agent” to provide structured outlooks on:
- Market dominance among specific industry competitors.
- Trends within a specific sub-sector.


