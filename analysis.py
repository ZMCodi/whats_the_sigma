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

def get_close(tickers: list[str], start_date: str, end_date: str) -> pd.DataFrame:
    # Convert Python list to SQL-friendly format: ('AAPL', 'MSFT')
    ticker_str = "(" + ", ".join([f"'{ticker}'" for ticker in tickers]) + ")"

    with pg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            query = f"""
                SELECT date, ticker, adj_close::float 
                FROM daily
                WHERE ticker IN {ticker_str}
                AND date BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY date
            """
            cur.execute(query)
            data = cur.fetchall()

    # Convert to DataFrame and pivot to get tickers as columns
    df = pd.DataFrame(data, columns=['date', 'ticker', 'adj_close'])
    df['adj_close'] = df['adj_close'].astype(float)  # Ensure adj_close is float
    df = df.pivot(index='date', columns='ticker', values='adj_close')

    return df

def get_log_rets(prices_df: pd.DataFrame) -> pd.DataFrame:
    return np.log(prices_df / prices_df.shift(1)).dropna()

def portfolio_returns(rets_df: pd.DataFrame, weights: list[float]):
    weights = np.array(weights)
    weights /= weights.sum()  # Normalize weights

    rets = np.array(rets_df.mean())
    if weights.ndim == 1:
        return float(np.sum(rets * weights) * 252)
    else:
        return np.sum(rets * weights, axis=1) * 252

def portfolio_volatility(rets_df: pd.DataFrame, weights: list[float]):
    weights = np.array(weights)
    weights /= weights.sum()  # Normalize weights

    cov_matrix = rets_df.cov() * 252
    if weights.ndim == 1:
        return float(np.sqrt(np.sum(weights * (weights @ cov_matrix))))
    else:
        return np.array(np.sqrt(np.sum(weights * (weights @ cov_matrix), axis=1)))


if __name__ == "__main__":
    # Example usage
    tickers = ['AAPL', 'MSFT', 'NVDA']
    df = get_close(tickers, '2023-01-01', '2025-01-01')
    log_rets = get_log_rets(df)
    print(portfolio_volatility(log_rets, [0.5, 0.3, 0.2]))
