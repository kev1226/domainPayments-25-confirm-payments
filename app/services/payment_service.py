import stripe
import requests
from fastapi import HTTPException
from bson import ObjectId
from app.database import payments, client
from app.models.payment_model import build_payment_document
from app.config import (
    STRIPE_SECRET_KEY,
    UPDATE_ORDER_STATUS_URL,
    DECREASE_STOCK_URL,
    RESTORE_STOCK_URL,
    CHECK_STOCK_URL,
)

stripe.api_key = STRIPE_SECRET_KEY
orders = client["orders_db"]["orders"]


def confirm_payment_logic(order_id: str, token: str, email: str):
    order = orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if order["status"] == "CANCELADA":
        raise HTTPException(
            status_code=400, detail="No se puede pagar una orden cancelada"
        )
    if order["user"]["email"] != email:
        raise HTTPException(status_code=403, detail="No autorizado")
    if order["status"] != "PENDIENTE_DE_PAGO":
        raise HTTPException(status_code=400, detail="Orden ya pagada o inválida")

    # ✅ Preparar payload para verificar stock
    stock_items = [
        {"productId": int(p["product_id"]), "quantity": p["quantity"]}
        for p in order.get("products", [])
    ]

    try:
        res = requests.post(CHECK_STOCK_URL, json={"items": stock_items}, timeout=5)
        if res.status_code != 200:
            raise HTTPException(
                status_code=400, detail="❌ Stock insuficiente para completar el pago"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al verificar stock: {str(e)}"
        )

    # ✅ Solo si el stock es suficiente, se crea el PaymentIntent
    amount = order["total"]["amount"]
    currency = order["total"]["currency"]

    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency,
            payment_method_types=["card"],
            description=f"Pago para orden {order_id}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Stripe: {str(e)}")

    stripe_id = payment_intent.id

    payment_doc = build_payment_document(order_id, email, amount, currency, stripe_id)
    payment_doc["status"] = "pendiente"
    payments.insert_one(payment_doc)

    return {
        "message": "Intento de pago creado",
        "payment_id": stripe_id,
        "order_id": order_id,
        "status": "pendiente",
        "client_secret": payment_intent.client_secret,
    }


def finalize_payment_logic(order_id: str, token: str, email: str):
    payment = payments.find_one(
        {"order_id": order_id, "user_email": email}, sort=[("timestamp", -1)]
    )
    if not payment:
        raise HTTPException(status_code=404, detail="❌ Pago no encontrado")

    # 1. Obtener la orden
    order = orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        raise HTTPException(status_code=404, detail="❌ Orden no encontrada")

    # 2. Preparar payload para stock
    stock_items = [
        {"productId": int(p["product_id"]), "quantity": p["quantity"]}
        for p in order.get("products", [])
    ]

    # 3. Descontar stock primero
    try:
        res = requests.post(DECREASE_STOCK_URL, json={"items": stock_items}, timeout=5)
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail="❌ Error al descontar stock")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al contactar decrease-stock: {str(e)}"
        )

    # 4. Verificar con Stripe
    try:
        pi = stripe.PaymentIntent.retrieve(payment["stripe_payment_id"])
        if pi.status != "succeeded":
            # 🔁 Si el pago no fue exitoso, revertimos el stock
            requests.post(RESTORE_STOCK_URL, json={"items": stock_items})
            raise HTTPException(
                status_code=400, detail="⚠️ El pago no se completó, se restauró el stock"
            )

        # 5. Actualizar estado del pago
        payments.update_one(
            {"_id": payment["_id"]}, {"$set": {"status": "pagado_confirmado"}}
        )

        # 6. Actualizar orden vía GraphQL
        mutation = f'mutation {{ updateOrderStatus(id: "{order_id}") {{ id status }} }}'
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            UPDATE_ORDER_STATUS_URL,
            headers=headers,
            json={"query": mutation},
            timeout=5,
        )

        if response.status_code != 200 or "errors" in response.json():
            raise HTTPException(status_code=500, detail="❌ Error al actualizar orden")

        return {"message": "✅ Pago exitoso, stock descontado y orden actualizada"}

    except Exception as e:
        # 🔁 Revertir stock si hay fallo en cualquier parte
        requests.post(RESTORE_STOCK_URL, json={"items": stock_items})
        raise HTTPException(
            status_code=500, detail=f"❌ Error durante el flujo de pago: {str(e)}"
        )
