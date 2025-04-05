import psycopg as pg
import pandas as pd
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
import scipy.optimize as sco

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

    rets = np.array(rets_df.mean())
    if weights.ndim == 1:
        weights /= weights.sum()  # Normalize weights
        return float(np.sum(rets * weights) * 252)
    else:
        return np.sum(rets * weights, axis=1) * 252

def portfolio_volatility(rets_df: pd.DataFrame, weights: list[float]):
    weights = np.array(weights)

    cov_matrix = rets_df.cov() * 252
    if weights.ndim == 1:
        weights /= weights.sum()  # Normalize weights
        return float(np.sqrt(np.sum(weights * (weights @ cov_matrix))))
    else:
        return np.array(np.sqrt(np.sum(weights * (weights @ cov_matrix), axis=1)))

def generate_weights(rets_df: pd.DataFrame, I: int) -> np.ndarray:
    """Generate I sets of random weights that sum to 1"""
    noa = rets_df.shape[1]  # number of assets
    weights = np.random.random((I, noa))
    # Normalize each row to sum to 1
    weights /= weights.sum(axis=1)[:, np.newaxis]
    return weights

def get_returns_range(rets_df: pd.DataFrame) -> tuple[float, float]:
    """Get the range of returns for a set of weights"""
    weights = generate_weights(rets_df, 1_000)
    returns = portfolio_returns(rets_df, weights)
    return returns.min(), returns.max()

def efficient_frontier(rets_df: pd.DataFrame):
    noa = rets_df.shape[1]  # number of assets
    eweights = np.array(noa * [1.0 / noa])

    def min_vol(weights):
       return portfolio_volatility(rets_df, weights)

    min_rets, max_rets = get_returns_range(rets_df)

    t_rets = np.linspace(min_rets, max_rets, 50)
    t_vols = []
    weights = []
    for target_ret in t_rets:
        constraints = ({'type': 'eq', 'fun': lambda x: portfolio_returns(rets_df, x) - target_ret},
                        {'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bounds = tuple((0, 1) for _ in range(noa))
        result = sco.minimize(min_vol, eweights, method='SLSQP', bounds=bounds, constraints=constraints)
        weights.append(result['x'])
        t_vols.append(result['fun'])

    t_vols = np.array(t_vols)
    weights = np.array(weights)

    return t_rets, t_vols, weights

if __name__ == "__main__":
    # Example usage
    tickers = ['AAPL', 'MSFT', 'NVDA']
    df = get_close(tickers, '2023-01-01', '2025-01-01')
    log_rets = get_log_rets(df)
    print(get_returns_range(log_rets))
    # print(get_returns_range(log_rets))
