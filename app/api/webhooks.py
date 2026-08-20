from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.order import Order
from app.webhooks.sender import send_webhook
import json

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/payment")
async def handle_payment_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Receives payment events from portal-payment (CPP) and updates matching orders.
    """
    body_bytes = await request.body()
    try:
        data = json.loads(body_bytes)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = data.get("event")
    payload = data.get("data", {})
    razorpay_order_id = payload.get("razorpay_order_id")
    razorpay_payment_id = payload.get("razorpay_payment_id")

    if event == "payment.success":
        # Match order by payment_order_id or payment_id
        query = db.query(Order)
        filters = []
        if razorpay_order_id:
            filters.append(Order.payment_order_id == razorpay_order_id)
        if razorpay_payment_id:
            filters.append(Order.payment_id == razorpay_payment_id)
            
        if filters:
            orders = query.filter(*filters).all()
            for order in orders:
                if order.payment_status != "paid":
                    order.payment_status = "paid"
                    order.status = "confirmed"
                    db.commit()
                    db.refresh(order)

                    if order.application:
                        background_tasks.add_task(
                            send_webhook,
                            order.application,
                            "order.paid",
                            {
                                "order_id": order.id,
                                "status": order.status,
                                "payment_status": order.payment_status,
                                "total_amount": order.total_amount
                            }
                        )

    return {"status": "processed"}
