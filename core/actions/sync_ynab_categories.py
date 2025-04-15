from core.models import YnabCategory
from core.integrations.ynab import get_categories


def sync_ynab_categories(budget_id) -> None :
    ynab_categories = get_categories(budget_id)

    for category in ynab_categories:
        YnabCategory.objects.update_or_create(
            id=category['id'],
            defaults={
                'name': category['name'],
                'hidden': category['hidden'],
                'category_group_name': category['category_group_name']
            })
