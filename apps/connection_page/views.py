from django.shortcuts import redirect, render
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import SchwabToken
import urllib.parse
import requests
import base64
from oauthlib.oauth1.rfc5849 import SIGNATURE_HMAC, SIGNATURE_TYPE_AUTH_HEADER
from requests_oauthlib import OAuth1Session


@login_required
def schwab_authenticate(request):
    auth_url = 'https://api.schwabapi.com/v1/oauth/authorize'
    # This dynamically builds the URL that MUST match the portal
    redirect_uri = request.build_absolute_uri(reverse('connection_page:schwab_callback'))
    params = {
        'client_id': settings.SCHWAB_APP_KEY,
        'redirect_uri': redirect_uri
    }
    print(f"Redirecting to Schwab with callback: {redirect_uri}") # For debugging
    return redirect(f'{auth_url}?{urllib.parse.urlencode(params)}')

@login_required
def schwab_callback(request):
    auth_code = request.GET.get('code')
    if not auth_code:
        return render(request, 'error.html', {'error': 'Schwab authorization code not found.'})

    # This also dynamically builds the URL that MUST match the portal
    redirect_uri = request.build_absolute_uri(reverse('connection_page:schwab_callback'))
    print(f"Handling Schwab callback with redirect_uri: {redirect_uri}") # For debugging

    try:
        token_url = 'https://api.schwabapi.com/v1/oauth/token'
        client_creds = f"{settings.SCHWAB_APP_KEY}:{settings.SCHWAB_APP_SECRET}"
        encoded_creds = base64.b64encode(client_creds.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded_creds}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': redirect_uri
        }
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()

        SchwabToken.objects.update_or_create(
            user=request.user,
            defaults={
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in'),
            }
        )
        request.session['has_brokerage_connection'] = True
        return redirect('holdings:holdings_list')
    except Exception as e:
        print(f"Error during Schwab token exchange: {e}")
        if hasattr(e, 'response'):
            print(f"Response Body: {e.response.text}")
        return render(request, 'error.html', {'error': 'Failed to retrieve Schwab tokens.'})

# ... (E*TRADE views remain the same) ...

@login_required
def etrade_authenticate(request):
    request_token_url = 'https://api.etrade.com/oauth/request_token'
    authorize_url = 'https://us.etrade.com/e/t/etws/authorize'
    oauth = OAuth1Session(
        client_key=settings.ETRADE_CONSUMER_KEY,
        client_secret=settings.ETRADE_CONSUMER_SECRET,
        callback_uri="oob",
        signature_method=SIGNATURE_HMAC,
        signature_type=SIGNATURE_TYPE_AUTH_HEADER,
    )
    try:
        fetch_response = oauth.fetch_request_token(request_token_url)
        request.session['etrade_request_token'] = fetch_response.get('oauth_token')
        request.session['etrade_request_token_secret'] = fetch_response.get('oauth_token_secret')
        full_authorize_url = oauth.authorization_url(authorize_url)
        return redirect(full_authorize_url)
    except Exception as e:
        return render(request, 'error.html', {'error': 'Failed to get E*TRADE request token.'})

@login_required
def etrade_callback(request):
    access_token_url = 'https://api.etrade.com/oauth/access_token'
    oauth_verifier = request.GET.get('oauth_verifier')
    if not oauth_verifier:
        return render(request, 'error.html', {'error': 'E*TRADE verifier not found.'})
    oauth = OAuth1Session(
        client_key=settings.ETRADE_CONSUMER_KEY,
        client_secret=settings.ETRADE_CONSUMER_SECRET,
        resource_owner_key=request.session.get('etrade_request_token'),
        resource_owner_secret=request.session.get('etrade_request_token_secret'),
        verifier=oauth_verifier,
        signature_method=SIGNATURE_HMAC,
        signature_type=SIGNATURE_TYPE_AUTH_HEADER,
    )
    try:
        oauth_tokens = oauth.fetch_access_token(access_token_url)
        request.session['etrade_access_token'] = oauth_tokens.get('oauth_token')
        request.session['etrade_access_token_secret'] = oauth_tokens.get('oauth_token_secret')
        request.session['has_brokerage_connection'] = True
        return redirect('holdings:holdings_list')
    except Exception as e:
        return render(request, 'error.html', {'error': 'Failed to get E*TRADE access token.'})
