"""Support Bot package.

Public API:
- [`handle_user_query()`](src/support_bot/chat/handler.py:43)
- [`create_thread_and_ask()`](src/support_bot/chat/handler.py:111)
"""

from .chat.handler import create_thread_and_ask, handle_user_query

__all__ = [
    "handle_user_query",
    "create_thread_and_ask",
]
