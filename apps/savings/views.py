from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def savings_view(request):
    context = {'is_menu': True}
    return render(request, 'savings/savings_view.html', context)
