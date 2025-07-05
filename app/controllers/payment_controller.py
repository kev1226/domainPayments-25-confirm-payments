from fastapi import APIRouter, Header, HTTPException
from app.dto import ConfirmPaymentDTO
from app.utils.jwt_utils import decode_token
from app.services.payment_service import confirm_payment_logic, finalize_payment_logic

payment_router = APIRouter()


@payment_router.post("/confirm-payment")
def confirm_payment(dto: ConfirmPaymentDTO, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Formato Bearer inválido")
    token = authorization.replace("Bearer ", "")
    user = decode_token(token)
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=403, detail="Email no encontrado en token")
    return confirm_payment_logic(dto.order_id, token, email)


@payment_router.post("/finalize-payment")
def finalize_payment(dto: ConfirmPaymentDTO, authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Formato Bearer inválido")
    token = authorization.replace("Bearer ", "")
    user = decode_token(token)
    email = user.get("email")
    if not email:
        raise HTTPException(status_code=403, detail="Email no encontrado en token")
    return finalize_payment_logic(dto.order_id, token, email)
