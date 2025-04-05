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

{
    "name": string,
    "age": integer,
    "budget": integer,
    "investment_start": string,
    "investment_end": string,
    "hobbies": [string],
    "avoids": [string],
    "employer": string or null,
    "salary": number or null
}
"""

    print(f"Prompt: {prompt}\n")
    
    result = generate_text(prompt)
    
    if result:
        print(f"Generation time: {result['generation_time']:.2f} seconds\n")
        content = extract_content(result)
        print(content)
        return content
    else:
        print("Failed to get a response from the server.")
