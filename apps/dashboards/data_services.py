# /apps/dashboards/data_services.py
import requests
from django.conf import settings
from apps.connection_page.models import SchwabToken

def get_market_movers(user):
    """
    Fetches market movers (top gainers, losers, etc.) from the Schwab API.
    """
    movers_data = {
        'top_gainers': [],
        'top_losers': [],
        'most_active': []
    }
    try:
        token_obj = SchwabToken.objects.get(user=user)
        headers = {'Authorization': f'Bearer {token_obj.access_token}'}

        # We will fetch movers for the S&P 500 index
        index_symbol = '$SPX.X'
        movers_url = f'https://api.schwabapi.com/marketdata/v1/movers/{index_symbol}'

        # --- Get Top Gainers ---
        params_gainers = {'sort': 'PERCENT_CHANGE_UP', 'frequency': 1}
        response_gainers = requests.get(movers_url, headers=headers, params=params_gainers)
        if response_gainers.ok:
            movers_data['top_gainers'] = response_gainers.json().get('movers', [])

        # --- Get Top Losers ---
        params_losers = {'sort': 'PERCENT_CHANGE_DOWN', 'frequency': 1}
        response_losers = requests.get(movers_url, headers=headers, params=params_losers)
        if response_losers.ok:
            movers_data['top_losers'] = response_losers.json().get('movers', [])

        # --- Get Most Active ---
        params_active = {'sort': 'VOLUME', 'frequency': 1}
        response_active = requests.get(movers_url, headers=headers, params=params_active)
        if response_active.ok:
            movers_data['most_active'] = response_active.json().get('movers', [])

    except SchwabToken.DoesNotExist:
        print("User does not have a Schwab token.")
    except Exception as e:
        print(f"An error occurred while fetching market movers: {e}")

    return movers_data
