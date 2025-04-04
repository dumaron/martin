from core.models import YnabCategory
from core.adapters.ynab import get_categories


def sync_ynab_categories():
    ynab_categories = get_categories()
    for category in ynab_categories:
        YnabCategory.objects.update_or_create(
            id=category['id'],
            defaults={
                'name': category['name'],
                'hidden': category['hidden'],
                'category_group_name': category['category_group_name']
            })
