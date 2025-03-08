# stock_chatbot/query_processor.py
import re
from datetime import datetime
import pytz
from .utils import bold, safe_float
from .analysis import historical_trend_analysis, financial_health_timeline, performance_forecasting, get_stock_analysis
from .forensic import forensic_analysis
from .order_placement import get_current_price, place_buy_order, place_sell_order
from .ai_integration import annual_report_summarizer, generate_scoring_verdict
from difflib import SequenceMatcher

STOCK_ALIASES = {
    'hdfcbank': 'HDFC Bank',
    'sbi': 'State Bank of India',
    'tcs': 'Tata Consultancy Services',
    # Add more aliases as needed
}

def extract_metric(query):
    metrics = {'revenue': 'RevenueGrowth', 'ebitda': 'EBITDAGrowth', 'debt': 'DebtToEquity', 'debt ratio': 'DebtToEquity', 'profit': 'NetProfitMargin', 'recommendation': 'Verdict', 'advice': 'Verdict', 'cash reserve': 'CashReserve', 'cash': 'CashReserve'}
    return next((metric for key, metric in metrics.items() if key in query.lower()), None)

def find_stock_from_query(query, stock_data):
    query_lower = query.lower()
    for stock in stock_data:
        if query_lower == stock.get('Stock', '').lower():
            return stock['Stock']
    for stock in stock_data:
        name = stock.get('Stock', '').lower()
        if set(query_lower.split()) & set(name.split()):
            return stock['Stock']
    abbrev_mapping = {'asian': 'Asian Paints Limited', 'itc': 'ITC Limited', 'coal': 'Coal India Limited', 'bharti': 'Bharti Airtel Limited', 'bajaj': 'Bajaj Auto Limited', 'axis': 'Axis Bank Limited'}
    return next((full_name for abbrev, full_name in abbrev_mapping.items() if abbrev in query_lower and any(s.get('Stock', '').lower() == full_name.lower() for s in stock_data)), None)

def clean_numerical_fields(stock_item):
    if 'years' not in stock_item:
        return
    numerical_fields = ['RevenueGrowth', 'EBITDAGrowth', 'NetProfitMargin', 'DebtToEquity', 'InterestCoverage', 'PromoterHolding', 'IndustryRanking', 'EPSGrowth']
    for year, data in stock_item['years'].items():
        for field in numerical_fields:
            if field in data:
                data[field] = safe_float(data[field])

def extract_year(query):
    year_match = re.search(r'(20\d{2}-\d{2})|(FY\s?\d{4})|(20\d{2})', query, re.IGNORECASE)
    if not year_match:
        return None
    year = year_match.group()
    if '-' in year and len(year) == 7:
        return year
    elif year.lower().startswith('fy'):
        return f"20{year[-2:]}-{str(int(year[-2:]) + 1)}"
    return f"{year}-{str(int(year) + 1)[-2:]}"

def validate_data_presence(stock, metric):
    required_fields = {'revenue': ['RevenueGrowth', 'AnnualReports'], 'profit': ['NetProfitMargin', 'EBITDA'], 'debt': ['DebtToEquity'], 'cash': ['CashReserve']}
    latest_year = max(stock['years'])
    return [f for f in required_fields.get(metric, []) if f not in stock['years'][latest_year]]

def similarity_ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()

def extract_stock_name(user_input, stock_data):
    """
    Extract stock name from user input.
    
    Args:
        user_input (str): The user's input text
        stock_data (list): List of stock dictionaries containing stock information
        
    Returns:
        str: Extracted stock name or None if not found
    """
    # Convert input to lowercase for case-insensitive matching
    user_input = user_input.lower()
    
    # Get all available stock names
    available_stocks = {stock['Stock'].lower(): stock['Stock'] for stock in stock_data}
    
    # First try direct matching
    for stock_name in available_stocks.keys():
        if stock_name in user_input:
            return available_stocks[stock_name]
    
    # If no direct match, try fuzzy matching
    words = user_input.split()
    for word in words:
        # Skip common words that might appear in queries
        if word in {'analyze', 'check', 'stock', 'price', 'data', 'info', 'about', 'tell', 'me', 'show', 'get'}:
            continue
        
        # Try to match with available stocks
        for stock_name in available_stocks.keys():
            if (word in stock_name) or (stock_name in word):
                return available_stocks[stock_name]
    
    if user_input in STOCK_ALIASES:
        return STOCK_ALIASES[user_input]
    
    return None

def suggest_similar_stocks(query, stock_data, max_suggestions=3):
    query = query.lower()
    suggestions = []
    
    for stock in stock_data:
        stock_name = stock['Stock'].lower()
        similarity = similarity_ratio(query, stock_name)
        if similarity > 0.5:  # Adjust threshold as needed
            suggestions.append((stock['Stock'], similarity))
    
    # Sort by similarity and return top suggestions
    suggestions.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in suggestions[:max_suggestions]]

def process_query(user_input, stock_data, five_paisa_client, neo_client, openai_client):
    # If the query is about analyzing a specific stock
    if "analyze" in user_input.lower():
        # Extract stock name from user input (you'll need to implement this logic)
        stock_name = extract_stock_name(user_input, stock_data)
        if stock_name:
            return get_stock_analysis(stock_name, stock_data, openai_client)
    
    # Handle other types of queries...

    lower_query = user_input.lower()
    greeting_pattern = r'\b(hi|hello|hey|howdy|hola)\b'
    if re.search(greeting_pattern, lower_query) and len(user_input.split()) <= 3:
        return "Hello! I'm your Stock Analysis Chatbot. I can help you analyze financial data or place buy/sell orders..."

    if lower_query.startswith("deploy"):
        from .deployment import deploy_remote_script
        return deploy_remote_script()

    forensic_triggers = ['forensic', 'fraud check', 'accounting anomaly', 'auditor remark', 'insider trading', 'benford', 'revenue quality', 'cash flow', 'related party', 'expense anomaly']
    if any(trigger in lower_query for trigger in forensic_triggers):
        matched_stock = find_stock_from_query(user_input, stock_data)
        if matched_stock:
            stock = next((s for s in stock_data if s['Stock'].lower() == matched_stock.lower()), None)
            return forensic_analysis(stock, openai_client)
        return "Please specify a valid stock for forensic analysis"

    buy_match = re.search(r'place buy order for (\d+) shares of (.+)', lower_query)
    if buy_match:
        quantity, stock_name = int(buy_match.group(1)), buy_match.group(2).strip()
        matched_stock = find_stock_from_query(stock_name, stock_data)
        if matched_stock and (stock := next((s for s in stock_data if s['Stock'] == matched_stock), None)):
            return place_buy_order(neo_client, stock, quantity)
        return f"Stock '{stock_name}' not found in database..."

    sell_match = re.search(r'place sell order for (\d+) shares of (.+)', lower_query)
    if sell_match:
        quantity, stock_name = int(sell_match.group(1)), sell_match.group(2).strip()
        matched_stock = find_stock_from_query(stock_name, stock_data)
        if matched_stock and (stock := next((s for s in stock_data if s['Stock'] == matched_stock), None)):
            return place_sell_order(neo_client, stock, quantity)
        return f"Stock '{stock_name}' not found in database..."

    start_year = int(m.group(1)) if (m := re.search(r'since\s*(\d{4})', user_input, re.IGNORECASE)) else None
    extracted_year = extract_year(user_input)
    clean_query = re.sub(r'(20\d{2}-\d{2})|(FY\s?\d{4})|(20\d{2})', '', user_input, flags=re.IGNORECASE).strip()

    matched_stock = find_stock_from_query(clean_query, stock_data)
    if not matched_stock:
        if any(term in lower_query for term in ['stock', 'share', 'market', 'invest', 'finance', 'analysis']):
            return "I don't have information about this specific stock or query in my database..."
        return "I'm specialized in stock analysis based on my financial database..."

    stock = next((s for s in stock_data if s['Stock'].lower() == matched_stock.lower()), None)
    metric = extract_metric(clean_query)

    if "predict" in lower_query and metric:
        return performance_forecasting(stock, metric, openai_client, years=3)
    if "summarize" in lower_query or "annual report" in lower_query:
        return annual_report_summarizer(stock, openai_client, extracted_year)
    if ("display" in lower_query or "show" in lower_query) and "cash reserve" in lower_query:
        return financial_health_timeline(stock, openai_client, metric_filter='CashReserve')
    if "trend" in lower_query and metric:
        return historical_trend_analysis(stock, metric, openai_client, start_year=start_year)

    price_keywords = ["current price", "live price", "stock price", "market price", "share price"]
    if any(keyword in lower_query for keyword in price_keywords):
        ticker = stock.get('Ticker', '')
        if not ticker:
            return f"No ticker available for {stock['Stock']} in the database."
        scrip_data = f"{ticker}_EQ"
        if (current_price := get_current_price(five_paisa_client, scrip_data)) is not None:
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S %Z")
            return f"The current price of {stock['Stock']} ({ticker}) is ₹{current_price} as of {current_time}."
        return f"Unable to fetch the current price for {stock['Stock']} at this time."

    return generate_scoring_verdict(stock, openai_client, extracted_year)

def process_financial_data(data):
    """Process financial data with proper error handling"""
    try:
        # Convert basic metrics
        basic_metrics = ['RevenueGrowth', 'EBITDAGrowth', 'NetProfitMargin']
        for metric in basic_metrics:
            if metric in data:
                data[metric] = safe_float(data[metric])
                
        # Convert ratios (might want a different default)
        ratio_metrics = ['DebtToEquity', 'InterestCoverage']
        for metric in ratio_metrics:
            if metric in data:
                data[metric] = safe_float(data[metric], default=None)  # Use None for missing ratios
                
        # Convert percentages
        percentage_metrics = ['PromoterHolding']
        for metric in percentage_metrics:
            if metric in data:
                data[metric] = safe_float(data[metric])
                # Ensure percentage is in valid range
                if data[metric] is not None:
                    data[metric] = max(0.0, min(100.0, data[metric]))
                    
    except Exception as e:
        print(f"Error processing financial data: {str(e)}")
        return None
        
    return data