# Whats the Sigma - Portfolio Optimization Challenge

A portfolio optimization algorithm developed for Manchester Trading Society's Portfolio Risk and Investment Management challenge at StudentHack.

## 📋 Overview

This project was developed during StudentHack, where we competed in Manchester Trading Society's Portfolio Risk and Investment Management challenge. The goal was to build optimal investment portfolios for different investor profiles within specific timeframes and budget constraints.

### 📝 Context
- We were given investor profiles with demographic information, preferences, and investment constraints
- Each investor had a specific investment timeframe and budget
- We needed to recommend appropriate stocks and allocation amounts

### 🎯 Goal
- Build investment portfolios by specifying tickers and their respective shares
- Optimize portfolios to best accommodate each client's risk tolerance and preferences
- Achieve the best risk-adjusted return possible within the given constraints

### ⚙️ Implementation
Our approach involved two main components:
1. Use Google Gemini Flash to analyze investor profiles and determine appropriate tickers and risk indices
2. Run the tickers through an Efficient Frontier optimization algorithm to calculate optimal portfolio weights

### 💡 Highlights
- Highly vectorized code allowing for fast response times (~1.2 seconds with LLM integration)
- During low-latency rounds, we implemented a simpler algorithm that could submit responses every 0.2 seconds
- Finished 2nd place in the final three rounds of the competition
- Gained valuable experience building a low-latency financial application

## 🧠 Key Technologies

- **Python** - Core programming language
- **Pandas/NumPy** - Data manipulation and numerical calculations
- **SciPy** - Portfolio optimization
- **PostgreSQL/TimescaleDB** - Database for stock market data
- **Google Gemini API** - Natural language processing for investor profile analysis

## 🔍 Key Components

### `analysis.py`
Contains the portfolio optimization logic using Modern Portfolio Theory, implementing the Efficient Frontier algorithm to determine optimal stock weightings based on historical returns and volatility.

### `lms.py`
Handles communication with Google Gemini API to analyze investor profiles and extract relevant information for portfolio construction. Implements both full LLM analysis and faster heuristic-based approaches.

### `main.py`
The main execution script that coordinates the overall process: fetching investor profiles, generating portfolio recommendations, and submitting results to the competition server.

### `stocks.py`
Organizes stocks by sector and category, allowing for diversification and sector-based allocation strategies.

## 📊 Future Improvements

- Implement more sophisticated risk models
- Integrate alternative data sources for better predictions
- Optimize algorithm performance further for even lower latency
- Add more comprehensive backtesting capabilities
