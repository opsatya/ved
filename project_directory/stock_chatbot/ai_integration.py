# stock_chatbot/ai_integration.py
import json
from .utils import cached_openai_request, clean_ai_response, safe_float, bold

def generate_explanation_for_table(client, table_text, context):
    prompt = context + "\nHere is the table:\n" + table_text + "\nPlease provide a detailed explanation in at least 5 lines..."
    return cached_openai_request(client, "gpt-4o-mini", "You are a senior financial analyst providing detailed insights.", prompt)

def annual_report_summarizer(stock, client, year=None):
    year = year or max(stock['years'].keys())
    if year not in stock['years']:
        return f"No data available for {year}"
    data = stock['years'][year]
    prompt = f"Create a concise 5-point summary for {stock['Stock']}'s {year} annual report with these metrics: " + ", ".join([f"{k}: {v}" for k, v in data.items()])
    return cached_openai_request(client, "gpt-4o-mini", "You are a financial analyst creating concise report summaries.", prompt)

def generate_ai_summary(client, prompt):
    return cached_openai_request(client, "gpt-4o-mini", "You are a financial analyst creating concise report summaries.", prompt)

def generate_scoring_verdict(stock, client, year=None):
    if not year:
        year = max(stock['years'].keys(), default=None)
        if not year:
            return f"{bold('❌ Error')}: No annual data available for {stock['Stock']}"
    current_data = stock['years'][year]
    prompt = f"""
You are a senior financial analyst. Evaluate the following financial metrics for {stock['Stock']} for the fiscal year {year}...
### **Metrics**:
- Revenue Growth: {current_data.get('RevenueGrowth', 'Data not available')}%
- EBITDA Growth: {current_data.get('EBITDAGrowth', 'Data not available')}%
- Net Profit Margin: {current_data.get('NetProfitMargin', 'Data not available')}%
- Debt-to-Equity: {current_data.get('DebtToEquity', 'Data not available')}
- Interest Coverage: {current_data.get('InterestCoverage', 'Data not available')}
- Promoter Holding: {current_data.get('PromoterHolding', 'Data not available')}%
..."""
    return cached_openai_request(client, "gpt-4o-mini", "You are a senior financial analyst evaluating stock performance...", prompt)

def openrouter_chat(client, query, stock_data, general_chat=False):
    system_message = f"""You are a financial data parser that ONLY uses provided JSON data...
Available Stock Data:
{json.dumps(stock_data, indent=2)}
..."""
    return cached_openai_request(client, "gpt-4o-mini", system_message, f"Query: {query}\n\nAnswer using ONLY the provided JSON:")

def score_revenue_growth(value):
    if value > 15: return {'points': 10, 'display': '++10 (＞15%)'}
    if value > 10: return {'points': 8, 'display': '+8 (10-15%)'}
    if value > 5: return {'points': 5, 'display': '+5 (5-10%)'}
    return {'points': 2, 'display': '+2 (＜5%)'}

def score_ebitda(value):
    if value > 20: return {'points': 15, 'display': '++15 (＞20%)'}
    if value > 15: return {'points': 12, 'display': '+12 (15-20%)'}
    if value > 10: return {'points': 5, 'display': '+5 (10-15%)'}
    return {'points': 2, 'display': '+2 (＜10%)'}

def score_profit(value):
    if value > 20: return {'points': 10, 'display': '++10 (＞20%)'}
    if value > 15: return {'points': 7, 'display': '+7 (15-20%)'}
    if value > 10: return {'points': 5, 'display': '+5 (10-15%)'}
    return {'points': 3, 'display': '+3 (＜10%)'}

def score_debt(value):
    if 1.5 <= value <= 3: return {'points': 5, 'display': '+5 (Optimal 1.5-3)'}
    if value < 1.5: return {'points': 3, 'display': '+3 (Low <1.5)'}
    return {'points': -2, 'display': '-2 (High >3)'}

def score_holding(value):
    if 40 <= value <= 60: return {'points': 5, 'display': '+5 (40-60%)'}
    if value > 60: return {'points': 3, 'display': '+3 (>60%)'}
    return {'points': -1, 'display': '-1 (<40%)'}

def calculate_risks(stock, year):
    risks = {
        'geo_political': -5 if 'paints' in stock['Stock'].lower() else 0,
        'debt_risk': -3 if safe_float(stock['years'][year].get('DebtToEquity', 0)) > 4 else 0,
        'growth_risk': -2 if safe_float(stock['years'][year].get('RevenueGrowth', 0)) < 5 else 0
    }
    return {'total': sum(risks.values()), 'details': "\n".join([f"• {k.replace('_', ' ').title()}: {v} pts" for k, v in risks.items() if v < 0])}

def get_recommendation(score):
    recommendations = {
        range(80, 101): {'text': '✅ Strong Buy', 'reasons': ['Excellent fundamentals', 'Strong growth trajectory'], 'outlook': 'High growth potential with strong fundamentals'},
        range(60, 80): {'text': '🟢 Buy', 'reasons': ['Good financial metrics', 'Stable growth'], 'outlook': 'Positive outlook with moderate growth'},
        range(40, 60): {'text': '🟡 Hold', 'reasons': ['Mixed performance', 'Moderate risks'], 'outlook': 'Wait for improved fundamentals'},
        range(0, 40): {'text': '🔴 Risky - Consider Exit', 'reasons': ['Weak metrics', 'High risk profile'], 'outlook': 'Caution advised - monitor closely'}
    }
    return next((details for r, details in recommendations.items() if score in r), {'text': '⚠️ No Recommendation', 'reasons': ['Insufficient data'], 'outlook': 'Cannot determine'})