import httpx
import logging
import asyncio
import hmac
import hashlib
import json
import time
from typing import Any, Dict
from app.models.application import Application

logger = logging.getLogger("portal_order.sender")

async def send_webhook(application: Application, event_type: str, data: Dict[str, Any]):
    """
    Sends an HMAC-signed webhook to the application's callback URL.
    """
    if not application.webhook_url:
        logger.debug(f"Skipping webhook for application '{application.name}' (no URL set)")
        return

    timestamp = int(time.time())
    payload = {
        "event_type": event_type,
        "application_id": application.id,
        "timestamp": timestamp,
        "data": data
    }

    body_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    secret_bytes = (application.api_secret or "default_webhook_secret").encode('utf-8')
    signature = hmac.new(secret_bytes, body_bytes, hashlib.sha256).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Timestamp": str(timestamp)
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                application.webhook_url,
                content=body_bytes,
                headers=headers
            )
            response.raise_for_status()
            logger.info(f"Successfully sent webhook '{event_type}' to {application.webhook_url}")
    except Exception as e:
        logger.error(f"Failed to send webhook '{event_type}' to {application.webhook_url}: {e}")
