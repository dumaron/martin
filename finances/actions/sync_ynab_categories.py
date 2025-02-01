from finances.models import YnabCategory
from finances.adapters.ynab import get_categories


def sync_ynab_categories(user):
    ynab_categories = get_categories()
    for category in ynab_categories:

        if category['original_category_group_id'] is None:
            print(category)

        YnabCategory.objects.update_or_create(
            id=category['id'],
            defaults={
                'name': category['name'],
                'hidden': category['hidden'],
                'category_group_name': category['category_group_name'],
                'user': user
            })
    return
