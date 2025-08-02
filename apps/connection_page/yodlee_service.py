# /apps/connection_page/yodlee_service.py
import requests
from django.conf import settings

def get_yodlee_fastlink_token():
    """
    Gets a user-specific token for one of Yodlee's pre-built sandbox users.
    This is the required method for testing the FastLink flow.
    """
    # NOTE: In a live production app, you would use the actual user's loginName.
    # For the Yodlee sandbox, we MUST use one of their provided test users.
    YODLEE_SANDBOX_USER = 'sbMem6v8nce94w58b61'

    url = f"{settings.YODLEE_API_URL}/auth/token"
    headers = {
        'Api-Version': '1.1',
        'loginName': YODLEE_SANDBOX_USER,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'clientId': settings.YODLEE_CLIENT_ID,
        'secret': settings.YODLEE_SECRET
    }

    try:
        print(f"Requesting FastLink token for Yodlee sandbox user: {YODLEE_SANDBOX_USER}...")
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        print("Successfully received FastLink token.")
        return token_data.get('token', {}).get('accessToken')
    except requests.exceptions.HTTPError as e:
        print(f"Error getting Yodlee FastLink token: {e.response.text}")
        return None

