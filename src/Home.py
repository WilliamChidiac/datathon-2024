import streamlit as st
import plotly.graph_objects as go
import numpy as np

def create_animated_chart():
    # Generate sample data
    x = np.linspace(0, 10, 100)
    y1 = np.sin(x) * np.exp(x/10)
    y2 = np.cos(x) * np.exp(x/10)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x, y=y1,
        mode='lines',
        line=dict(color='#00ff00', width=2),
        fill='tonexty'
    ))
    
    fig.add_trace(go.Scatter(
        x=x, y=y2,
        mode='lines',
        line=dict(color='#ff00ff', width=2),
        fill='tonexty'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title={
            'text': 'Financial Analytics Dashboard',
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=30, color='white')
        },
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=400
    )
    
    return fig

def main():
    # Page configuration
    st.set_page_config(
        page_title="Financial Analyst Assistant",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            background-color: #0e1117;
        }
        .stButton>button {
            background-color: #00ff00;
            color: black;
            font-weight: bold;
            border-radius: 20px;
            padding: 15px 30px;
            border: none;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background-color: #ff00ff;
            transform: scale(1.05);
        }
        .big-text {
            font-size: 60px !important;
            font-weight: bold !important;
            background: linear-gradient(45deg, #00ff00, #ff00ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding: 20px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<p class="big-text">Financial Analyst Assistant</p>', unsafe_allow_html=True)
    
    # Animated chart
    st.plotly_chart(create_animated_chart(), use_container_width=True)
    
    # Features section
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Stock Analysis")
        st.markdown("""
        Dive deep into stock market data with our comprehensive analysis tools:
        - Real-time stock price tracking
        - Technical indicators
        - Company financials
        - Chat with a bot
        """)
        if st.button("Go to Stock Analysis", key="stock_btn"):
            st.switch_page("pages/Stock_Analysis.py")

    with col2:
        st.markdown("### 📄 Document Summarizer")
        st.markdown("""
        Transform complex financial documents into actionable insights:
        - AI-powered summarization
        - Key metrics extraction
        - Risk analysis
        - Strategic recommendations
        """)
        if st.button("Go to Document Summarizer", key="doc_btn"):
            st.switch_page("pages/Document_Summarizer.py")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>Powered by LangChain, AWS Bedrock, and Streamlit</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()