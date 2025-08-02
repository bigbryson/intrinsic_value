# /apps/connection_page/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from . import yodlee_service

@login_required
def generate_fastlink_token(request):
    """
    Generates the user-specific token needed to launch FastLink
    by using a pre-configured Yodlee sandbox user.
    """
    # Corrected function name
    fastlink_token = yodlee_service.get_yodlee_fastlink_token()

    if not fastlink_token:
        return JsonResponse({'error': 'Could not generate FastLink token'}, status=500)

    return JsonResponse({'fastlink_token': fastlink_token})

# Add this back in as it is used by your dashboard's JavaScript
@login_required
def yodlee_success_callback(request):
    """
    This view is called by the frontend after a successful FastLink connection.
    It sets a session flag to prevent the connection modal from showing again.
    """
    request.session['has_brokerage_connection'] = True
    return JsonResponse({'status': 'ok'})
