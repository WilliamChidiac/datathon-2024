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
from scripts.web_search.companyChatbot import companyChatbot
import time
import concurrent.futures

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
    obj = companyChatbot(
        company_ticker=ticker_input,
        company_name=info.get('longName', 'N/A'),
        industry_name=info.get('sector', 'N/A'),
        sub_sector_name=info.get('industry', 'N/A'),
        country=info.get('country', 'N/A'),
        company_description=info.get('longBusinessSummary', 'N/A'),
        variables=None,
        search_selection=None, # Auto select all search features
    )
    obj.build_instructions()
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
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "futures" not in st.session_state:
            st.session_state.futures = {}

        # Check if the ticker_input is new and start the background thread
        if self.ticker_input not in st.session_state['ticker_system_instructs']:
            print(f"Starting background thread for {self.ticker_input}")
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
        obj = companyChatbot(
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
        chat_container = st.container()

        if st.session_state.messages: # If messages are not empty, new chat button appears
            if st.button("Start a New Chat"):
                st.session_state.messages = []  # Clear the chat history

        # Display chat messages
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

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
                    
                    if self.ticker_input not in st.session_state['ticker_system_instructs']:
                        self.wait_for_system_instructs()

                    system_instructs = st.session_state['ticker_system_instructs'][self.ticker_input]
                    with st.spinner("Thinking..."):
                        response = self.get_llm_response(prompt, system_instructs, st.session_state.messages)
                    
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
                    return
                
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

            return resp['content'][0]['text']

        except Exception as e:
            print(f"Error getting response: {str(e)}")
            return "I'm sorry, I encountered an issue while generating the answer. Please try again later."

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