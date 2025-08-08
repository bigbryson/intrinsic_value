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
    error_message = None

    try:
        token_obj = SchwabToken.objects.get(user=request.user)
        accounts_url = f'https://api.schwabapi.com/trader/v1/accounts?fields=positions'
        headers = {
            'Authorization': f'Bearer {token_obj.access_token}'
        }

        response = requests.get(accounts_url, headers=headers)
        response.raise_for_status()
        accounts_data = response.json()

        if accounts_data and isinstance(accounts_data, list) and len(accounts_data) > 0:
            first_account = accounts_data[0]
            if 'securitiesAccount' in first_account:
                holdings = first_account['securitiesAccount'].get('positions', [])

    except SchwabToken.DoesNotExist:
        error_message = "You haven't connected a Schwab account yet."
    except requests.exceptions.HTTPError as e:
        error_message = f"API Error: Could not fetch holdings. The token may have expired. Details: {e.response.text}"
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"

    context = {
        'holdings': holdings,
        'error_message': error_message,
        'is_menu': True,
    }
    return render(request, 'holdings/holdings_list.html', context)

## below is the yodlee holdings api

# @login_required
# def holdings_list(request):
#     accounts = []
#     error_message = None

#     try:
#         # Get a token for the sandbox user to make API calls
#         user_token = yodlee_service.get_yodlee_fastlink_token()
#         if user_token:
#             # Use the token to get the list of linked accounts
#             accounts = yodlee_service.get_yodlee_accounts(user_token)
#         else:
#             error_message = "Could not get a token to fetch Yodlee accounts."

#     except Exception as e:
#         error_message = f"An unexpected error occurred: {e}"
#         print(f"An error occurred in holdings_list: {e}")

#     context = {
#         'accounts': accounts, # We are now passing 'accounts'
#         'error_message': error_message,
#         'is_menu': True,
#     }
#     return render(request, 'holdings/holdings_list.html', context)
