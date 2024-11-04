import streamlit as st
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import boto3
import json
import yfinance as yf
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import boto3
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_aws import BedrockEmbeddings, BedrockLLM
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Chroma
import tempfile
import os

class TickerInsights:
    def __init__(self, ticker):
        self.ticker : str = ticker
        self.ticker_obj : yf.Ticker = yf.Ticker(ticker)
        print(f"TickerInsights object created for {ticker}")
    
    def get_summary(self):
        return self.ticker_obj.info
    
    def get_historical_data(self, period='1y'):
        return self.ticker_obj.history(period=period)
    
    def get_recommendations(self):
        return self.ticker_obj.recommendations
    
    def get_earnings(self):
        return self.ticker_obj.income_stmt
    
    def get_dividends(self):
        return self.ticker_obj.dividends
    
class StockDashboard:
    def __init__(self):
        st.set_page_config(page_title="Stock Analysis", layout="wide")
        
        # Initialize AWS session
        self.aws_session = boto3.Session()
        
        # Initialize stock analysis
        self.ticker_input = st.text_input("Enter Ticker Symbol", "AAPL")
        self.insights = TickerInsights(self.ticker_input)
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
    

    def display_summary(self):
        info = self.insights.get_summary()
        
        col1, col2, col3= st.columns(3)
        with col1:
            st.metric("Current Price", f"${info.get('currentPrice', 'N/A')}")
        with col2:
            st.metric("Market Cap", f"${info.get('marketCap', 'N/A'):,}")
        with col3:
            st.metric("52 Week High", f"${info.get('fiftyTwoWeekHigh', 'N/A')}")

    def display_company_info(self):
        info = self.insights.get_summary()
        st.write(info.get('longBusinessSummary', 'No description available'))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Sector", info.get("sector", "N/A"))
            st.metric("Industry", info.get("industry", "N/A"))
        with col2:
            website = info.get("website", "N/A")
            if website != "N/A":
                st.markdown("Website")
                st.markdown(f"<a href='{website}' style='font-size: 24px'>{website}</a>", unsafe_allow_html=True)
            else:
                st.metric("Website", "No website available")
            st.metric("Country", info.get("country", "N/A"))
    
    def display_board_members(self):
        info = self.insights.get_summary()
        board_members : list[dict] = info.get('companyOfficers', [])
        if board_members == []:
            st.markdown("No board members available")
            return
        column = st.columns(3)
        index = 0
        for member in board_members:
            with column[index % 3]:
                name = member.get('name', 'N/A')
                google_search = f"https://www.google.com/search?q={name.replace(' ', '+').replace("'", "%27")}"
                st.markdown(f"**<a href='{google_search}' style='font-size: 24px; color: #1e88e5;'>{name}</a>-{member.get('title', 'N/A')}**", unsafe_allow_html=True)
                st.markdown(f"year of birth : {member.get('yearBorn', 'N/A')} ({member.get('age', 'N/A')} years old)")
                st.markdown(f"fiscal year: {member['fiscalYear']}")
                st.markdown(f"total pay: {member.get('totalPay', 'N/A')}")
                st.markdown(f"exercised value: {member.get('exercisedValue', 'N/A')}")
                st.markdown(f"unexercised value: {member.get('unexercisedValue', 'N/A')}")
                st.markdown(f"---")
            index += 1


    def plot_historical_data(self):
        df = self.insights.get_historical_data()
        fig = go.Figure(data=[
            go.Candlestick(x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])
        ])
        fig.update_layout(title="Stock Price History")
        st.plotly_chart(fig, use_container_width=True)
        
    def plot_recommendations(self):
        df = self.insights.get_recommendations()
        if isinstance(df, pd.DataFrame) and not df.empty:
            plot_df = df.iloc[0].drop('period').reset_index()
            plot_df.columns = ['Grade', 'Count']
            fig = px.bar(plot_df,  
                        x='Grade', y='Count', 
                        title="Analyst Recommendations")
            fig.update_layout(
            xaxis_title="Recommendation Grade",
            yaxis_title="Number of Analysts"
            )
            st.plotly_chart(fig, use_container_width=True)
            
    def plot_earnings(self):
        earnings = self.insights.get_earnings()
        if earnings is not None:
            df = pd.DataFrame(earnings)
            fig = px.bar(df, title="Yearly Earnings")
            st.plotly_chart(fig, use_container_width=True)
            
    def display_chat(self):
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("What would you like to know about this stock?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get LLM response
            with st.chat_message("assistant"):
                
                response = self.get_llm_response(prompt, st.session_state.messages)
                
                st.session_state.messages.append(response)
                st.markdown(response)
    
    
    def get_llm_response(self, prompt, system_instructs :str = "stock", past_responses : list = []):
        claude_model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        messages = [{
            "role": "user",
            "content": prompt
        }]
        if past_responses is not None:
            messages = past_responses + messages
        try:
            # Prepare message payload for Claude

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": 1000,
                "system": system_instructs,
                "messages": messages,
                "temperature": 0.8,
            })
            
            bedrock = boto3.client('bedrock-runtime')
            
            # Invoke Claude model
            response = bedrock.invoke_model(
                modelId=claude_model_id,
                body=body
            )

            # Decode response
            resp = json.loads(response['body'].read().decode('utf-8'))

            # Extract assistant response
            prev_answer = {
                "role": resp['role'],
                "content": resp['content'][0]['text']
            }

            print(f"Previous answer: {prev_answer}")
            print(f"Messages: {messages}")

            conversation_thread = messages + [prev_answer]

            return {
                'response': prev_answer['content'],
                'past_responses': conversation_thread
            }

        except Exception as e:
            print(f"Error getting response: {str(e)}")

    def run(self):
        st.title(f"Financial Dashboard - {self.ticker_input}")
        
        self.display_summary()
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Description","Price History", "Recommendations", "Earnings", "Board Members", "Chat"])
        with tab1:
            self.display_company_info()
        with tab2:
            self.plot_historical_data()
        with tab3:
            self.plot_recommendations()
        with tab4:
            self.plot_earnings()
        with tab5:
            self.display_board_members()
        with tab6:
            self.display_chat()



if __name__ == "__main__":
    dashboard = StockDashboard()
    dashboard.run()