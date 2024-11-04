# !pip install setuptools==67.8.0
# !pip install transformers feedparser --use-deprecated=legacy-resolver yfinance

import feedparser
import yfinance as yf
import matplotlib.pyplot as plt
from transformers import pipeline
from statistics import mean

# Load the FinBERT model
pipe = pipeline("text-classification", model="ProsusAI/finbert")

def get_ticker(company_name):
    """
    Retrieves the ticker symbol for a given company name.
    """
    try:
        ticker = yf.Ticker(company_name).ticker
        return ticker 
    except Exception as e:
        print(f"Error fetching ticker: {e}")
        return None

def fetch_news(ticker):
    """
    Fetches financial news articles from RSS feeds for a given ticker symbol.
    """
    rss_feeds = [
        f'https://finance.yahoo.com/rss/headline?s={ticker}'
    ]
    
    articles = []
    for rss_url in rss_feeds:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            articles.append(entry)
    return articles

def analyze_sentiment(articles, keyword):
    """
    Analyzes sentiment of news articles filtered by a keyword.
    """
    total_score = 0
    num_articles = 0
    sentiment_scores = []

    for entry in articles:
        print(f"Title: {entry.title}")
        print(f"Summary: {entry.summary if 'summary' in entry else 'No summary available'}")
        print('-' * 40)

        if keyword.lower() not in entry.summary.lower():
            continue

        sentiment = pipe(entry.summary)[0]
        score = sentiment["score"] if sentiment["label"] == 'positive' else -sentiment["score"]
        sentiment_scores.append(score)
        total_score += score
        num_articles += 1

    return sentiment_scores, total_score, num_articles

def plot_sentiment_trend(sentiment_scores):
    """
    Plots the sentiment trend across the articles.
    """
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(sentiment_scores)), sentiment_scores, marker='o')
    plt.title('Sentiment Trend Over Articles')
    plt.xlabel('Article Number')
    plt.ylabel('Sentiment Score')
    plt.axhline(y=0, color='gray', linestyle='--')
    plt.show()

def detect_anomalies(sentiment_scores):
    """
    Detects anomalies in sentiment scores based on the mean score.
    """
    avg_sentiment = mean(sentiment_scores)
    threshold = 2 * abs(avg_sentiment)
    anomalies = [(i, score) for i, score in enumerate(sentiment_scores) if abs(score - avg_sentiment) > threshold]

    if anomalies:
        print("\nAnomalies detected in sentiment scores:")
        for idx, score in anomalies:
            print(f"Article {idx + 1}: Sentiment Score = {score:.2f}")
    else:
        print("\nNo significant anomalies detected.")

def finbert_sentiment_analysis(company_name, keyword):
    """
    Main function to execute sentiment analysis for a given company and keyword.
    """
    ticker = get_ticker(company_name)
    if not ticker:
        print("Ticker not found. Please try a different company name.")
        return

    print(f"Using ticker: {ticker}")
    articles = fetch_news(ticker)
    print(articles)
    sentiment_scores, total_score, num_articles = analyze_sentiment(articles, keyword)

    if num_articles > 0:
        final_score = total_score / num_articles
        overall_sentiment = "Positive" if final_score >= 0.15 else "Negative" if final_score <= -0.15 else "Neutral"
        print(f'Overall sentiment: {overall_sentiment} ({final_score:.2f})')
        
        plot_sentiment_trend(sentiment_scores)
        detect_anomalies(sentiment_scores)
    else:
        print("No articles matched the keyword.")

if __name__ == "__main__":
    company_name = input("Enter the company name: ")
    keyword = input("Enter a keyword to filter articles (e.g., 'meta'): ")
    finbert_sentiment_analysis(company_name, keyword)
