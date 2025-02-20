from finances.models import (
    BankFileImport,
    BankExpense,
    YnabImport,
    YnabTransaction,
    YnabCategory
)

def test_models_import():
    """Test that all models can be imported from the new location"""
    assert BankFileImport is not None
    assert BankExpense is not None
    assert YnabImport is not None
    assert YnabTransaction is not None
    assert YnabCategory is not None