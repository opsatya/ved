# stock_chatbot/analysis.py
from .utils import bold, format_table, safe_float, get_prev_year, trend_icon
from .ai_integration import generate_explanation_for_table

def historical_trend_analysis(stock, metric, client, start_year=None, years=5):
    all_years = sorted(stock['years'].keys(), reverse=True)
    filtered_years = [yr for yr in all_years if int(yr.split('-')[0]) >= start_year] if start_year else all_years
    valid_data = [(yr, stock['years'][yr].get(metric)) for yr in filtered_years[:years] if stock['years'][yr].get(metric) is not None]
    if not valid_data:
        return f"{bold('⚠️ No Data')}: {metric} not available for analysis"
    years_list, values = zip(*valid_data)
    max_val, min_val = max(values), min(values)
    response = [
        f"{bold('📈 HISTORICAL TREND ANALYSIS')}",
        f"Company: {stock['Stock']} | Metric: {metric} | Period: {years_list[-1]}–{years_list[0]}",
        ""
    ]
    table_data = []
    for yr, val in valid_data:
        prev_val = next((v for y, v in valid_data if y == get_prev_year(yr)), 0)
        try:
            if metric == 'DebtToEquity' and prev_val != 0:
                change = ((val - prev_val) / prev_val * 100)
            else:
                change = (val - prev_val)
            change_str = f"{trend_icon(change)} {abs(change):.1f}%"
        except (TypeError, ValueError):
            change_str = "N/A"
        
        val_str = f"{val:.2f}" if metric == 'DebtToEquity' else f"{val}%"
        trend_text = "Uptrend" if change > 0 else "Downtrend" if change < 0 else "Stable"
        table_data.append([yr, val_str, trend_text, change_str])
    table_text = format_table(["Year", "Value", "Trend", "YoY Change"], table_data)
    response.append(table_text)
    response.extend([
        "\n" + bold("🔍 KEY INSIGHTS:"),
        f"- Peak Performance: {max_val}% in {years_list[values.index(max_val)]}",
        f"- Lowest Value: {min_val}% in {years_list[values.index(min_val)]}",
        f"- 3Y Avg: {sum(values[:3]) / 3:.1f}% | 5Y Avg: {sum(values) / len(values):.1f}%"
    ])
    overall_change = values[0] - values[-1]
    overall_trend = "uptrend" if overall_change > 0 else "downtrend" if overall_change < 0 else "stable"
    response.append(f"\nOverall, the performance shows an {overall_trend}.")
    explanation = generate_explanation_for_table(client, table_text, "Analyze the historical trend table above...")
    response.append("\n" + explanation)
    return "\n".join(response)

def financial_health_timeline(stock, client, metric_filter=None):
    if metric_filter == 'CashReserve' and not any(stock['years'][y].get('CashReserve') is not None for y in stock['years']):
        return "Cash reserve data not available for this stock"
    metrics = ['CashReserve'] if metric_filter == 'CashReserve' else ['DebtToEquity', 'InterestCoverage', 'PromoterHolding']
    timeline_data = [[year, "\n".join([f"Cash Reserve: ₹{safe_float(value):,.0f} Cr" if metric == 'CashReserve' else f"{metric}: {value}" for metric in metrics if (value := stock['years'][year].get(metric))])] for year in sorted(stock['years'].keys(), reverse=True)[:3] if any(stock['years'][year].get(m) for m in metrics)]
    table_text = f"{bold('🏛️ CASH RESERVE TREND' if metric_filter else '🏛️ FINANCIAL HEALTH TIMELINE')}\n" + format_table(["Year", "Metrics"], timeline_data)
    explanation = generate_explanation_for_table(client, table_text, "Analyze the cash reserve changes" if metric_filter else "Analyze the financial health timeline")
    return table_text + "\n" + explanation

def performance_forecasting(stock, metric, client, years=3):
    sorted_years = sorted(stock['years'].keys(), reverse=True)[:years]
    values = [stock['years'][y].get(metric, 0) for y in sorted_years]
    if len(values) < 2:
        return format_table(["Warning"], [["Insufficient data for forecasting"]])
    growth_rates = [((values[i] - prev_value) / prev_value * 100) if (prev_value := stock['years'].get(get_prev_year(sorted_years[i]), {}).get(metric)) and prev_value != 0 else None for i in range(len(sorted_years))]
    cagr = (values[0] / values[-1]) ** (1 / (len(values) - 1)) - 1
    table_data = [[yr, f"{val}%", f"{gr:.1f}%" if gr is not None else "-"] for yr, val, gr in zip(sorted_years, values, growth_rates)]
    forecast = values[0] * (1 + cagr)
    table_text = "\n".join([f"{bold('📊 PERFORMANCE FORECAST')}", f"Metric: {metric} | Basis: {years}Y CAGR", format_table(["Year", "Growth Rate", "YoY Change"], table_data), f"Projected {metric} for next fiscal year: {forecast:.1f}%", f"CAGR: {cagr * 100:.1f}% | Confidence: {'High' if cagr > 0 else 'Low'}"])
    explanation = generate_explanation_for_table(client, table_text, "Analyze the performance forecast table above...")
    return table_text + "\n" + explanation

def analyze_stock(stock_name, stock_data, client, year=None):
    stock = next((s for s in stock_data if s['Stock'].lower() == stock_name.lower()), None)
    if not stock:
        return {"error": f"Stock '{stock_name}' not found in database"}
    year = year or max(stock['years'].keys(), default=None)
    if not year:
        return {"error": "No annual data available for this stock"}
    current_data = stock['years'].get(year, {})
    return {
        "Stock": stock['Stock'],
        "Year": year,
        "Basic Metrics": {
            k: safe_float(current_data.get(k)) 
            for k in ["RevenueGrowth", "EBITDAGrowth", "NetProfitMargin", "ROCE", "EPSGrowth"]
        },
        "Trend Analysis": {
            "3Y Revenue Trend": historical_trend_analysis(stock, 'RevenueGrowth', client, years=3),
            "5Y Profit Trend": historical_trend_analysis(stock, 'NetProfitMargin', client, years=5)
        },
        "Financial Health": {
            k: safe_float(current_data.get(k)) 
            for k in ["DebtToEquity", "InterestCoverage", "PromoterHolding"]
        },
        "Verdict": stock.get('Verdict', 'No recommendation available')
    }

def format_analysis_response(analysis):
    if 'error' in analysis:
        return f"❌ Error: {analysis['error']}"
    
    response = [
        f"{bold('🚀 COMPREHENSIVE ANALYSIS')}",
        f"Company: {analysis['Stock']} | Fiscal Year: {analysis['Year']}",
        "",
        bold("📊 KEY METRICS"),
        format_table(["Metric", "Value"], [[k, f"{v}%"] for k, v in analysis['Basic Metrics'].items()]),
        "\n" + bold("🏛️ FINANCIAL HEALTH"),
        format_table(["Indicator", "Value"], [
            ["Debt-to-Equity", f"{analysis['Financial Health']['DebtToEquity']}"],
            ["Interest Coverage", f"{analysis['Financial Health']['InterestCoverage']}"],
            ["Promoter Holding", f"{analysis['Financial Health']['PromoterHolding']}%"]
        ]),
        "\n" + bold("📈 TREND ANALYSIS"),
        analysis['Trend Analysis']['3Y Revenue Trend'],
        "\n" + analysis['Trend Analysis']['5Y Profit Trend'],
        "\n" + bold("📌 ANALYST VERDICT"),
        analysis['Verdict']
    ]
    return "\n".join(str(item) for item in response)

def get_stock_analysis(stock_name, stock_data, openai_client, year=None):
    """
    Get analysis for a specific stock
    
    Args:
        stock_name (str): The name of the stock to analyze
        stock_data (list): List of stock data dictionaries
        openai_client: The OpenAI client instance
        year (str, optional): Specific year to analyze. Defaults to most recent.
    
    Returns:
        str: Formatted analysis response
    """
    try:
        # Get the analysis
        result = analyze_stock(
            stock_name=stock_name,
            stock_data=stock_data,
            client=openai_client,
            year=year
        )
        
        # Format and return the response
        return format_analysis_response(result)
    except Exception as e:
        return f"❌ Error analyzing stock: {str(e)}"

# Example usage:
def process_stock_analysis_request(stock_name, stock_data, openai_client):
    """Process a stock analysis request"""
    # You can specify a year if needed
    # analysis = get_stock_analysis(stock_name, stock_data, openai_client, year="2023")
    
    # Or let it use the most recent year
    analysis = get_stock_analysis(stock_name, stock_data, openai_client)
    return analysis