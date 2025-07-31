from django.shortcuts import redirect, render
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import SchwabToken
import urllib.parse
import requests
import base64

# E*TRADE imports
from oauthlib.oauth1.rfc5849 import SIGNATURE_HMAC, SIGNATURE_TYPE_AUTH_HEADER
from requests_oauthlib import OAuth1Session

# --- This function needs to be restored ---
@login_required
def get_schwab_api_client(request):
    """
    Initializes the schwab-py Client and defines the token update mechanism.
    """
    def token_updater(token_data):
        SchwabToken.objects.update_or_create(
            user=request.user,
            defaults={
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in'),
            }
        )
    # The client must be created first, before it can be used to get a token.
    return Client(settings.SCHWAB_APP_KEY, token_updater=token_updater)


@login_required
def schwab_authenticate(request):
    """
    Builds the authorization URL and redirects the user to Schwab.
    """
    auth_url = 'https://api.schwabapi.com/v1/oauth/authorize'
    params = {
        'client_id': settings.SCHWAB_APP_KEY,
        'redirect_uri': request.build_absolute_uri(reverse('connection_page:callback'))
    }
    return redirect(f'{auth_url}?{urllib.parse.urlencode(params)}')


@login_required
def schwab_callback(request):
    """
    Handles the callback from Schwab by manually exchanging the authorization
    code for an access token and saving it.
    """
    auth_code = request.GET.get('code')
    if not auth_code:
        return render(request, 'error.html', {'error': 'Authorization code not found.'})

    try:
        # 1. Prepare the token request
        token_url = 'https://api.schwabapi.com/v1/oauth/token'

        # Create the authorization header
        client_creds = f"{settings.SCHWAB_APP_KEY}:{settings.SCHWAB_APP_SECRET}"
        encoded_creds = base64.b64encode(client_creds.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded_creds}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # Prepare the data payload
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': request.build_absolute_uri(reverse('connection_page:callback'))
        }

        # 2. Make the POST request to get the token
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()  # Raise an exception for bad responses (4xx or 5xx)
        token_data = response.json()

        # 3. Save the token to the database
        SchwabToken.objects.update_or_create(
            user=request.user,
            defaults={
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in'),
            }
        )

        # 4. Set session flag and redirect
        request.session['has_brokerage_connection'] = True
        return redirect('holdings:holdings_list')

    except Exception as e:
        print(f"Error during Schwab token exchange: {e}")
        return render(request, 'error.html', {'error': 'Failed to retrieve tokens.'})


# --- E*TRADE Views (No changes needed) ---
@login_required
def etrade_authenticate(request):
    # This logic remains the same
    # ...
    pass

@login_required
def etrade_callback(request):
    # This logic also remains the same
    # ...
    request.session['has_brokerage_connection'] = True
    return redirect('holdings:holdings_list')
