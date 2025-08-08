# /apps/transactions/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .data_services import get_transactions_for_user
from datetime import datetime, timedelta

@login_required
def transactions_list(request):
    """
    Displays categorized and summarized lists of transactions with a date filter.
    """
    # --- Handle Date Filtering ---
    today = datetime.now()
    start_date_str = request.GET.get('start_date', (today - timedelta(days=90)).strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', today.strftime('%Y-%m-%d'))

    # Convert string dates from the form into datetime objects for the API call
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    all_transactions = get_transactions_for_user(request.user, start_date, end_date)
    error_message = None

    # --- Categorize and Summarize Transactions ---
    categories = {
        "deposits_and_withdrawals": [], "dividends_and_interest": [],
        "transfers": [], "trades": [], "other": []
    }
    sums = {key: 0 for key in categories}

    for trx in all_transactions:
        trx_type = trx.get('type', '').upper()
        net_amount = trx.get('netAmount', 0)

        if 'DEPOSIT' in trx_type or 'WITHDRAWAL' in trx_type:
            categories["deposits_and_withdrawals"].append(trx)
            sums["deposits_and_withdrawals"] += net_amount
        elif 'DIVIDEND' in trx_type or 'INTEREST' in trx_type:
            categories["dividends_and_interest"].append(trx)
            sums["dividends_and_interest"] += net_amount
        elif 'TRANSFER' in trx_type:
            categories["transfers"].append(trx)
            sums["transfers"] += net_amount
        elif trx_type == 'TRADE':
            categories["trades"].append(trx)
            sums["trades"] += net_amount
        else:
            categories["other"].append(trx)
            sums["other"] += net_amount

    if not all_transactions:
        error_message = f"No transactions found for the selected date range ({start_date_str} to {end_date_str})."

    context = {
        'transactions_by_cat': categories,
        'sums_by_cat': sums,
        'error_message': error_message,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'is_menu': True,
    }
    return render(request, 'transactions/transactions_list.html', context)
