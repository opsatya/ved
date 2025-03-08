# stock_chatbot/data_loader.py
import os
import glob
import json

def load_stock_data(directory='stock_data'):
    data = []
    json_files = glob.glob(os.path.join(directory, "*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in directory: {directory}")
    for file_path in json_files:
        try:
            with open(file_path, "r") as file:
                file_data = json.load(file)
                if isinstance(file_data, list):
                    data.extend(file_data)
                elif isinstance(file_data, dict):
                    data.append(file_data)
                else:
                    print(f"Warning: {file_path} contains unexpected data format.")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    return data