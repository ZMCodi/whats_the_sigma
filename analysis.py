import psycopg as pg
import pandas as pd
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np

# Load environment variables from .env file
load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def get_data(tickers: list[str], start_date: str, end_date: str) -> pd.DataFrame:
    # Convert Python list to SQL-friendly format: ('AAPL', 'MSFT')
    ticker_str = "(" + ", ".join([f"'{ticker}'" for ticker in tickers]) + ")"
    
    with pg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            query = f"""
                SELECT date, ticker, adj_close 
                FROM daily
                WHERE ticker IN {ticker_str}
                AND date BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY date
            """
            cur.execute(query)
            data = cur.fetchall()

    # Convert to DataFrame and pivot to get tickers as columns
    df = pd.DataFrame(data, columns=['date', 'ticker', 'adj_close'])
    df = df.pivot(index='date', columns='ticker', values='adj_close')

    return df

if __name__ == "__main__":
    # Example usage
    tickers = ['AAPL', 'MSFT', 'NVDA']
    df = get_data(tickers, '2023-01-01', '2025-01-01')
    print(df.head())
