# /apps/holdings/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
import json
from apps.connection_page.models import SchwabToken

@login_required
def holdings_list(request):
    holdings = []
    total_market_value = 0
    total_day_gain_loss = 0
    total_cost_basis = 0
    error_message = None

    try:
        token_obj = SchwabToken.objects.get(user=request.user)
        accounts_url = f'https://api.schwabapi.com/trader/v1/accounts?fields=positions'
        headers = { 'Authorization': f'Bearer {token_obj.access_token}' }

        response = requests.get(accounts_url, headers=headers)
        response.raise_for_status()
        accounts_data = response.json()

        if accounts_data and isinstance(accounts_data, list) and len(accounts_data) > 0:
            first_account = accounts_data[0]
            if 'securitiesAccount' in first_account:
                holdings = first_account['securitiesAccount'].get('positions', [])

                # Calculate portfolio totals
                if holdings:
                    total_market_value = sum(p.get('marketValue', 0) for p in holdings)
                    total_day_gain_loss = sum(p.get('currentDayProfitLoss', 0) for p in holdings)
                    total_cost_basis = sum(p.get('averagePrice', 0) * p.get('longQuantity', 0) for p in holdings)

    except SchwabToken.DoesNotExist:
        error_message = "You haven't connected a Schwab account yet."
    except requests.exceptions.HTTPError as e:
        error_message = f"API Error: Could not fetch holdings. The token may have expired."
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"

    context = {
        'holdings': holdings,
        'total_market_value': total_market_value,
        'total_day_gain_loss': total_day_gain_loss,
        'total_cost_basis': total_cost_basis,
        'error_message': error_message,
        'is_menu': True,
    }
    return render(request, 'holdings/holdings_list.html', context)
