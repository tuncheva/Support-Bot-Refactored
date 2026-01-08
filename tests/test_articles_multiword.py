# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'src')
from support_bot.services.product_catalog import file_search_products

# Test cases with articles in both words
test_queries = [
    ('електрическата сушилня', 'bg', 'Electric Dryer with article on both words'),
    ('електрическата четка', 'bg', 'Electric Toothbrush with article on both words'),
    ('електрическа сушилня', 'bg', 'Electric Dryer without article'),
    ('сушилня', 'bg', 'Just dryer'),
    ('електрическа четка за зъби', 'bg', 'Electric toothbrush multi-word'),
    ('четката за зъби', 'bg', 'Toothbrush with article'),
]

print('Testing Multi-Word Article Recognition\n' + '='*70)
for query, lang, desc in test_queries:
    results = file_search_products(query, language=lang)
    print(f'\n{desc}')
    print(f'Query: "{query}" ({lang})')
    if results:
        for i, r in enumerate(results[:2]):
            field = 'name_bg' if lang == 'bg' else 'name'
            price = r['price']
            print(f'  {i+1}. {r[field]} - ${price}')
    else:
        print('  No matches found')
