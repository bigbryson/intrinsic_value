# /apps/holdings/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from schwab.client import Client
from apps.connection_page.models import SchwabToken

@login_required
def holdings_list(request):
    holdings = []
    try:
        # Get the token for the current user
        token = SchwabToken.objects.get(user=request.user)

        # Initialize the client with the user's token
        api_client = Client.from_access_token(
            access_token=token.access_token,
            app_key=settings.SCHWAB_APP_KEY,
            app_secret=settings.SCHWAB_APP_SECRET,
            token_updater=None # Not needed for read-only operations
        )

        # Fetch account holdings
        response = api_client.get_account_holdings('positions')
        if response.ok:
            accounts = response.json()
            # We'll just use the first account for this example
            if accounts and len(accounts) > 0:
                holdings = accounts[0].get('positions', [])
        else:
            print(f"Error fetching holdings: {response.text}")

    except SchwabToken.DoesNotExist:
        # Handle case where user has no token
        print("User does not have a Schwab token.")
    except Exception as e:
        print(f"An error occurred: {e}")

    context = {
        'holdings': holdings
    }
    return render(request, 'holdings/holdings_list.html', context)
