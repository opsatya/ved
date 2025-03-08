# stock_chatbot/forensic.py
from collections import defaultdict
from .utils import safe_float, bold, format_table, cached_openai_request, clean_ai_response

def check_benfords_law(stock):
    amounts = [str(int(safe_float(data.get('Revenue', 0))))[0] for _, data in stock['years'].items() if data.get('Revenue') and str(int(safe_float(data['Revenue'])))]
    if not amounts:
        return ["Insufficient data for Benford's Law analysis"]
    distribution = defaultdict(int)
    for d in amounts:
        distribution[d] += 1
    total = len(amounts)
    expected = {'1': 30.1, '2': 17.6, '3': 12.5, '4': 9.7, '5': 7.9, '6': 6.7, '7': 5.8, '8': 5.1, '9': 4.6}
    return [f"Digit {digit}: {observed/total*100:.1f}% vs expected {expected[digit]}%" for digit in '123456789' if abs((observed := distribution[digit]) / total * 100 - expected[digit]) > 5] or ["No significant deviations from Benford's Law"]

def detect_insider_trading(stock):
    trading_data = stock.get('InsiderTrades', [])
    if not trading_data:
        return ["No insider trading data available"]
    last_year = max(stock['years'].keys(), default="").split('-')[0]
    recent_trades = [t for t in trading_data if t.get('date', '').startswith(last_year)]
    if not recent_trades:
        return ["No recent insider trades"]
    sell_ratio = sum(1 for t in recent_trades if t.get('type', '').lower() == 'sell') / len(recent_trades)
    anomalies = [f"High sell ratio ({sell_ratio:.0%}) in current year"] if sell_ratio > 0.7 else []
    if any(int(t.get('shares', 0)) > 10000 for t in recent_trades):
        anomalies.append("Large block trades detected")
    return anomalies or ["No suspicious insider trading patterns"]

def analyze_revenue_quality(stock):
    anomalies = [f"{year}: High revenue growth ({rev_growth}%) with long AR days ({ar_days})" if rev_growth > 20 and ar_days > 90 else f"{year}: Declining revenue ({rev_growth}%) with short AR days ({ar_days})" if rev_growth < -10 and ar_days < 30 else None for year, data in stock['years'].items() if (rev_growth := safe_float(data.get('RevenueGrowth', 0))) and (ar_days := safe_float(data.get('AccountsReceivableDays', 0)))]
    return [a for a in anomalies if a] or ["Consistent revenue quality metrics"]

def check_auditor_remarks(stock):
    anomalies = [f"{year}: {remarks[:100]}..." for year, data in stock['years'].items() if (remarks := data.get('AuditorRemarks', '')) and any(kw in remarks.lower() for kw in ['disclaimer', 'qualified', 'uncertainty', 'material misstatement'])]
    return anomalies or ["No critical auditor remarks found"]

def check_cash_flow_anomalies(stock):
    anomalies = [f"{year}: {note[:100]}..." for year, data in stock['years'].items() if (note := data.get('CashFlowAnomalies', '')) and any(kw in note.lower() for kw in ['irregular', 'dispute', 'non-recurring', 'unexplained'])]
    return anomalies or ["No significant cash flow anomalies"]

def check_related_parties(stock):
    anomalies = [f"{year}: Suspicious transactions reported" for year, data in stock['years'].items() if (trans := data.get('RelatedPartyTransactions', '')) and any(kw in trans.lower() for kw in ['material', 'significant', 'unapproved', 'non-arm'])]
    return anomalies or ["No problematic related party transactions"]

def check_expense_anomalies(stock):
    anomalies = [f"{year}: Severe EBITDA decline ({data['EBITDAGrowth']}%) despite revenue growth" for year, data in stock['years'].items() if safe_float(data.get('EBITDAGrowth', 0)) < -50 and safe_float(data.get('RevenueGrowth', 0)) > 5]
    return anomalies or ["No significant expense anomalies"]

def forensic_analysis(stock, client, year=None):
    year = year or max(stock['years'].keys(), default=None)
    current_data = stock['years'].get(year, {})
    analysis = {
        'benfords_law': check_benfords_law(stock),
        'insider_trading': detect_insider_trading(stock),
        'revenue_quality': analyze_revenue_quality(stock),
        'expense_anomalies': check_expense_anomalies(stock),
        'auditor_issues': check_auditor_remarks(stock),
        'cash_flow': check_cash_flow_anomalies(stock),
        'related_parties': check_related_parties(stock)
    }
    return format_forensic_report(stock, analysis, year, client)

def format_forensic_report(stock, analysis, year, client):
    report = [
        f"{bold('🔍 FORENSIC ANALYSIS')}",
        f"Company: {stock['Stock']} | FY: {year}",
        "\n" + bold("🚩 Benford's Law Analysis:"), *[f"• {item}" for item in analysis['benfords_law']],
        "\n" + bold("🚩 Insider Trading Patterns:"), *[f"• {item}" for item in analysis['insider_trading']],
        "\n" + bold("🚩 Revenue Quality Check:"), *[f"• {item}" for item in analysis['revenue_quality']],
        "\n" + bold("🚩 Expense Anomalies:"), *[f"• {item}" for item in analysis['expense_anomalies']],
        "\n" + bold("🚩 Auditor Remarks Analysis:"), *[f"• {item}" for item in analysis['auditor_issues']],
        "\n" + bold("🚩 Cash Flow Irregularities:"), *[f"• {item}" for item in analysis['cash_flow']],
        "\n" + bold("🚩 Related Party Transactions:"), *[f"• {item}" for item in analysis['related_parties']]
    ]
    prompt = f"Explain these forensic findings for {stock['Stock']} in under 300 words: {analysis}\nFocus on:\n1. Most critical red flags\n2. Investor implications\n3. Recommended next steps"
    explanation = cached_openai_request(client, "gpt-4o-mini", "You're a forensic accountant explaining findings", prompt)
    report.extend(["\n" + bold("📝 Expert Interpretation:"), clean_ai_response(explanation)])
    return "\n".join(report)