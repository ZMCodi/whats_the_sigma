# Use to classify risk (high, med, low)
import json
import datetime

def risk_eval(profile_dict):
    profile_dict = json.loads(profile_dict)
    try:
        score = 0
        

        if profile_dict["age"] < 30:
            score += 1
        elif profile_dict["age"] > 60:
            score -= 1
        

        budget = profile_dict["budget"]["amount"] if isinstance(profile_dict["budget"], dict) else profile_dict["budget"]
        

        start_datetime = profile_dict["investment_start"]
        end_datetime = profile_dict["investment_end"]
        
        try:
            if start_datetime and end_datetime:
                start_date = datetime.datetime.strptime(start_datetime, "%Y-%m-%d")
                end_date = datetime.datetime.strptime(end_datetime, "%Y-%m-%d")
                
                investment_duration = (end_date - start_date).days / 365.25
                
                if investment_duration < 1:
                    score += 1  
                elif investment_duration > 5:
                    score -= 1
        except:
            pass
            
        avoid_industries = profile_dict.get("avoid_industries", [])
        if not avoid_industries and "avoids" in profile_dict:
            avoid_industries = profile_dict["avoids"]
            
        avoided = [sector.lower() for sector in avoid_industries]
        high_risk = ["technology", "financial services", "consumer cyclical", "energy", "industrials"]
        
        for sector in avoided:
            if any(risk_sector in sector for risk_sector in high_risk):
                score -= 1
            
        if "utilities" in avoided or "consumer defensive" in avoided:
            score += 1
     
        if score >= 3:
            risk = 1   
        elif score > 0:
            risk = 0.6666 
        else:
            risk = 0.3333

        result = {
            "name": profile_dict.get("name"),
            "age": profile_dict.get("age"),
            "budget": budget,
            "investment_start": start_datetime,
            "investment_end": end_datetime,
            "hobbies": profile_dict.get("hobbies", []),
            "avoids": avoid_industries,
            "employer": profile_dict.get("employer"),
            "salary": profile_dict.get("salary"),
            "risk": risk
        }
        
        return result
    
    except:
        pass
