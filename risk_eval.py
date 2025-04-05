# Use to classify risk (high, med, low)
import json
import datetime

def risk_eval(profile_json):
    try:
        with open(profile_json, 'r') as file:
            data = json.load(file)
    
    except:
        print("Error: Unable to parse JSON data.")
        return None
    

    score = 0
    output = data[0]["output"]

    if output["age"] < 30:
        score += 1
    elif output["age"] > 60:
        score -= 1
    
    
    budget = output["budget"]

    start_datetime = output["investment_start"]
    end_datetime = output["investment_end"]
    
    try:
        start_date = datetime.datetime.strptime(start_datetime, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end_datetime, "%Y-%m-%d")

        investment_duration = (end_date - start_date).days / 365.25

        if investment_duration < 3:
            score += 1
        elif investment_duration > 10:
            score -= 1

        
    except:
        pass

    avoided = [sector.lower() for sector in output["avoid_industries"]]
    high_risk = ["technology", "financial services", "consumer cyclical", "energy", "industrials"]
    
    for sector in avoided:
        if sector in high_risk:
            score -= 1
        
        elif "utilities" in avoided or "consumer defensive" in avoided:
            score += 1
    
    if score >= 3:
        risk = "high"
    
    if score > 0:
        risk = "medium"
    
    else:
        risk = "low"
    
    print(risk)



        
    
  
    
risk_eval("data.json")
