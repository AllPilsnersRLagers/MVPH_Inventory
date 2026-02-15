"""Stock alert notification utilities."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypedDict

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpRequest
from django.template.loader import render_to_string

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    from .models import InventoryItem

logger = logging.getLogger(__name__)


class StockAlert(TypedDict):
    """Structure for a stock alert notification."""

    item_id: str
    item_name: str
    old_status: str
    new_status: str
    quantity: str
    reorder_point: str
    unit: str
    timestamp: str


SESSION_KEY = "stock_alerts"


def queue_stock_alert(
    request: HttpRequest,
    item: InventoryItem,
    old_status: str,
    new_status: str,
) -> None:
    """Queue a stock alert notification in the session.

    Only queues if transitioning TO 'low' or 'reorder' status from 'ok'.
    Does not queue if already in a critical status.
    """
    # Only notify on transitions TO critical states
    if new_status not in ("low", "reorder"):
        return

    # Don't notify if already in a critical state
    if old_status in ("low", "reorder"):
        return

    alerts: list[StockAlert] = request.session.get(SESSION_KEY, [])

    alert: StockAlert = {
        "item_id": str(item.pk),
        "item_name": item.name,
        "old_status": old_status,
        "new_status": new_status,
        "quantity": str(item.quantity_on_hand),
        "reorder_point": str(item.reorder_point),
        "unit": item.get_unit_of_measure_display(),
        "timestamp": datetime.now().isoformat(),
    }

    alerts.append(alert)
    request.session[SESSION_KEY] = alerts
    request.session.modified = True


def get_pending_alerts(request: HttpRequest) -> list[StockAlert]:
    """Retrieve all pending stock alerts from the session."""
    alerts: list[StockAlert] = request.session.get(SESSION_KEY, [])
    return alerts


def clear_pending_alerts(request: HttpRequest) -> None:
    """Clear all pending stock alerts from the session."""
    if SESSION_KEY in request.session:
        del request.session[SESSION_KEY]
        request.session.modified = True


def send_stock_alert_email(user: AbstractUser, alerts: list[StockAlert]) -> bool:
    """Send a batched stock alert email to the user.

    Returns True if email was sent, False otherwise.
    """
    if not alerts:
        return False

    if not user.email:
        return False

    # Separate into reorder (critical) and low (warning)
    reorder_alerts = [a for a in alerts if a["new_status"] == "reorder"]
    low_alerts = [a for a in alerts if a["new_status"] == "low"]

    context = {
        "user": user,
        "reorder_alerts": reorder_alerts,
        "low_alerts": low_alerts,
        "total_count": len(alerts),
    }

    subject = f"[MVPH Inventory] {len(alerts)} item(s) need attention"

    # Render both plain text and HTML versions
    text_body = render_to_string("inventory/emails/stock_alert.txt", context)
    html_body = render_to_string("inventory/emails/stock_alert.html", context)

    send_mail(
        subject=subject,
        message=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_body,
        fail_silently=False,
    )

    return True
