import requests
import json
import time
import re
import os
from dotenv import load_dotenv

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
                        "text": "You are a financial advisor at the biggest investment firm in the world. You are very good at creating portfolios."
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
            "maxOutputTokens": 512,
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
7. Pay attention to the sectors the customer explicitly wants to avoid.
8. The risk index is a number from 0-1 with 1 being very very volatile. Choose an appropriate index for the client.
9. Don't be afraid to suggest a lot of tickers (10+) if the risk index is low and budget is large enough
10. Take into account the stock behavior within the client's investment timeframe.

Based on this, create a JSON schema with the following fields. DO NOT FORGET ANY FIELDS:

{{
    "tickers": list of tickers that the client should invest in based on the guidelines above,
    "budget": integer,
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
