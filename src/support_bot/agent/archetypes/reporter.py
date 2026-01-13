from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from support_bot.agent.archetypes.executor import ExecutionState
from support_bot.agent.core.models import AgentContext


_BG_MONTHS_SHORT = {
    1: "яну",
    2: "фев",
    3: "мар",
    4: "апр",
    5: "май",
    6: "юни",
    7: "юли",
    8: "авг",
    9: "сеп",
    10: "окт",
    11: "ное",
    12: "дек",
}


def _format_date_long(iso_date: str, language: str) -> str:
    """Convert YYYY-MM-DD to a localized long-ish date.

    - en: 'Jan 13, 2026'
    - bg: '13 яну 2026'

    Falls back to the input on parse error.
    """

    try:
        d = date.fromisoformat(str(iso_date))
    except Exception:
        return str(iso_date)

    if language == "bg":
        month = _BG_MONTHS_SHORT.get(d.month, str(d.month))
        return f"{d.day} {month} {d.year}"

    return d.strftime("%b %d, %Y")


def _localize_order_status(status: str, language: str) -> str:
    if language != "bg":
        return str(status)

    s = (status or "").strip().lower()
    mapping = {
        "processing": "обработва се",
        "shipped": "изпратено",
        "out for delivery": "в доставка",
        "delivered": "доставено",
        "cancelled": "отказано",
    }
    return mapping.get(s, str(status))


@dataclass
class Reporter:
    """Formats the final user-facing response."""

    def format(self, *, context: AgentContext, state: ExecutionState) -> str:
        language = context.language
        products_found = state.products_found
        order_info = state.order_info

        parts: list[str] = []

        if context.product_term:
            if products_found:
                name_field = "name_bg" if language == "bg" else "name"
                desc_field = "description_bg" if language == "bg" else "description"
                price_label = "Цена:" if language == "bg" else "Price:"

                yes_text = "Да!" if language == "bg" else "Yes!"

                # Show ALL matches immediately (no follow-up prompt).
                lines: list[str] = []
                for p in products_found:
                    if not isinstance(p, dict):
                        continue
                    lines.append(
                        f"{yes_text} {p.get(name_field,'')} — {p.get(desc_field,'')} {price_label} ${p.get('price')}"
                    )

                parts.extend(lines)

            else:
                no_match_text = (
                    f"Не са намерени продукти, отговарящи на '{context.product_term}'."
                    if language == "bg"
                    else f"No products found matching '{context.product_term}'."
                )
                parts.append(no_match_text)

        if order_info:
            status_label = "е със статус" if language == "bg" else "is currently"
            localized_status = _localize_order_status(str(order_info.get("status") or ""), language)
            parts.append(
                (
                    f"Поръчка {order_info.get('order_id')} {status_label} {localized_status}."
                    if language == "bg"
                    else f"Order {order_info.get('order_id')} is currently {localized_status}."
                )
            )
            if order_info.get("estimated_delivery"):
                est_text = "Очаквана доставка:" if language == "bg" else "Estimated delivery:"
                formatted = _format_date_long(str(order_info.get("estimated_delivery")), language)
                parts.append(f"{est_text} {formatted}")

        if not parts:
            sorry_text = (
                "Съжалявам — не могах да намеря информация за продукт или поръчка във вашия въпрос."
                if language == "bg"
                else "Sorry — I couldn't find product or order information in your question."
            )
            parts.append(sorry_text)

        return " ".join(parts).strip()
