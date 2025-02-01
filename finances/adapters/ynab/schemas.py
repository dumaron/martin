from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class ExternalYnabTransaction(BaseModel):
    id: str
    date: str = Field(..., pattern="^\d{4}-\d{2}-\d{2}$")
    amount: float
    memo: Optional[str] = None
    approved: bool
    cleared: str = Field(..., pattern="^(cleared|uncleared|reconciled)$")
    flag_color: Optional[str] = Field(None, pattern="^(red|orange|yellow|green|blue|purple)$")
    flag_name: Optional[str] = None
    account_id: Optional[UUID] = None
    payee_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    transfer_account_id: Optional[UUID] = None
    transfer_transaction_id: Optional[str] = None
    matched_transaction_id: Optional[str] = None
    import_id: Optional[str] = None
    import_payee_name: Optional[str] = None
    import_payee_original: Optional[str] = None
    debt_transaction_type: Optional[str] = Field(
        None,
        pattern="^(payment|refund|fee|interest|escrow|balanceAdjustment|credit|charge)$"
    )
    deleted: bool


class YnabTransactionResponseData(BaseModel):
    transactions: List[ExternalYnabTransaction]
    server_knowledge: int = Field(..., description="Server knowledge number for delta updates")


class YnabTransactionListResponse(BaseModel):
    data: YnabTransactionResponseData = Field(..., description="YNAB /transactions response data")


class YnabTransactionCreationResponse(BaseModel):
    data: ExternalYnabTransaction = Field(..., description="YNAB /transactions/{id} response data")