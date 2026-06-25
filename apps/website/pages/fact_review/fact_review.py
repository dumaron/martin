from django.shortcuts import get_object_or_404, redirect, render

from apps.website.pages.page import Page
from core import hkm
from core.hkm.models import Transaction

page = Page(name='fact_review_page', base_route='knowledge/review/<int:transaction_id>')


@page.main
def main_render(request, transaction_id):
	transaction = get_object_or_404(Transaction, pk=transaction_id)
	review = hkm.review_transaction(transaction.id)
	return render(request, 'fact_review/fact_review.html', {'transaction': transaction, 'review': review})


@page.action('apply')
def apply_draft(request, transaction_id):
	transaction = get_object_or_404(Transaction, pk=transaction_id)
	hkm.apply_transaction(transaction)
	return redirect('entity_list_page.main_render')


@page.action('discard')
def discard_draft(request, transaction_id):
	transaction = get_object_or_404(Transaction, pk=transaction_id)
	hkm.discard_draft(transaction)
	return redirect('fact_create_page.main_render')
