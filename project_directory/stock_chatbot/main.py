# stock_chatbot/main.py
import os
import sys
import traceback
from flask import Flask, request, jsonify, render_template
from .api_clients import FivePaisaClient, NeoAPI
from .data_loader import load_stock_data
from .query_processor import process_query
from .utils import stream_response
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)

# Load stock data and initialize API clients (done once when the app starts)
STOCK_DATA_DIRECTORY = 'stock_data'
stock_data = load_stock_data(STOCK_DATA_DIRECTORY)

five_paisa_cred = {
    "APP_NAME": "5P50289032", "APP_SOURCE": "22145", "USER_ID": "jv0zaXaW7lD",
    "PASSWORD": "ZusnUUqsJoh", "USER_KEY": "24BLhwIxzMHo31rotJYypWuvYUU4mCHZ",
    "ENCRYPTION_KEY": "FanCs8NKjzunmTmGXgxkOPYS5QUwsXvU"
}
five_paisa_client = FivePaisaClient(cred=five_paisa_cred)

neo_client = NeoAPI(
    consumer_key="fmHOCOoINQuyTfdB8S_aiiWMdlQa",
    consumer_secret="xjI_osC4q4r4zkWbFpq_Vgw4LTga",
    environment='prod', access_token=None, neo_fin_key=None
)
try:
    neo_client.login(mobilenumber="+916303008951", password="Avks@1234")
    neo_client.session_2fa(OTP="271707")
except Exception as e:
    print(f"NeoAPI login failed: {str(e)}")

api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("Error: OPENAI_API_KEY environment variable not set.")
    sys.exit(1)
openai_client = OpenAI(api_key=api_key)

# Serve the frontend at root URL
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Define the Flask route to handle chatbot queries
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({"error": "No query provided"}), 400
        
        user_input = data['query']
        
        if user_input.lower() in ["quit", "exit", "bye"]:
            return jsonify({"response": "Goodbye! 👋"}), 200
        
        response = process_query(user_input, stock_data, five_paisa_client, neo_client, openai_client)
        
        return jsonify({"response": response}), 200
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"⚠️ Error: {str(e)}. Please try again."}), 500

if __name__ == "__main__":
    print("Starting the Stock Analysis Chatbot Flask App...")
    app.run(debug=True, host='0.0.0.0', port=5000)