from pydantic import BaseModel


class ConfirmPaymentDTO(BaseModel):
    order_id: str
