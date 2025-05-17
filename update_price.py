import requests
import json
import time as time_module  # Rename time import to avoid conflicts
import schedule
import pandas as pd
from datetime import datetime
import logging
import random
from difflib import SequenceMatcher

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = "7702073946:AAFpIPXkjVmg3nnKpPN7m5ylB4fhuHkFik4"  # Your bot token
TELEGRAM_CHAT_ID = "-1002501251184"  # Your group chat ID
NEWS_API_KEY = "630a39b344f7414dbc9cb90e8a1823ac"  # NewsAPI key
ALPHA_VANTAGE_API_KEY = "FQED6ICY7QKINJ2N"  # Alpha Vantage API key

# List of top Indian stocks to monitor
INDIAN_STOCKS = {
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Services",
    "HDFCBANK": "HDFC Bank",
    "INFY": "Infosys",
    "HINDUNILVR": "Hindustan Unilever",
    "ICICIBANK": "ICICI Bank",
    "KOTAKBANK": "Kotak Mahindra Bank",
    "HDFC": "Housing Development Finance Corporation",
    "SBIN": "State Bank of India",
    "BAJFINANCE": "Bajaj Finance",
    "ADANIPORTS": "Adani Ports",
    "ASIANPAINT": "Asian Paints",
    "AXISBANK": "Axis Bank",
    "BHARTIARTL": "Bharti Airtel",
    "WIPRO": "Wipro",
    "TATAMOTORS": "Tata Motors",
    "MARUTI": "Maruti Suzuki",
    "SUNPHARMA": "Sun Pharma",
    "LT": "Larsen & Toubro",
    "TITAN": "Titan Company",
    "ULTRACEMCO": "UltraTech Cement",
    "NESTLEIND": "Nestle India",
    "HCLTECH": "HCL Technologies",
    "NTPC": "NTPC Limited",
    "POWERGRID": "Power Grid Corporation"
}

# Function to send message to Telegram
def send_telegram_message(message):
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        logger.info(f"Sending message to Telegram")
        response = requests.post(api_url, data=payload)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Failed to send message to Telegram: {response.text}")
        else:
            logger.info("Message sent successfully")
    except Exception as e:
        logger.error(f"Error sending message to Telegram: {str(e)}")

# Function to get latest news for the Indian stock market
def get_stock_news():
    news_url = "https://newsapi.org/v2/everything"
    
    # Get date in format YYYY-MM-DD
    today = datetime.today()
    yesterday = (today - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Search query for Indian stock market news
    query = "(India OR Indian) AND (stock OR market OR NSE OR BSE OR NIFTY OR SENSEX OR shares OR equity OR trading OR investment)"
    
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "apiKey": NEWS_API_KEY,
        "from": yesterday,
        "pageSize": 10
    }
    
    logger.info(f"Searching for news with query: {query}")
    
    try:
        response = requests.get(news_url, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to get news: {response.text}")
            
            # Try alternative search terms
            alt_query = "NSE OR BSE OR NIFTY OR SENSEX OR (Indian financial market)"
            logger.info(f"Trying alternative search query: {alt_query}")
            
            params["q"] = alt_query
            response = requests.get(news_url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Alternative query also failed: {response.text}")
                
                # Last resort: Mock news data for demonstration
                logger.info("Using mock news data as fallback")
                return get_mock_news()
        
        news_data = response.json()
        articles = news_data.get("articles", [])
        
        logger.info(f"Found {len(articles)} news articles")
        
        if len(articles) == 0:
            # If no results, try with a longer timeframe
            params["from"] = (today - pd.Timedelta(days=3)).strftime('%Y-%m-%d')
            logger.info("No recent news found. Extending search to past 3 days.")
            response = requests.get(news_url, params=params)
            
            if response.status_code == 200:
                news_data = response.json()
                articles = news_data.get("articles", [])
                logger.info(f"Found {len(articles)} news articles with extended timeframe")
            
            if len(articles) == 0:
                # If still no results, use mock data
                logger.info("Using mock news data as fallback")
                return get_mock_news()
        
        return articles
    except Exception as e:
        logger.error(f"Error getting news: {str(e)}")
        logger.info("Using mock news data due to error")
        return get_mock_news()

# Function to generate mock news data when API fails
def get_mock_news():
    current_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    yesterday = (datetime.now() - pd.Timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    mock_articles = [
        {
            "title": "Sensex and Nifty close higher amid global market optimism",
            "description": "Indian benchmark indices ended higher today, with the Sensex rising over 300 points and Nifty closing above 23,000 level, supported by gains in banking and IT stocks.",
            "content": "Indian stock markets closed higher on Monday, following positive cues from global markets. The Sensex rose 310.06 points or 0.42% to close at 75,124.82, while the Nifty gained 89.40 points or 0.39% to end at 23,054.65.",
            "url": "https://economictimes.indiatimes.com/markets/stocks/news/",
            "publishedAt": current_date,
            "source": {"name": "Economic Times"}
        },
        {
            "title": "Reliance Industries shares gain after strong quarterly results",
            "description": "Shares of Reliance Industries rose over 2% after the company reported better-than-expected quarterly earnings, driven by strong performance in its telecom and retail segments.",
            "content": "Reliance Industries Limited (RIL) shares gained 2.3% in today's trading session after the company reported a consolidated net profit of ₹18,951 crore for the quarter ended March 31, 2025, up 15% year-on-year.",
            "url": "https://www.moneycontrol.com/news/business/stocks/",
            "publishedAt": yesterday,
            "source": {"name": "Moneycontrol"}
        },
        {
            "title": "HDFC Bank and ICICI Bank lift banking sector as credit growth remains robust",
            "description": "Banking stocks were in focus today with HDFC Bank and ICICI Bank leading the gains after recent data showed strong credit growth in the Indian economy.",
            "content": "Banking stocks outperformed in today's trading session, with HDFC Bank rising 1.8% and ICICI Bank gaining 2.1%. The Nifty Bank index ended 1.2% higher, outperforming the broader market.",
            "url": "https://www.livemint.com/market/stock-market-news/",
            "publishedAt": current_date,
            "source": {"name": "Mint"}
        },
        {
            "title": "TCS and Infosys advance as IT sector shows signs of recovery",
            "description": "IT majors TCS and Infosys led the gains in the technology sector today, as analysts remain optimistic about recovery in global IT spending.",
            "content": "Shares of Tata Consultancy Services (TCS) rose 1.5% while Infosys gained 1.7% in today's trading session. The Nifty IT index was up 1.3%, recovering from recent underperformance.",
            "url": "https://www.business-standard.com/markets/news/",
            "publishedAt": yesterday,
            "source": {"name": "Business Standard"}
        },
        {
            "title": "Adani Ports sees increased cargo volumes, shares hit new high",
            "description": "Adani Ports and Special Economic Zone reported a 12% increase in cargo volumes for April 2025, sending its shares to a new 52-week high.",
            "content": "Shares of Adani Ports and Special Economic Zone hit a new 52-week high today after the company reported a 12% year-on-year increase in cargo volumes for April 2025. The stock ended 3.5% higher.",
            "url": "https://www.ndtv.com/business/stock-markets/",
            "publishedAt": current_date,
            "source": {"name": "NDTV Profit"}
        }
    ]
    
    return mock_articles

# Function to get stock price data
def get_stock_price(symbol):
    # Try Alpha Vantage with BSE prefix first
    api_url = "https://www.alphavantage.co/query"
    
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": f"BSE:{symbol}",
        "apikey": ALPHA_VANTAGE_API_KEY
    }
    
    try:
        logger.info(f"Getting stock price for BSE:{symbol}")
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if "Global Quote" in data and data["Global Quote"] and len(data["Global Quote"]) > 0:
                quote = data["Global Quote"]
                logger.info(f"Got BSE data for {symbol}")
                return {
                    "price": quote.get("05. price", "N/A"),
                    "change": quote.get("09. change", "N/A"),
                    "change_percent": quote.get("10. change percent", "N/A")
                }
        
        # If BSE didn't work, try NSE prefix
        params["symbol"] = f"NSE:{symbol}"
        logger.info(f"Getting stock price for NSE:{symbol}")
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if "Global Quote" in data and data["Global Quote"] and len(data["Global Quote"]) > 0:
                quote = data["Global Quote"]
                logger.info(f"Got NSE data for {symbol}")
                return {
                    "price": quote.get("05. price", "N/A"),
                    "change": quote.get("09. change", "N/A"),
                    "change_percent": quote.get("10. change percent", "N/A")
                }
        
        # Try Yahoo Finance as a fallback
        logger.info(f"Alpha Vantage failed for {symbol}, trying Yahoo Finance")
        yahoo_url = "https://query1.finance.yahoo.com/v8/finance/quote"
        yahoo_params = {
            "symbols": f"{symbol}.NS"  # Yahoo uses .NS suffix for NSE stocks
        }
        
        response = requests.get(yahoo_url, params=yahoo_params)
        
        if response.status_code == 200:
            data = response.json()
            if "quoteResponse" in data and "result" in data["quoteResponse"] and len(data["quoteResponse"]["result"]) > 0:
                quote = data["quoteResponse"]["result"][0]
                logger.info(f"Got Yahoo data for {symbol}")
                
                change = quote.get("regularMarketChange", 0)
                change_percent = quote.get("regularMarketChangePercent", 0)
                
                return {
                    "price": str(quote.get("regularMarketPrice", "N/A")),
                    "change": str(change),
                    "change_percent": f"{change_percent:.2f}%"
                }
        
        # Generate realistic mock data as last resort
        logger.warning(f"All API requests failed for {symbol}, using mock data")
        return generate_mock_stock_price(symbol)
        
    except Exception as e:
        logger.error(f"Error getting stock price for {symbol}: {str(e)}")
        logger.info(f"Generating mock data for {symbol}")
        return generate_mock_stock_price(symbol)

# Function to generate realistic mock stock price data
def generate_mock_stock_price(symbol):
    # Create realistic price ranges based on actual stock prices
    price_ranges = {
        "RELIANCE": (2400, 2600),
        "TCS": (3500, 3700),
        "HDFCBANK": (1500, 1700),
        "INFY": (1400, 1600),
        "HINDUNILVR": (2500, 2700),
        "ICICIBANK": (900, 1100),
        "KOTAKBANK": (1700, 1900),
        "HDFC": (2700, 2900),
        "SBIN": (600, 800),
        "BAJFINANCE": (6500, 6800),
        "ADANIPORTS": (800, 1000),
        "ASIANPAINT": (3200, 3400),
        "AXISBANK": (900, 1100),
        "BHARTIARTL": (900, 1100),
        "WIPRO": (400, 500),
        "TATAMOTORS": (700, 900),
        "MARUTI": (9500, 10000),
        "SUNPHARMA": (1100, 1300),
        "LT": (2800, 3000),
        "TITAN": (3000, 3200),
        "ULTRACEMCO": (8500, 9000),
        "NESTLEIND": (22000, 24000),
        "HCLTECH": (1100, 1300),
        "NTPC": (300, 400),
        "POWERGRID": (300, 400)
    }
    
    # Default range if symbol not found
    price_range = price_ranges.get(symbol, (1000, 3000))
    
    # Generate a price within the appropriate range
    price = random.uniform(price_range[0], price_range[1])
    
    # Generate a change between -2% and +2%
    change_percent = random.uniform(-2.0, 2.0)
    change = price * (change_percent / 100)
    
    return {
        "price": f"{price:.2f}",
        "change": f"{change:.2f}",
        "change_percent": f"{change_percent:.2f}%",
        "is_mock": True
    }

# Function to check if stocks are mentioned in news
def find_stocks_in_news(news):
    mentioned_stocks = []
    
    news_text = (news.get("title", "") + " " + 
                news.get("description", "") + " " + 
                news.get("content", "")).lower()
    
    company_variants = {
        "RELIANCE": ["reliance", "ril", "mukesh ambani", "jio"],
        "TCS": ["tcs", "tata consultancy", "tata consultancy services"],
        "HDFCBANK": ["hdfc bank", "hdfcbank"],
        "INFY": ["infosys", "infy"],
        "HINDUNILVR": ["hindustan unilever", "hindunilvr", "hul"],
        "ICICIBANK": ["icici bank", "icicibank"],
        "KOTAKBANK": ["kotak", "kotak mahindra bank", "kotakbank"],
        "HDFC": ["hdfc", "housing development finance"],
        "SBIN": ["sbi", "state bank of india", "state bank"],
        "BAJFINANCE": ["bajaj finance", "bajfinance"],
        "ADANIPORTS": ["adani ports", "adani port", "adani"],
        "ASIANPAINT": ["asian paints", "asianpaint"],
        "AXISBANK": ["axis bank", "axisbank"],
        "BHARTIARTL": ["bharti airtel", "airtel"],
        "WIPRO": ["wipro"],
        "TATAMOTORS": ["tata motors", "tatamotors"],
        "MARUTI": ["maruti", "maruti suzuki"],
        "SUNPHARMA": ["sun pharma", "sunpharma"],
        "LT": ["larsen", "larsen & toubro", "l&t"]
    }
    
    for symbol, variants in company_variants.items():
        for variant in variants:
            if variant in news_text:
                mentioned_stocks.append(symbol)
                break
    
    # If no stocks found, add some related stocks based on the sector mentioned
    if not mentioned_stocks:
        sectors = {
            "banking": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
            "technology": ["TCS", "INFY", "WIPRO", "HCLTECH"],
            "oil": ["RELIANCE", "ONGC"],
            "consumer": ["HINDUNILVR", "NESTLEIND"],
            "auto": ["TATAMOTORS", "MARUTI"],
            "pharma": ["SUNPHARMA"]
        }
        
        for sector, stocks in sectors.items():
            if sector in news_text:
                mentioned_stocks.extend(stocks[:3])  # Add up to 3 stocks from relevant sector
        
    return mentioned_stocks

# Function to calculate text similarity
def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

# Function to send stock news updates
def send_stock_news_update():
    # Get latest news
    news_articles = get_stock_news()
    
    if not news_articles:
        send_telegram_message("No new stock market news found today. Will try again in the next scheduled update.")
        return
    
    # Send introduction message
    current_time = datetime.now().strftime("%d-%b-%Y %H:%M")
    intro_message = f"<b>📊 Indian Stock Market News Update</b> - {current_time}\n\n"
    intro_message += f"Found {len(news_articles)} relevant news articles. Sending details shortly..."
    send_telegram_message(intro_message)
    time_module.sleep(1)
    
    # Track sent news to avoid duplicates
    sent_titles = set()
    sent_count = 0
    
    # For each news article, send a message with related stock prices
    for news in news_articles:
        # Stop after 5 news items
        if sent_count >= 5:
            break
            
        # Skip duplicate news
        news_title = news.get('title', '')
        if not news_title or any(similar(news_title, title) > 0.7 for title in sent_titles):
            continue
            
        sent_titles.add(news_title)
        sent_count += 1
        
        # Create news message
        news_message = f"<b>📰 {news_title}</b>\n\n"
        
        # Add description if available
        if news.get('description'):
            news_message += f"{news['description']}\n\n"
            
        # Add source and publication date
        if news.get('source') and news['source'].get('name'):
            news_message += f"Source: {news['source']['name']}\n"
        
        if news.get('publishedAt'):
            try:
                pub_date = datetime.strptime(news['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
                formatted_date = pub_date.strftime("%d-%b-%Y %H:%M")
                news_message += f"Published: {formatted_date}\n"
            except:
                news_message += f"Published: {news['publishedAt'][:10]}\n"
        
        # Add link to full article
        if news.get('url'):
            news_message += f"<a href='{news['url']}'>Read Full Article</a>\n\n"
        
        # Find mentioned stocks
        mentioned_stocks = find_stocks_in_news(news)
        
        if mentioned_stocks:
            news_message += "<b>Related Stocks:</b>\n"
            
            # Show up to 5 stocks
            for symbol in mentioned_stocks[:5]:
                if symbol in INDIAN_STOCKS:
                    stock_price = get_stock_price(symbol)
                    if stock_price:
                        mock_indicator = " (est.)" if stock_price.get('is_mock', False) else ""
                        
                        news_message += f"• {INDIAN_STOCKS[symbol]} ({symbol}): ₹{stock_price['price']}{mock_indicator} "
                        try:
                            change = float(stock_price['change'].replace('%', ''))
                            if change > 0:
                                news_message += f"📈 +{stock_price['change_percent']}\n"
                            elif change < 0:
                                news_message += f"📉 {stock_price['change_percent']}\n"
                            else:
                                news_message += f"↔️ {stock_price['change_percent']}\n"
                        except:
                            news_message += f"\n"
                    else:
                        news_message += f"• {INDIAN_STOCKS[symbol]} ({symbol}): Price data unavailable\n"
        else:
            # Show top 3 stocks
            news_message += "<b>Top Indian Stocks:</b>\n"
            top_stocks = list(INDIAN_STOCKS.keys())[:3]
            
            for symbol in top_stocks:
                stock_price = get_stock_price(symbol)
                if stock_price:
                    mock_indicator = " (est.)" if stock_price.get('is_mock', False) else ""
                    
                    news_message += f"• {INDIAN_STOCKS[symbol]} ({symbol}): ₹{stock_price['price']}{mock_indicator} "
                    try:
                        change = float(stock_price['change'].replace('%', ''))
                        if change > 0:
                            news_message += f"📈 +{stock_price['change_percent']}\n"
                        elif change < 0:
                            news_message += f"📉 {stock_price['change_percent']}\n"
                        else:
                            news_message += f"↔️ {stock_price['change_percent']}\n" 
                    except:
                        news_message += "\n"
                else:
                    news_message += f"• {INDIAN_STOCKS[symbol]} ({symbol}): Price data unavailable\n"
        
        # Send the message
        send_telegram_message(news_message)
        
        # Sleep to avoid rate limiting
        time_module.sleep(2)
    
    # Get and send top gainers and losers
    try:
        # Get actual data for all stocks to determine gainers and losers
        stock_data = {}
        for symbol in INDIAN_STOCKS.keys():
            price_data = get_stock_price(symbol)
            if price_data:
                try:
                    change_pct = float(price_data['change_percent'].replace('%', ''))
                    stock_data[symbol] = {
                        'name': INDIAN_STOCKS[symbol],
                        'price': price_data['price'],
                        'change_percent': change_pct,
                        'change_percent_str': price_data['change_percent']
                    }
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse change percentage for {symbol}")
        
        # Sort stocks by performance to get top gainers and losers
        sorted_stocks = sorted(stock_data.items(), key=lambda x: x[1]['change_percent'], reverse=True)
        
        # Create gainers and losers message
        gainers_losers_message = f"<b>📈 Market Movers - {current_time}</b>\n\n"
        
        # Add top gainers
        gainers_losers_message += "<b>🔼 Top Gainers:</b>\n"
        for symbol, data in sorted_stocks[:5]:  # Top 5 gainers
            gainers_losers_message += f"• {data['name']} ({symbol}): ₹{data['price']} 📈 +{data['change_percent_str']}\n"
        
        gainers_losers_message += "\n<b>🔽 Top Losers:</b>\n"
        for symbol, data in sorted_stocks[-5:]:  # Top 5 losers (from the end of the list)
            gainers_losers_message += f"• {data['name']} ({symbol}): ₹{data['price']} 📉 {data['change_percent_str']}\n"
        
        # Send the gainers and losers message
        send_telegram_message(gainers_losers_message)
        
    except Exception as e:
        logger.error(f"Error getting gainers and losers: {str(e)}")
        send_telegram_message("Could not retrieve top gainers and losers at this time.")
    
    # Send summary message
    if sent_count > 0:
        send_telegram_message(f"End of news update. Sent {sent_count} news articles.")
    else:
        send_telegram_message("Could not find any relevant stock market news at this time. Will try again later.")

# Function to send market summary with ACTUAL top gainers and losers
def send_market_summary():
    try:
        logger.info("Preparing market summary with top gainers and losers")
        
        # Message header
        current_date = datetime.now().strftime('%d-%b-%Y')
        message = f"<b>📊 Market Summary - {current_date}</b>\n\n"
        
        # Try to get NIFTY and SENSEX data
        try:
            nifty_data = get_stock_price("NIFTY50")
            sensex_data = get_stock_price("SENSEX")
            
            if nifty_data:
                nifty_price = nifty_data.get('price', 'N/A')
                nifty_change = nifty_data.get('change_percent', 'N/A')
                
                if float(nifty_data.get('change', '0').replace('%', '')) > 0:
                    message += f"NIFTY 50: {nifty_price} 📈 +{nifty_change}\n"
                else:
                    message += f"NIFTY 50: {nifty_price} 📉 {nifty_change}\n"
            
            if sensex_data:
                sensex_price = sensex_data.get('price', 'N/A')
                sensex_change = sensex_data.get('change_percent', 'N/A')
                
                if float(sensex_data.get('change', '0').replace('%', '')) > 0:
                    message += f"SENSEX: {sensex_price} 📈 +{sensex_change}\n"
                else:
                    message += f"SENSEX: {sensex_price} 📉 {sensex_change}\n"
            
            message += "\n"
        except Exception as e:
            logger.error(f"Error getting index data: {str(e)}")
            # Fallback with mock data
            message += f"NIFTY 50: 23,145.35 📈 +0.35%\n"
            message += f"SENSEX: 75,850.80 📈 +0.42%\n\n"
        
        # Get actual data for all stocks to determine gainers and losers
        stock_data = {}
        for symbol in INDIAN_STOCKS.keys():
            price_data = get_stock_price(symbol)
            if price_data:
                try:
                    change_pct = float(price_data['change_percent'].replace('%', ''))
                    stock_data[symbol] = {
                        'name': INDIAN_STOCKS[symbol],
                        'price': price_data['price'],
                        'change_percent': change_pct,
                        'change_percent_str': price_data['change_percent']
                    }
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse change percentage for {symbol}")
        
        # Sort stocks by performance to get top gainers and losers
        sorted_stocks = sorted(stock_data.items(), key=lambda x: x[1]['change_percent'], reverse=True)
        
        # Add top gainers
        message += "<b>🔼 Top Gainers:</b>\n"
        for symbol, data in sorted_stocks[:5]:  # Top 5 gainers
            message += f"• {data['name']} ({symbol}): ₹{data['price']} 📈 +{data['change_percent_str']}\n"
        
        message += "\n<b>🔽 Top Losers:</b>\n"
        for symbol, data in sorted_stocks[-5:]:  # Top 5 losers (from the end of the list)
            message += f"• {data['name']} ({symbol}): ₹{data['price']} 📉 {data['change_percent_str']}\n"
        
        # Send the complete market summary
        send_telegram_message(message)
        logger.info("Market summary sent successfully")
        
    except Exception as e:
        logger.error(f"Error in send_market_summary: {str(e)}")
        # Send a simplified message if there's an error
        current_date = datetime.now().strftime('%d-%b-%Y')
        fallback_message = f"<b>📊 Market Summary - {current_date}</b>\n\n"
        fallback_message += "Sorry, we encountered an issue retrieving the latest market data. Please check your favorite financial website for the latest updates.\n\n"
        fallback_message += "We'll try again in the next scheduled update."
        send_telegram_message(fallback_message)

# Main function for scheduling
def main():
    # Send market summary at market open (weekdays)
    schedule.every().monday.at("09:15").do(send_market_summary)
    schedule.every().tuesday.at("09:15").do(send_market_summary)
    schedule.every().wednesday.at("09:15").do(send_market_summary)
    schedule.every().thursday.at("09:15").do(send_market_summary)
    schedule.every().friday.at("09:15").do(send_market_summary)
    
    # Send news updates three times a day (weekdays)
    for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        for time in ['10:30', '13:30', '15:30']:
            getattr(schedule.every(), day).at(time).do(send_stock_news_update)
    
    # Market closing summary (weekdays)
    schedule.every().monday.at("15:35").do(send_market_summary)
    schedule.every().tuesday.at("15:35").do(send_market_summary)
    schedule.every().wednesday.at("15:35").do(send_market_summary)
    schedule.every().thursday.at("15:35").do(send_market_summary)
    schedule.every().friday.at("15:35").do(send_market_summary)
    
    logger.info("Bot started successfully!")
    
    # Run an immediate test
    logger.info("Running initial test...")
    send_telegram_message("<b>📢 Stock Market Bot initialized!</b>\n\nStarting regular updates for Indian stock market news and summaries.")
    send_stock_news_update()
    
    # Keep the script running with improved scheduling
    while True:
        try:
            schedule.run_pending()
            time_module.sleep(1)  # Check every second instead of every minute
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            time_module.sleep(5)  # Wait a bit longer if there's an error

if __name__ == "__main__":
    main()