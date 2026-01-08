"""Chat handler: parse a user message and call services."""

from __future__ import annotations

import re
from typing import Any

from support_bot.services.order_status import getOrderStatus
from support_bot.services.product_catalog import file_search_products


def handle_user_query(user_input: str, debug: bool = False):
    """Handle a simple user query by using the product-search and order-status tools.

    If `debug` is True, also return a dict describing which tools were called and
    with what arguments.
    Automatically detects Bulgarian language in the input.
    """

    tools_called: list[dict[str, Any]] = []
    text = (user_input or "").strip()
    
    is_bulgarian = bool(re.search(r'[\u0400-\u04FF]', text))
    language = "bg" if is_bulgarian else "en"

    is_order_query = bool(re.search(r'\b(?:order|status|поръчка|статус)\b', text, re.IGNORECASE))
    
    order_match = re.search(r"#?([0-9]{3,})", text)
    order_info = None
    if order_match:
        oid = order_match.group(1)
        order_info = getOrderStatus(oid)
        tools_called.append({"tool": "getOrderStatus", "args": [oid]})

    prod_term = None
    if not is_order_query:
        qmatch = re.search(
            r"(?:(?<=\s)|(?<=^))'([^']+?)'(?=(?:\s|[.,?!]|$))|\"([^\"]+?)\"", text
        )
        if qmatch:
            prod_term = qmatch.group(1) or qmatch.group(2)
        else:
            patterns = [
                (r"(?:sell|have|price\s+of|about|get|want)\s+(?:a\s+)?(?:an\s+)?(?:the\s+)?(.+?)(?:[?!.,]|$)", "en"),
                (r"(?:търся|цена\s+на)\s+(.+?)(?:[?!.,]|$)", "bg"),
                (r"(?:имате|имат|имаш)\s+(?:ли\s+)?(.+?)(?:[?!.,]|$)", "bg"),
            ]
            
            for pattern, lang in patterns:
                if language == lang or lang is None:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        phrase = match.group(1).strip() if match.lastindex else match.group(0)
                        prod_term = phrase
                        break
            
            if not prod_term:
                common_words = {"do", "you", "sell", "have", "what", "can", "is", "it", "the", "a", "an", "or", "and", "price", "of", "for", "with", "in", "on", "at", "to", "that", "this", "about", "does", "need", "get", "want",
                              "да", "вие", "продавате", "имате", "имаш", "ли", "какво", "е", "цена", "на", "какъв", "има", "по", "един", "в", "с", "от", "за", "то", "търся", "той", "тя", "то", "трябва", "можеш", "мога", "можете"}
                if is_bulgarian:
                    words = re.findall(r"[\u0400-\u04FF]{3,}", text, re.IGNORECASE)
                else:
                    words = re.findall(r"\b[a-z]{3,}\b", text.lower())
                
                product_words = [w for w in set(words) if w.lower() not in common_words]
                if product_words:
                    prod_term = min(product_words, key=lambda w: len(w))
            
            if prod_term and language == 'en' and prod_term.endswith('s'):
                singular = prod_term[:-1]
                if len(singular) >= 3:
                    prod_term = singular

    products_found = []
    if prod_term:
        products_found = file_search_products(prod_term, language=language)
        tools_called.append({"tool": "file_search_products", "args": [prod_term, language]})
        
        if not products_found and ' ' in prod_term:
            words = prod_term.split()
            for search_word in [words[-1]] + words[:-1]:
                products_found = file_search_products(search_word, language=language)
                if products_found:
                    break

    parts: list[str] = []
    
    if not is_order_query:
        if products_found:
            p = products_found[0]
            name_field = 'name_bg' if language == 'bg' else 'name'
            desc_field = 'description_bg' if language == 'bg' else 'description'
            price_label = "Цена:" if language == 'bg' else "Price:"
            parts.append(f"{p[name_field]} — {p.get(desc_field,'')} {price_label} ${p['price']}")
            if len(products_found) > 1:
                matches_text = "още съвпадения намерени." if language == 'bg' else "more matches found."
                parts.append(f"({len(products_found)-1} {matches_text})")
        elif prod_term:
            no_match_text = f"Не са намерени продукти, отговарящи на '{prod_term}'." if language == 'bg' else f"No products found matching '{prod_term}'."
            parts.append(no_match_text)

    if order_info:
        status_text = "статус" if language == 'bg' else "is currently"
        parts.append(f"Поръчка {order_info['order_id']} {status_text} {order_info['status']}." if language == 'bg' else f"Order {order_info['order_id']} is currently {order_info['status']}.")
        if order_info.get("estimated_delivery"):
            est_text = "Очаквана доставка:" if language == 'bg' else "Estimated delivery:"
            parts.append(f"{est_text} {order_info['estimated_delivery']}")

    if not parts:
        sorry_text = "Съжалявам — не могах да намеря информация за продукт или поръчка във вашия въпрос." if language == 'bg' else "Sorry — I couldn't find product or order information in your question."
        parts.append(sorry_text)

    response = " ".join(parts)
    if debug:
        return response, {"tools_called": tools_called}
    return response


def create_thread_and_ask(question: str):
    """Simulate creating a thread and asking the assistant; returns response and debug info."""

    return handle_user_query(question, debug=True)
