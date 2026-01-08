# Loads the product catalog from JSON and performs rule-based keyword search with scoring
# bg normalization 

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from support_bot.config import products_path


@dataclass(frozen=True)
class ProductCatalog:
    products: list[dict[str, Any]]

    @classmethod
    def load(cls, path: Path | None = None) -> "ProductCatalog":
        p = path or products_path()
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                data = []
        except Exception:
            data = []
        return cls(products=data)

    def _normalize_bulgarian(self, word: str) -> str:
        """Remove Bulgarian articles and case endings for matching.
        
        Handles definite articles: та (the-fem), то (the-neut), ят (the-pl), ът (the-masc)
        Also removes common adjective endings: ски, ска, на, ен, а
        """
        word = word.lower()
        original_len = len(word)
        
        article_endings = [
            'ята',
            'ято',
            'ятo',
            'та',
            'то',
            'ят',
            'ът',
            'ьт',
        ]
        
        # Try each article ending, removing only one
        for ending in article_endings:
            if word.endswith(ending) and len(word) > len(ending) + 2:
                return word[:-len(ending)]
        # if no article is found, try removing descriptor endings
        descriptor_endings = ['ската', 'ски', 'ска', 'на', 'ен', 'ни', 'а']
        for ending in sorted(descriptor_endings, key=len, reverse=True):
            if word.endswith(ending) and len(word) > len(ending) + 3:
                return word[:-len(ending)]
        
        return word

    def search(self, keyword: str, language: str = "en") -> list[dict[str, Any]]:
        
        if not keyword:
            return []
        
        name_field = "name_bg" if language == "bg" else "name"
        desc_field = "description_bg" if language == "bg" else "description"
        
        keywords = keyword.split()
        
        # Normalize keywords (especially for Bulgarian morphology)
        if language == "bg":
            normalized_keywords = [self._normalize_bulgarian(kw) for kw in keywords]
        else:
            normalized_keywords = [kw.lower() for kw in keywords]
        
        results_with_scores: list[tuple[dict[str, Any], int]] = []
        
        for p in self.products:
            name_text = str(p.get(name_field, "")).lower()
            desc_text = str(p.get(desc_field, "")).lower()
            category_text = str(p.get("category", "")).lower()
            full_text = f"{name_text} {desc_text} {category_text}"
            
            if language == "bg":
                name_words = re.findall(r'[\u0400-\u04FF]+', name_text)
                desc_words = re.findall(r'[\u0400-\u04FF]+', desc_text)
                
                normalized_name_words = [self._normalize_bulgarian(w) for w in name_words]
                normalized_desc_words = [self._normalize_bulgarian(w) for w in desc_words]
                
                normalized_product_text = " ".join(normalized_name_words + normalized_desc_words)
                normalized_product_text += " " + full_text
            else:
                normalized_product_text = full_text
            
            match_count = 0
            for i, norm_kw in enumerate(normalized_keywords):
                if norm_kw in normalized_product_text:
                    match_count += 1
                elif keywords[i].lower() in full_text:
                    match_count += 1
            
            if match_count > 0:
                bonus = 0
                for orig_kw in keywords:
                    if orig_kw.lower() in full_text:
                        bonus += 2
                
                # Extra boost if product name contains the keywords (prioritize name over description)
                if language == "bg":
                    name_match_boost = sum(1 for nkw in normalized_keywords if nkw in " ".join(normalized_name_words))
                    bonus += name_match_boost * 3
                else:
                    name_match_boost = sum(1 for kw in keywords if kw.lower() in name_text)
                    bonus += name_match_boost * 3
                
                results_with_scores.append((p, match_count + bonus))
        
        results_with_scores.sort(key=lambda x: x[1], reverse=True)
        results = [p for p, _ in results_with_scores]
        return results


_DEFAULT_CATALOG = ProductCatalog.load()


def file_search_products(keyword: str, language: str = "en") -> list[dict[str, Any]]:
    """Backwards-compatible function wrapper that supports language parameter."""

    return _DEFAULT_CATALOG.search(keyword, language)
