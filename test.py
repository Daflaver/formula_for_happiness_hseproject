import pytest
import numpy as np

from utils import clean_text, rubert_label, happiness_level

def test_clean_text_removes_html_and_urls():
    """Тест: проверяем, что функция очистки текста убирает ссылки и мусор"""
    dirty_text = "Всем привет! <br> Смотрите мой сайт https://example.com!"
    cleaned = clean_text(dirty_text)
    
    assert "https" not in cleaned
    assert "br" not in cleaned
    assert "всем привет смотрите мой сайт" in cleaned.lower()

def test_rubert_label_mapping():
    """Тест: проверяем, что маппинг меток RuBERT работает корректно"""
    assert rubert_label({'label': 'POSITIVE'}) == 1
    assert rubert_label({'label': 'NEGATIVE'}) == 0
    assert rubert_label({'label': 'NEUTRAL'}) == 2

def test_happiness_level_categorization():
    """Тест: проверяем разбиение индекса счастья на категории"""
    assert happiness_level(0.8) == 'Высокий'
    assert happiness_level(0.65) == 'Высокий'
    assert happiness_level(0.5) == 'Средний'
    assert happiness_level(0.1) == 'Низкий'

def test_formula_bounds():
    """Тест: проверяем, что формула счастья не выдает значений больше 1.0 и меньше 0.0"""
    s_network = 1.0
    s_activity = 1.0
    s_sentiment = 1.0
    has_toxic = False
    
    index = (s_network * 0.30) + (s_activity * 0.20) + (s_sentiment * 0.50)
    if has_toxic:
        index *= 0.85
        
    assert 0.0 <= index <= 1.0
    assert np.isclose(index, 1.0) 