import requests
import json
import time
import re
import os
from dotenv import load_dotenv
from stocks import sp500_by_category

# Load environment variables from .env file
load_dotenv()

def generate_text(prompt, model="gemini-2.0-flash-lite", api_url="https://generativelanguage.googleapis.com/v1beta/models"):
    # Get API key from environment variable loaded via dotenv
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file")
    
    # Construct the full API URL with the model and API key
    full_api_url = f"{api_url}/{model}:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": "You are a financial advisor at the biggest investment firm in the world. You are very good at creating portfolios. You should only output JSON. Do not add any other text."
                    }
                ]
            },
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.6,
            "maxOutputTokens": 2048,
        }
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(full_api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        result = response.json()
        
        return {
            "response": result,
            "generation_time": generation_time
        }
    except requests.exceptions.RequestException as e:
        print(f"Error making request to Gemini API: {e}")
        return None

def extract_content(response):
    if response and "response" in response:
        try:
            # Gemini API response structure is different from the previous API
            return response["response"]["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            print(f"Error extracting content: {e}")
            return "Error: Could not extract content from response"
    return "Error: No valid response received"

def create_payload(input):
    prompt = f"""{input}

The information above is an investment profile from a potential client. What you have to do is understand the client's risk profile.
Based on this, you will determine the client's investment portfolio. Here are some guidelines:
1. Only S&P500 stocks are allowed.
2. Take into account the client's age, budget, salary and other information.
3. Create a list of tickers that are appropriate for the client.
4. The more risk averse the client is, the more diversified the portfolio should be in terms of quantity and sector exposure.
5. The more risk averse the client is, the less volatile the stocks should be.
6. The more risk averse the client is, the more they should avoid volatile sectors.
7. DO NOT LIST TICKERS IN SECTORS THAT THE CLIENT EXPLICITLY MENTIONED TO AVOID.
8. The risk index is a number from 0-1 with 1 being very very volatile. Choose an appropriate index for the client.
9. Don't be afraid to suggest a lot of tickers (10+) if the risk index is low and budget is large enough.
10. Take into account the stock behavior within the client's investment timeframe.
11. Only give tickers that are traded during the investment timeframe.

Based on this, create a JSON schema with the following fields. DO NOT FORGET ANY FIELDS. MAKE SURE YOU PARSE THE DATES CORRECTLY.:

{{
    "tickers": list of tickers that the client should invest in based on the guidelines above,
    "budget": integer or None if unspecified,
    "investment_start": string (yyyy-mm-dd),
    "investment_end": string (yyyy-mm-dd),
    "risk": number from 0-1 which is the risk index of the client
}}
"""

    print(f"Prompt: {prompt}\n")
    
    result = generate_text(prompt)
    
    if result:
        content = extract_content(result)

        model_output = content

        # Remove optional triple quotes or markdown-style code fences
        # This regex removes leading/trailing ⁠ json,  ⁠ or '''json
        match = re.search(r"\{.*\}", model_output, flags=re.DOTALL)
        try:
            content_dict = eval(match.group(0))
            return content_dict
        except (AttributeError, SyntaxError) as e:
            print("Failed to parse JSON:", e)
            return None
            # Add logic to just move onto the next loop
    else:
        print("Failed to get a response from the server.")

def create_payload_fast(input_data):
    # Parse the input JSON
    try:
        if isinstance(input_data, str):
            # Sometimes input comes as a string containing JSON
            if input_data.startswith('{"message":'):
                data = json.loads(input_data)
                client_data = json.loads(data.get("message", "{}"))
            else:
                client_data = json.loads(input_data)
        else:
            client_data = input_data
    except json.JSONDecodeError:
        # If not JSON, try to parse as a plain text description
        client_data = {"text_description": input_data}
    
    # Extract relevant info
    budget = client_data.get("budget")
    start_date = client_data.get("start", client_data.get("start_date"))
    end_date = client_data.get("end", client_data.get("end_date"))
    age = client_data.get("age", 35)  # Default to 35 if not specified
    salary = client_data.get("salary", 50000)  # Default salary
    dislikes = client_data.get("dislikes", [])
    
    # Calculate risk profile (0-1)
    # Lower age = higher risk tolerance
    age_factor = max(0, min(1, (age - 20) / 60))  # Age 20 → 0, Age 80 → 1
    
    # Higher salary = higher risk tolerance
    salary_factor = max(0, min(1, 1 - (salary / 200000)))  # $0 → 1, $200k+ → 0
    
    # Combine factors (age is more important)
    risk_score = 1 - (0.7 * age_factor + 0.3 * salary_factor)
    
    # Select tickers based on risk profile and sectors to avoid
    tickers = select_tickers(risk_score, dislikes, budget)
    
    # Create the payload
    payload = {
        "tickers": tickers,
        "budget": budget,
        "investment_start": start_date,
        "investment_end": end_date,
        "risk": risk_score
    }
    
    return payload

def select_tickers(risk_score, dislikes, budget):
    """Select appropriate tickers based on risk profile and dislikes"""
    # Define sector volatility (higher = more volatile)
    sector_volatility = {
        "Technology": 0.8,
        "Finance or Crypto Assets": 0.7,
        "Crypto Assets": 0.9,
        "Life Sciences": 0.6,
        "Energy and Transportation": 0.7,
        "Trade and Services": 0.5,
        "Structured Finance": 0.6,
        "Industrial Applications and Services": 0.6,
        "Manufacturing": 0.5,
        "International Corp Fin": 0.7
    }
    
    # Filter out disliked sectors
    available_sectors = {k: v for k, v in sector_volatility.items() if k not in dislikes}
    
    # Sort sectors by volatility
    sorted_sectors = sorted(available_sectors.items(), key=lambda x: x[1])
    
    # Determine how many sectors and stocks based on risk profile
    if risk_score < 0.3:  # Conservative
        num_sectors = 4
        stocks_per_sector = 2
        # Prefer less volatile sectors
        preferred_sectors = [s[0] for s in sorted_sectors[:num_sectors]]
    elif risk_score < 0.7:  # Moderate
        num_sectors = 3
        stocks_per_sector = 2
        # Mix of sectors
        preferred_sectors = [s[0] for s in sorted_sectors[::2][:num_sectors]]
    else:  # Aggressive
        num_sectors = 2
        stocks_per_sector = 3
        # Prefer more volatile sectors
        preferred_sectors = [s[0] for s in sorted_sectors[-num_sectors:]]
    
    # Adjust stocks per sector based on budget
    if budget:
        min_per_stock = 500  # Minimum investment per stock
        max_stocks = budget // min_per_stock
        if max_stocks < num_sectors * stocks_per_sector:
            # Reduce number of stocks if budget is too small
            stocks_per_sector = max(1, max_stocks // num_sectors)
            num_sectors = min(num_sectors, max_stocks)
    
    selected_tickers = []
    import random
    
    # Use our predefined sector dictionary
    for sector in preferred_sectors[:num_sectors]:
        if sector in sp500_by_category and len(sp500_by_category[sector]) > 0:
            sector_tickers = random.sample(
                sp500_by_category[sector], 
                min(stocks_per_sector, len(sp500_by_category[sector]))
            )
            selected_tickers.extend(sector_tickers)
    
    # Ensure we have at least some stocks
    if not selected_tickers:
        # Fallback to some stable stocks
        selected_tickers = ["AAPL", "JNJ", "PG", "KO", "WMT"]
    
    return selected_tickers

# def create_payload(input):
#     prompt = f"""{input}

# Suggest appropriate number of tickers based on the risk number. It is a number from 0-1 with 1 being very very volatile. Try to diversify more if the risk index is low. Condense into the JSON schema below. JSON output only.
# {{
#     "tickers": [string],
#     "budget": integer,
#     "investment_start": string (yyyy-mm-dd),
#     "investment_end": string (yyyy-mm-dd),
#     "risk": number (use risk from the input)
# }}
# """

#     print(f"Prompt: {prompt}\n")
    
#     result = generate_text(prompt)
    
#     if result:
#         print(f"Generation time: {result['generation_time']:.2f} seconds\n")
#         content = extract_content(result)
#         print(content)

#         model_output = content

#         # Remove optional triple quotes or markdown-style code fences
#         # This regex removes leading/trailing ⁠ json,  ⁠ or '''json
#         match = re.search(r"\{.*\}", model_output, flags=re.DOTALL)
#         try:
#             content_dict = eval(match.group(0))
#             return content_dict
#         except (AttributeError, SyntaxError) as e:
#             print("Failed to parse JSON:", e)
#             return None
#             # Add logic to just move onto the next loop
#     else:
#         print("Failed to get a response from the server.")
