import psycopg as pg
import pandas as pd
from dotenv import load_dotenv
import os
import pandas as pd
import numpy as np
import scipy.optimize as sco
import math
import json

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

def generate_weights(rets_df: pd.DataFrame, I: int):
    """Generate I sets of weights at once"""
    noa = rets_df.shape[1]  # number of assets
    min_alloc = 0.5 / noa
    max_alloc = 2 / noa
    weights = np.zeros((I, noa))
    remaining = np.ones(I)

    for i in range(noa - 1):
        # Calculate valid ranges for all simulations at once
        min_for_this = np.maximum(
            min_alloc,
            remaining - (noa - i - 1) * max_alloc
        )
        max_for_this = np.minimum(
            max_alloc,
            remaining - (noa - i - 1) * min_alloc
        )

        # Generate weights for this asset for all simulations
        weights[:, i] = np.random.uniform(
            min_for_this, 
            max_for_this
        )
        remaining -= weights[:, i]

    # Set final weights
    weights[:, -1] = remaining

    # Return equal weights for any invalid combinations
    invalid_mask = (
        (weights < min_alloc).any(axis=1) | 
        (weights > max_alloc).any(axis=1) |
        ~np.isclose(weights.sum(axis=1), 1.0)
    )
    weights[invalid_mask] = np.full(noa, 1.0/noa)

    return weights

def get_returns_range(rets_df: pd.DataFrame) -> tuple[float, float]:
    """Get the range of returns for a set of weights"""
    weights = generate_weights(rets_df, 1_000)
    returns = portfolio_returns(rets_df, weights)
    return returns.min(), returns.max()

def efficient_frontier(rets_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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

def find_nearest(array, value):
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or math.fabs(value - array[idx - 1]) < math.fabs(value - array[idx])):
        return idx - 1
    else:
        return idx

def portfolio_for_volatility(rets_df: pd.DataFrame, target_vol: float):
    """Find the portfolio weights for a given target volatility"""
    t_rets, t_vols, weights = efficient_frontier(rets_df)
    vol_range = t_vols.max() - t_vols.min()
    target_vol = (vol_range * target_vol) + t_vols.min()
    idx = find_nearest(t_vols, target_vol)
    return weights[idx]

def shares_for_price(ticker: str, close_df: pd.DataFrame, price: float) -> float:
    return float(price / close_df[ticker].iloc[0])

def create_portfolio(payload: str) -> list[tuple[str, float]]:
    payload = json.loads(payload)
    # Get the log returns
    close = get_close(payload['tickers'], payload['investment_start'], payload['investment_end'])
    rets_df = get_log_rets(close)

    # Get the weights for the target volatility
    weights = portfolio_for_volatility(rets_df, payload['risk'])
    budget = payload['budget'] - payload['budget'] * 0.1  # 10% for fees

    # Return formatted results
    res_list = [(ticker, shares_for_price(ticker, close, float(weight) * budget)) for ticker, weight in zip(rets_df.columns, weights) if weight > 1e-5]
    return [{'ticker': ticker, 'quantity': int(shares)} for ticker, shares in res_list]

if __name__ == "__main__":
    # Example usage
    tickers = ['AAPL', 'ETSY', 'NVDA', 'TSLA', 'PYPL', 'GOOGL']
    print(create_portfolio({
        'tickers': tickers,
        'start_date': '2019-08-09',
        'end_date': '2022-02-14',
        'target_vol': 0.2,
        'budget': 18000
    }))
