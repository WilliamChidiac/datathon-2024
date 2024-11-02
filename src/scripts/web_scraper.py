import requests
from bs4 import BeautifulSoup

def fetch_company_report(ticker):
    # Replace 'ticker' with the actual company ticker symbol
    url = f"https://www.morningstar.com/stocks/xnas/{ticker}/quote"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    
    # Send a GET request to the company's quote page
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # Parse the content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the link to the full company report
        report_link = soup.find('a', text='Read Company Report')
        
        if report_link:
            # Construct the report URL
            report_url = "https://www.morningstar.com" + report_link['href']
            print(f"Full Company Report URL: {report_url}")
            
            # Fetch the full report
            report_response = requests.get(report_url, headers=headers)
            if report_response.status_code == 200:
                report_soup = BeautifulSoup(report_response.content, 'html.parser')
                
                # Extract report content - customize these selectors as needed
                report_content = report_soup.find_all('section', class_='report-section')
                
                # Process the report sections
                for section in report_content:
                    print(section.get_text(strip=True))
            else:
                print("Failed to retrieve the full report.")
        else:
            print("Company report link not found.")
    else:
        print("Failed to retrieve the company quote page.")

# Example usage
if __name__ == "__main__":
    ticker_symbol = "AAPL"  # Example ticker for Apple Inc.
    fetch_company_report(ticker_symbol)
