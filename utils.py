import re

def clean_text(text: str) -> str:
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[^а-яёА-ЯЁa-zA-Z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()
    
def rubert_label(r: dict) -> int:
    if r['label'] == 'POSITIVE': return 1
    elif r['label'] == 'NEGATIVE': return 0
    else: return 2

def happiness_level(idx: float) -> str:
    if idx >= 0.65: return 'Высокий'
    elif idx >= 0.40: return 'Средний'
    else: return 'Низкий'