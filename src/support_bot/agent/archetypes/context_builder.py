from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from support_bot.agent.core.models import AgentContext, AgentInput
from support_bot.agent.governance.memory_manager import MemoryManager


@dataclass
class ContextBuilder:
    memory: MemoryManager

    def build(self, agent_input: AgentInput) -> AgentContext:
        text = (agent_input.user_text or "").strip()

        is_bulgarian = bool(re.search(r"[\u0400-\u04FF]", text))
        language = "bg" if is_bulgarian else "en"

        order_id = self._extract_order_id(text)
        product_term = self._extract_product_term(text=text, language=language, is_bulgarian=is_bulgarian)

        memory_ctx = self.memory.get_context(agent_input.session_id)

        return AgentContext(
            language=language,  # type: ignore[arg-type]
            normalized_text=text,
            order_id=order_id,
            product_term=product_term,
            memory=memory_ctx,
        )

    @staticmethod
    def _extract_order_id(text: str) -> str | None:
        order_match = re.search(r"#?([0-9]{3,})", text)
        if not order_match:
            return None
        return order_match.group(1)

    @staticmethod
    def _extract_product_term(*, text: str, language: str, is_bulgarian: bool) -> str | None:
        # Important: allow multi-tool queries like:
        # "What's the price of the 'Pro' model and status of order #123?"
        # So we do NOT early-exit on order keywords.
        #
        # But we DO avoid false positives where the extracted term is literally "order"
        # or "status" (these are order-intent tokens, not product terms).

        qmatch = re.search(r"(?:(?<=\s)|(?<=^))'([^']+?)'(?=(?:\s|[.,?!]|$))|\"([^\"]+?)\"", text)
        if qmatch:
            candidate = (qmatch.group(1) or qmatch.group(2) or "").strip()
            return candidate or None

        patterns: list[tuple[str, str]] = [
            (r"(?:sell|have|price\s+of|about|get|want)\s+(?:a\s+)?(?:an\s+)?(?:the\s+)?(.+?)(?:[?!.,]|$)", "en"),
            (r"(?:търся|цена\s+на)\s+(.+?)(?:[?!.,]|$)", "bg"),
            (r"(?:имате|имат|имаш)\s+(?:ли\s+)?(.+?)(?:[?!.,]|$)", "bg"),
        ]

        prod_term: str | None = None
        for pattern, lang in patterns:
            if language != lang:
                continue
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phrase = match.group(1).strip() if match.lastindex else match.group(0)
                prod_term = phrase
                break

        if not prod_term:
            common_words = {
                "do",
                "you",
                "sell",
                "have",
                "what",
                "can",
                "is",
                "it",
                "the",
                "a",
                "an",
                "or",
                "and",
                "price",
                "of",
                "for",
                "with",
                "in",
                "on",
                "at",
                "to",
                "that",
                "this",
                "about",
                "does",
                "need",
                "get",
                "want",
                "да",
                "вие",
                "продавате",
                "имате",
                "имаш",
                "ли",
                "какво",
                "е",
                "цена",
                "на",
                "какъв",
                "има",
                "по",
                "един",
                "в",
                "с",
                "от",
                "за",
                "то",
                "търся",
                "той",
                "тя",
                "трябва",
                "можеш",
                "мога",
                "можете",
            }

            if is_bulgarian:
                words = re.findall(r"[\u0400-\u04FF]{3,}", text, re.IGNORECASE)
            else:
                words = re.findall(r"\b[a-z]{3,}\b", text.lower())

            product_words = [w for w in set(words) if w.lower() not in common_words]
            if product_words:
                prod_term = min(product_words, key=lambda w: len(w))

        if prod_term:
            lowered = prod_term.strip().lower()
            if lowered in {"order", "status", "поръчка", "статус"}:
                return None

        if prod_term and language == "en" and prod_term.endswith("s"):
            singular = prod_term[:-1]
            if len(singular) >= 3:
                prod_term = singular

        return prod_term
