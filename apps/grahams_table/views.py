# django_stock_screener_materio/apps/screener_app/views.py
from django.shortcuts import render, get_object_or_404
from web_project.views import TemplateView # <-- Make sure this is the one being used
from django.utils.translation import gettext_lazy as _
from .data_services import get_screener_data_for_symbols, get_stock_detail_data
from django.core.paginator import Paginator
import pandas as pd
import logging
from django.conf import settings
from django.core.cache import cache
import os
from web_project import TemplateLayout # Import TemplateLayout

logger = logging.getLogger(__name__)

class StockScreenerPageView(TemplateView):
    def get(self, request, *args, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        # --- High-Performance Workflow ---

        # Get pre-filtered list of valid symbols, using cache
        valid_symbols = cache.get('valid_screener_symbols')
        if not valid_symbols:
            valid_tickers_file = os.path.join(settings.DOLT_EARNINGS_DATA_PATH, "valid_tickers_for_screener.txt")
            if not os.path.exists(valid_tickers_file):
                context['error_message'] = "The list of valid stocks has not been generated yet. Please run 'python manage.py prefilter_tickers' from your terminal."
                return render(request, 'grahams_table/error_page.html', context)

            with open(valid_tickers_file, 'r') as f:
                valid_symbols = [line.strip() for line in f if line.strip()]
            cache.set('valid_screener_symbols', valid_symbols, 3600)

        # Handle Search
        search_query = request.GET.get('q', '').strip()
        symbols_to_display = valid_symbols
        if search_query:
            symbols_to_display = [s for s in valid_symbols if search_query.upper() in s.upper()]

        # Paginate the list of SYMBOLS
        paginator = Paginator(symbols_to_display, 15)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Process data ONLY for the symbols on the current page
        processed_stocks = get_screener_data_for_symbols(page_obj.object_list)

        table_headers = [
            "Company Name", "Symbol", "Prev. Close", "Avg P/E (5yr)",
            "Graham Num", "Graham Diff %", "Intrinsic Val", "Intrinsic Diff %",
            "EPS AVG (5yr)", "Growth Rate (avg past 10 yrs)"
        ]

        context.update({
            'page_obj': page_obj,
            'stocks_list': processed_stocks,
            'page_title': _('Stock Screener'),
            'table_headers': table_headers,
            'search_query': search_query,
            'total_results': paginator.count
        })
        return render(request, 'grahams_table/grahams_table_list.html', context)

class StockDetailView(TemplateView):
    def get(self, request, *args, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))

        symbol_ticker = kwargs.get('symbol').upper()
        stock_data = get_stock_detail_data(symbol_ticker)

        context.update({
            'page_title': f"{stock_data.get('profile', {}).get('longName', symbol_ticker)} ({symbol_ticker})",
            'symbol': symbol_ticker,
            'profile': stock_data.get('profile'),
            'chart_data': stock_data.get('chart_data'),
            'key_stats': stock_data.get('key_stats'),
            'returns_data': stock_data.get('returns_data'),
            'financials': stock_data.get('financials'),
            'calculations': stock_data.get('calculations'),
        })
        return render(request, 'grahams_table/grahams_table_list.html', context)

class StockFinancialsView(TemplateView):
    def get(self, request, *args, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        symbol_ticker = kwargs.get('symbol').upper()
        statement_type = kwargs.get('statement_type')

        # You can add logic here later to fetch the specific financial data
        # based on the statement_type (e.g., balance-sheet, income-statement)
        # For now, we'll just set the context for the template.

        stock_data = get_stock_detail_data(symbol_ticker) # Reuse existing function to get company name

        context.update({
            'page_title': f"{stock_data.get('profile', {}).get('longName', symbol_ticker)} - {statement_type.replace('-', ' ').title()}",
            'symbol': symbol_ticker,
            'statement_type': statement_type,
            'detail_page_name': statement_type, # This is for highlighting the active menu item
        })
        return render(request, 'grahams_table/grahams_table_list.html', context)
