# stock_chatbot/order_placement.py
from datetime import datetime
import pytz

def get_current_price(five_paisa_client, scrip_data):
    req_data = [{"Exch": "N", "ExchType": "C", "ScripData": scrip_data}]
    try:
        response = five_paisa_client.fetch_market_feed_scrip(req_data)
        return response['Data'][0]['LastRate']
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def place_buy_order(neo_client, stock, quantity):
    ticker = stock.get('Ticker', '')
    if not ticker:
        return f"No ticker available for {stock['Stock']}."
    trading_symbol = f"{ticker}-EQ"
    try:
        response = neo_client.place_order(
            exchange_segment='nse_cm', product='CNC', price='0', order_type='MKT',
            quantity=str(quantity), validity='DAY', trading_symbol=trading_symbol,
            transaction_type='B', amo="NO", disclosed_quantity="0", market_protection="0",
            pf="N", trigger_price="0", tag=None
        )
        if response and response.get('stat') == 'Ok':
            return f"Buy order placed successfully for {quantity} shares of {stock['Stock']}. Order ID: {response.get('nOrdNo', 'Not provided')}"
        elif response and response.get('code') == '900901':
            return "Authentication failed: Invalid JWT token. Please restart the chatbot and provide a valid OTP."
        return f"Failed to place buy order. Response: {response}"
    except Exception as e:
        return f"Failed to place buy order with Neo API: {str(e)}"

def place_sell_order(neo_client, stock, quantity):
    ticker = stock.get('Ticker', '')
    if not ticker:
        return f"No ticker available for {stock['Stock']}."
    trading_symbol = f"{ticker}-EQ"
    try:
        response = neo_client.place_order(
            exchange_segment='nse_cm', product='CNC', price='0', order_type='MKT',
            quantity=str(quantity), validity='DAY', trading_symbol=trading_symbol,
            transaction_type='S', amo="NO", disclosed_quantity="0", market_protection="0",
            pf="N", trigger_price="0", tag=None
        )
        if response and response.get('stat') == 'Ok':
            return f"Sell order placed successfully for {quantity} shares of {stock['Stock']}. Order ID: {response.get('nOrdNo', 'Not provided')}"
        elif response and response.get('code') == '900901':
            return "Authentication failed: Invalid JWT token. Please restart the chatbot and provide a valid OTP."
        return f"Failed to place sell order. Response: {response}"
    except Exception as e:
        return f"Failed to place sell order with Neo API: {str(e)}"