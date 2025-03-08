# stock_chatbot/utils.py
import re
import time
import sys
import os
from functools import lru_cache

def safe_float(value, default=0.0):
    if isinstance(value, (int, float)):
        return float(value)
    try:
        cleaned = str(value).replace('%', '').replace(',', '').strip()
        return float(cleaned) if cleaned else default
    except (TypeError, ValueError):
        return default

def clean_ai_response(text):
    return re.sub(r'[\{\}\"]', '', text).replace("\\n", "\n")

def bold(text):
    return f"\033[1;36m{text}\033[0m"

def text_chart(value, max_value=None, width=20):
    if not max_value:
        max_value = max(value)
    return '▇' * max(1, int((value / max_value) * width))

def trend_icon(value):
    if value > 0:
        return "↑"
    if value < 0:
        return "↓"
    return "→"

def get_prev_year(fy):
    try:
        start = int(fy.split('-')[0])
        return f"{start-1}-{start%1000}"
    except:
        return str(int(fy) - 1)

def format_table(headers, rows):
    col_widths = [max(len(str(row[i])) for row in rows + [headers]) for i in range(len(headers))]
    top_border = "╔" + "╦".join("═" * (w + 2) for w in col_widths) + "╗"
    header_row = "║" + "║".join(f" {header.center(col_widths[i])} " for i, header in enumerate(headers)) + "║"
    separator = "╠" + "╬".join("═" * (w + 2) for w in col_widths) + "╣"
    bottom_border = "╚" + "╩".join("═" * (w + 2) for w in col_widths) + "╝"
    data_rows = ["║" + "║".join(f" {str(cell).ljust(col_widths[i])} " for i, cell in enumerate(row)) + "║" for row in rows]
    return "\n".join([top_border, header_row, separator] + data_rows + [bottom_border])

@lru_cache(maxsize=100)
def cached_openai_request(client, model, system_content, user_content, max_retries=3, retry_delay=5):
    if os.getenv('CLEAR_CACHE', '').lower() == 'true':
        cached_openai_request.cache_clear()
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content}
    ]
    for attempt in range(max_retries):
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )
            content = completion.choices[0].message.content
            if not content.endswith(('.', '!', '?')):
                content += " [Analysis truncated due to length constraints]"
            return content
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"API error: {str(e)}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                return f"Error: Unable to complete analysis after {max_retries} attempts: {str(e)}"

def stream_response(text):
    lines = text.split('\n')
    for line in lines:
        if any(c in line for c in ('╔', '║', '╚', '═', '╬')):
            sys.stdout.write(line + '\n')
            sys.stdout.flush()
            time.sleep(0.05)
        else:
            words = re.findall(r'\S+|\n', line)
            for i, word in enumerate(words):
                prefix = ' ' if i > 0 and not word.startswith(('\n', '▇')) else ''
                sys.stdout.write(prefix + word)
                sys.stdout.flush()
                delay = 0.02 if any(c in word for c in ('▇', '→', '↑', '↓')) else 0.03
                time.sleep(delay)
            sys.stdout.write('\n')
            sys.stdout.flush()
        time.sleep(0.01)