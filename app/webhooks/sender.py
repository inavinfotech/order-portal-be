import httpx
import logging
import asyncio
from typing import Any, Dict
from app.models.application import Application

logger = logging.getLogger("oms-service")

async def send_webhook(application: Application, event_type: str, data: Dict[str, Any]):
    """
    Sends a webhook to the application's callback URL.
    """
    if not application.webhook_url:
        logger.debug(f"Skipping webhook for application '{application.name}' (no URL set)")
        return

    payload = {
        "event_type": event_type,
        "application_id": application.id,
        "timestamp": data.get("timestamp"),
        "data": data
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                application.webhook_url,
                json=payload,
                headers={"X-OMS-Signature": "todo-signature-verification"} # Enhancement for future
            )
            response.raise_for_status()
            logger.info(f"Successfully sent webhook '{event_type}' to {application.webhook_url}")
    except Exception as e:
        logger.error(f"Failed to send webhook '{event_type}' to {application.webhook_url}: {e}")
