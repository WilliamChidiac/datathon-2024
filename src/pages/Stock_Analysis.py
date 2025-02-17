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
from scripts import ChatBot
import time
import concurrent.futures
import uuid

AGENT_ALIAS_ID = "FFI0XWNCH7"
AGENT_ID = "BWYEY0HCHS"

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

MAX_WORKERS = 2
@st.cache_resource
def get_executor():
    return concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS)

def set_ticker_system_instructs(ticker_input):
    insights = TickerInsights(ticker_input) # Have to redefine the object here to avoid pickling issues
    info = insights.get_summary()
    obj = ChatBot(
        company_ticker=ticker_input,
        company_name=info.get('longName', 'N/A'),
        industry_name=info.get('sector', 'N/A'),
        sub_sector_name=info.get('industry', 'N/A'),
        country=info.get('country', 'N/A'),
        company_description=info.get('longBusinessSummary', 'N/A'),
        board_members=info.get('companyOfficers', []),
        variables=None,
        search_selection=None, # Auto select all search features
    )
    obj.build_instructions()
    print("Finished building system instructions")
    return obj.system_instructs

class StockDashboard:
    def __init__(self):
        st.set_page_config(page_title="Stock Analysis", layout="wide")
        
        # Initialize stock analysis
        col1, _ = st.columns([0.3, 0.7])
        with col1:
            self.ticker_input = st.text_input("Enter Ticker Symbol", "AAPL")
        self.insights = TickerInsights(self.ticker_input)

        st.session_state.ticker = self.ticker_input

        if "ticker_system_instructs" not in st.session_state:
            st.session_state['ticker_system_instructs'] = {}
        if "ticker_ai_overview" not in st.session_state:
            st.session_state['ticker_ai_overview'] = {}
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "futures" not in st.session_state:
            st.session_state.futures = {}
        if "instructs_loading" not in st.session_state:
            st.session_state.instructs_loading = dict()

        # Check if the ticker_input is new and not being processed, then start a new background thread
        if (self.ticker_input not in st.session_state['ticker_system_instructs']) and (self.ticker_input not in st.session_state.instructs_loading):
            print(f"Starting background thread for {self.ticker_input}")
            st.session_state.instructs_loading[self.ticker_input] = True
            future = get_executor().submit(set_ticker_system_instructs, self.ticker_input)
            st.session_state.futures[self.ticker_input] = future
        
    def display_summary(self):
        info = self.insights.get_summary()
        
        col1, col2, col3= st.columns(3)
        with col1:
            st.metric("Current Price", f"${info.get('currentPrice', 'N/A')}")
        with col2:
            st.metric("Market Cap", f"${info.get('marketCap', 'N/A'):,}")
        with col3:
            st.metric("52 Week High", f"${info.get('fiftyTwoWeekHigh', 'N/A')}")

    def get_ticker_system_instructs(self):
        info = self.insights.get_summary()
        obj = ChatBot(
            company_ticker=self.ticker_input,
            company_name=info.get('longName', 'N/A'),
            industry_name=info.get('sector', 'N/A'),
            sub_sector_name=info.get('industry', 'N/A'),
            country=info.get('country', 'N/A'),
            company_description=info.get('longBusinessSummary', 'N/A'),
            variables=None,
            search_selection=None, # Auto select all search features
        )
        obj.build_instructions()
        st.session_state['ticker_system_instructs'][self.ticker_input] = obj.system_instructs

    def display_company_info(self):
        info = self.insights.get_summary()
        st.markdown("Overview")
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
        if self.ticker_input not in st.session_state['ticker_system_instructs']:
            self.wait_for_system_instructs()
            self.generate_ticker_overview() # To create initial overview for user + get a bunch of info into the chatbot context
            st.rerun() # Rerun the script to display the chat

        if st.button("Start a New Chat"):
            with st.spinner("Resetting chat..."):
                time.sleep(1)
            st.session_state.messages = []  # Clear the chat history
            # Store unique session ID for usage throughout the chat
            st.session_state['session_id'] = str(uuid.uuid4()) 
            st.session_state['is_chat_reset'] = True

        chat_container = st.container()

        # Display chat messages
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            if not st.session_state.messages:
                with st.chat_message("assistant"):
                    start_message = f"Hey there! I'm your personal financial analysis assistant. \n\nI've been specialized in financial analysis and have access to a lot of different types of data about this stock, including the information shown on this dashboard. \n\nAsk me any questions about this stock, its competitors, or the industry and we can start analyzing together! 🚀\n\n\n\n**To get started, here's an overview of the ticker you're interested in:**\n\n{st.session_state['ticker_ai_overview'][self.ticker_input]}"
                    if 'is_chat_reset' in st.session_state and st.session_state['is_chat_reset']:
                        st.write(start_message)
                    else:
                        st.write_stream(self.stream_data(start_message))
                    st.session_state.messages.append({"role": "assistant", "content": start_message})

        # Chat input
        if prompt := st.chat_input("What would you like to know about this stock?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

            # Get LLM response
            with chat_container:
                with st.chat_message("assistant"):

                    with st.spinner("Thinking..."):
                        response = self.get_llm_response(prompt)
                    
                    assistant_message = {'role': 'assistant', 'content': response}
                    st.session_state.messages.append(assistant_message)
                    st.write_stream(self.stream_data(response))
    
    def stream_data(self, data):
        for word in data.split(" "):
            yield word + " "
            time.sleep(0.02)

    def wait_for_system_instructs(self):
        future = st.session_state.futures.get(self.ticker_input)
        if not future:
            return

        stages = [
            ("Searching the web for relevant information...", 15),
            ("Building a profile for the target ticker...", 30),
            ("Cleaning my room...", 45),
            ("Formatting...", None)
        ]

        for message, max_time in stages:
            with st.spinner(message):
                start_time = time.time()
                while not future.done():
                    if max_time and (time.time() - start_time) > max_time:
                        break
                    time.sleep(0.1)
                if future.done():
                    st.session_state['ticker_system_instructs'][self.ticker_input] = future.result()
                    _ = st.session_state.instructs_loading.pop(self.ticker_input)
                    return
                
    def generate_ticker_overview(self):
        initial_prompt = st.session_state['ticker_system_instructs'][self.ticker_input]
        agent_client = boto3.client('bedrock-agent-runtime')

        st.session_state['session_id'] = str(uuid.uuid4())

        with st.spinner("Generating overview..."):
            response = agent_client.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                inputText=initial_prompt,
                sessionId=st.session_state['session_id'],
            )
            # Format response for display
            agent_answer = ''
            for event in response['completion']:
                if 'chunk' in list(event.keys()):
                    agent_answer += event['chunk']['bytes'].decode('utf-8')

            agent_answer = agent_answer.replace("$", "\\$") # Escape dollar signs for markdown
            print(f"Overview generated: {agent_answer}")
        
            st.session_state["ticker_ai_overview"][self.ticker_input] = agent_answer

    def get_llm_response(self, prompt):
        try:
            # Prepare message payload for Claude
            agent_client = boto3.client('bedrock-agent-runtime')

            response = agent_client.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                inputText=prompt,
                sessionId=st.session_state['session_id'],
            )

            # Format response for display
            agent_answer = ''
            for event in response['completion']:
                if 'chunk' in list(event.keys()):
                    agent_answer += event['chunk']['bytes'].decode('utf-8')
            agent_answer = agent_answer.replace("$", "\\$") # Escape dollar signs for markdown
            return agent_answer

        except Exception as e:
            print(f"Error getting response: {str(e)}")
            return "I'm sorry, I encountered an issue while generating the answer. Please try again later."

    def run(self):
        st.title(f"Financial Dashboard - {self.ticker_input}")
        
        self.display_summary()

        if st.toggle("AI Powered Interactive chat"):
            # Add some helpful information
            with st.expander("📌 Tips for best results"):
                st.markdown("""
                - Ask clear questions for better responses
                - Ask questions about the company or its financial outlook
                - Ask questions about competitors or industry trends
                - Use the chat to brainstorm analysis ideas
                - Ask questions about the data displayed on the dashboard
                - Have fun! 🚀
                """)
            self.display_chat() 
        else:
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Description","Price History", "Recommendations", "Earnings", "Board Members"])
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

if __name__ == "__main__":
    dashboard = StockDashboard()
    dashboard.run()
