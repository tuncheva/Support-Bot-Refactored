from __future__ import annotations

from support_bot.chat.handler import handle_user_query


def test_multi_tool_query_calls_both_tools():
    reply, dbg = handle_user_query("What's the price of the 'Pro' model, and what's the status of order #12345?", debug=True)

    assert isinstance(reply, str)
    assert "tools_called" in dbg
    assert "trace" in dbg

    names = [t["name"] for t in dbg["tools_called"]]
    assert "file_search_products" in names
    assert "getOrderStatus" in names


def test_product_search_en():
    reply, dbg = handle_user_query("Do you have smart watch?", debug=True)
    assert "file_search_products" in [t["name"] for t in dbg["tools_called"]]
    assert "Price:" in reply
    assert reply.startswith("Yes!")


def test_order_status_only_does_not_trigger_product_no_match():
    reply, dbg = handle_user_query("What’s the status of order #12345?", debug=True)
    assert "getOrderStatus" in [t["name"] for t in dbg["tools_called"]]
    assert "No products found" not in reply


def test_bulgarian_order_status():
    reply, dbg = handle_user_query("Статус на поръчка #12345", debug=True)
    assert "getOrderStatus" in [t["name"] for t in dbg["tools_called"]]
    assert "Поръчка" in reply
