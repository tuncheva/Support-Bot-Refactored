# mock order status service.

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any


def getOrderStatus(order_id: str) -> dict[str, Any]:

    oid = re.sub(r"[^0-9]", "", str(order_id)) or "0"
    n = int(oid) if oid.isdigit() else 0

    statuses = ["Processing", "Shipped", "Out for delivery", "Delivered", "Cancelled"]
    status = statuses[n % len(statuses)]

    today = datetime.utcnow().date()
    if status == "Processing":
        est = today + timedelta(days=3)
    elif status == "Shipped":
        est = today + timedelta(days=2)
    elif status == "Out for delivery":
        est = today + timedelta(days=1)
    elif status == "Delivered":
        est = today - timedelta(days=1)
    else:
        est = None

    mock_items = [
        {"id": "P1001", "name": "SmartWatch Pro", "qty": 1},
    ]

    return {
        "order_id": str(order_id),
        "status": status,
        "estimated_delivery": est.isoformat() if est else None,
        "tracking_id": f"TRK{n:06d}",
        "items": mock_items,
    }
