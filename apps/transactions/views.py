from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def transactions_list(request):
    context = {'is_menu': True}
    return render(request, 'transactions/transactions_list.html', context)
