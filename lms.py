import requests
import json
import time

def generate_text(prompt, model="qwen/qwen2.5-0.5b-instruct", api_url="http://localhost:1234/v1/chat/completions"):
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
        "max_tokens": 512
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        
        end_time = time.time()
        generation_time = end_time - start_time
        
        result = response.json()
        
        return {
            "response": result,
            "generation_time": generation_time
        }
    except requests.exceptions.RequestException as e:
        print(f"Error making request to LM Studio server: {e}")
        return None

def extract_content(response):
    if response and "response" in response:
        try:
            return response["response"]["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return "Error: Could not extract content from response"
    return "Error: No valid response received"

def extract_investment_profile(input):
    prompt = f"""{input}

Extract information from the investment profile above and condense into the JSON schema below. JSON output only.

{{
    "age": integer,
    "budget": integer,
    "investment_start": string (yyyy-mm-dd),
    "investment_end": string (yyyy-mm-dd),
    "avoids": [string],
    "salary": number or None
}}
"""

    print(f"Prompt: {prompt}\n")
    
    result = generate_text(prompt)
    
    if result:
        content = extract_content(result)
        import re

        model_output = content

        # Remove optional triple quotes or markdown-style code fences
        # This regex removes leading/trailing ⁠ json,  ⁠ or '''json
        cleaned = re.sub(r"^['\"⁠ ]*json['\" ⁠]*\s*|['\"`]*$", "", model_output.strip(), flags=re.IGNORECASE)

        # Now parse the JSON string to a Python dictionary
        try:
            data = json.loads(cleaned)
            print(data)
        except json.JSONDecodeError as e:
            print("Failed to parse JSON:", e)
        print(f"Generation time: {result['generation_time']:.2f} seconds\n")
        return cleaned[7:]
    else:
        print("Failed to get a response from the server.")

def create_payload(input):
    prompt = f"""{input}

Suggest appropriate number of tickers based on the risk number. It is a number from 0-1 with 1 being very very volatile. Try to diversify more if the risk index is low. Condense into the JSON schema below. JSON output only.
DO NOT WRITE ANYTHING OTHER THAN THE JSON OUTPUT!!!.
{{
    "tickers": [string],
    "budget": integer,
    "investment_start": string (yyyy-mm-dd),
    "investment_end": string (yyyy-mm-dd),
    "risk": number (use risk from the input)
}}
"""

    print(f"Prompt: {prompt}\n")
    
    result = generate_text(prompt)
    
    if result:
        print(f"Generation time: {result['generation_time']:.2f} seconds\n")
        content = extract_content(result)
        print(content)
        import re

        model_output = content

        # Remove optional triple quotes or markdown-style code fences
        # This regex removes leading/trailing ⁠ json,  ⁠ or '''json
        cleaned = re.sub(r"^['\"⁠ ]*json['\" ⁠]*\s*|['\"`]*$", "", model_output.strip(), flags=re.IGNORECASE)
        print(f"Cleaned in create_payload: {cleaned[7:]}")

        # Now parse the JSON string to a Python dictionary
        try:
            data = json.loads(cleaned)
            print(data)
        except json.JSONDecodeError as e:
            print("Failed to parse JSON:", e)
        print("!!!!!!!!!!!!!")
        print(cleaned[7:])
        return cleaned[7:]
    else:
        print("Failed to get a response from the server.")
