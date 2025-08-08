# /apps/transactions/data_services.py
import requests
from django.conf import settings
from apps.connection_page.models import SchwabToken
from datetime import datetime, timedelta
import json
import pandas as pd

# The function now accepts a date range
def get_transactions_for_user(user, start_date, end_date):
    """
    Fetches transaction history for a user's linked Schwab account for a specific date range.
    """
    try:
        token_obj = SchwabToken.objects.get(user=user)
        headers = {'Authorization': f'Bearer {token_obj.access_token}'}

        # Step 1: Get the account hash
        account_numbers_url = 'https://api.schwabapi.com/trader/v1/accounts/accountNumbers'
        acc_num_response = requests.get(account_numbers_url, headers=headers)
        acc_num_response.raise_for_status()
        account_hashes = acc_num_response.json()

        if not (account_hashes and isinstance(account_hashes, list) and len(account_hashes) > 0):
            return []

        account_hash = account_hashes[0].get('hashValue')
        if not account_hash:
            return []

        # Step 2: Use the hash to fetch transactions with the provided date range
        transactions_url = f'https://api.schwabapi.com/trader/v1/accounts/{account_hash}/transactions'
        params = {
            'startDate': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'endDate': end_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }

        trx_response = requests.get(transactions_url, headers=headers, params=params)
        trx_response.raise_for_status()

        return trx_response.json()

    except SchwabToken.DoesNotExist:
        print(">>> ERROR: User does not have a Schwab token.")
        return []
    except requests.exceptions.HTTPError as e:
        print(f">>> HTTP ERROR fetching transactions: {e.response.text}")
        return []
    except Exception as e:
        print(f">>> UNEXPECTED ERROR occurred: {e}")
        return []
def get_historical_portfolio_value(user):
    """
    Calculates the historical market value of a user's portfolio based on
    their transaction history. This is a simplified example.
    """
    # For this example, we'll generate some sample data.
    # In a real-world scenario, this function would need to:
    # 1. Fetch all transactions (not just the last 90 days).
    # 2. Get historical price data for each symbol.
    # 3. Iterate through time, calculating the portfolio value at each step.

    # --- Sample Data Generation ---
    dates = pd.date_range(end=datetime.now(), periods=180).to_pydatetime().tolist()
    # Generate a sample random walk for the portfolio value
    value = 100000
    values = []
    for _ in dates:
        value += (pd.np.random.randn() - 0.5) * 1000
        values.append(round(value, 2))

    # The function should return data in a format the chart can use
    return {
        'dates': [d.strftime('%Y-%m-%d') for d in dates],
        'values': values
    }
