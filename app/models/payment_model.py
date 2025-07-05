from datetime import datetime


def build_payment_document(order_id, email, amount, currency, stripe_id):
    return {
        "order_id": order_id,
        "user_email": email,
        "amount": amount,
        "currency": currency,
        "stripe_payment_id": stripe_id,
        "status": "pagado",
        "timestamp": datetime.utcnow(),
    }
