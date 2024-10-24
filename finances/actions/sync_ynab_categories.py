from finances.models import YnabCategory
from finances.adapters.ynab import YnabAdapter


def sync_ynab_categories():
    ynab_categories = YnabAdapter.get_categories()
    pass
