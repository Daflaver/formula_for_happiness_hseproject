"""
Формула цифрового счастья — Gradio App
"""
import gradio as gr
import numpy as np
from transformers import pipeline
sentiment_pipe = pipeline(
    "sentiment-analysis",
    model="blanchefort/rubert-base-cased-sentiment",
    truncation=True,
    max_length=512
)
LABEL_RU = {
    "POSITIVE": ("Позитивный", "😊"),
    "NEGATIVE": ("Негативный", "😔"),
    "NEUTRAL": ("Нейтральный", "😐"),
}

TOXIC_KEYWORDS = ["депрессия", "грусть", "боль", "слезы", "одиночество", "апатия", "ненависть", "суицид", "смерть", "безысходность"]
EXAMPLES = [
    [
        "Сегодня отличный день! Наконец-то сдал сессию, встретился с друзьями.\nВсё как-то грустно и уныло, ничего не радует.\nЗакончил большой проект — доволен результатом, хотя устал.",
        350, 60, 15, "музыка, путешествия, спорт"
    ],
    [
        "Опять эти пробки... три часа потерял.\nВыходные прошли отлично, наконец отдохнул.\nНормально. Ни хорошо, ни плохо.",
        120, 20, 5, "новости, политика"
    ]
]


def clamp01(val):
    return float(np.clip(val, 0.0, 1.0))


def compute_happiness(posts_text, friends_num, self_posts_num, reposts_num, groups_text):
    posts = [p.strip() for p in posts_text.strip().split("\n") if len(p.strip()) > 15]
    if not posts:
        return "Введите хотя бы один пост (минимум 15 символов)", "", "", ""
    if len(posts) > 50:
        posts = posts[:50]

    results = sentiment_pipe(posts, batch_size=8)
    counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
    sentiment_lines = []

    for post, res in zip(posts, results):
        label = res["label"]
        label_ru, emoji = LABEL_RU.get(label, ("Нейтральный", "😐"))
        counts[label] += 1
        sentiment_lines.append(
            f"{emoji} [{label_ru}, уверенность: {res['score']:.2f}]\n"
            f"   {post[:120]}{'...' if len(post) > 120 else ''}"
        )

    n = len(posts)
    positive_ratio = counts["POSITIVE"] / n
    friends_norm = clamp01(friends_num / 5000.0)
    activity_norm = clamp01((self_posts_num + reposts_num) / 200.0)
    has_toxic = any(kw in groups_text.lower() for kw in TOXIC_KEYWORDS)

    raw_index = friends_norm * 0.30 + activity_norm * 0.20 + positive_ratio * 0.50
    if has_toxic:
        raw_index *= 0.85
    happiness_index = round(clamp01(raw_index), 3)

    if happiness_index >= 0.65:
        level, advice = "Высокий", "Высокий уровень цифрового благополучия. Сохраняйте позитивный настрой!"
    elif happiness_index >= 0.40:
        level, advice = "Средний", "Умеренный уровень. Есть потенциал для роста — больше общения и позитивного контента!"
    else:
        level, advice = "Низкий", "Низкий уровень по анализируемым признакам. Рекомендуется обратить внимание на эмоциональный фон."

    index_output = (
        f"Happiness Index: {happiness_index:.3f} — {level}\n\n"
        f"Компоненты:\n"
        f"S_network  (друзья):     {friends_norm:.3f} × 0.30 = {friends_norm * 0.30:.3f}\n"
        f"S_activity (активность): {activity_norm:.3f} × 0.20 = {activity_norm * 0.20:.3f}\n"
        f"S_sentiment (позитив):   {positive_ratio:.3f} × 0.50 = {positive_ratio * 0.50:.3f}\n"
        f"Токсичные группы: {'ДА (штраф ×0.85)' if has_toxic else 'нет'}\n\n"
        f"{advice}"
    )

    summary = (
        f"Проанализировано постов: {n}\n"
        f"Позитивных: {counts['POSITIVE']} ({counts['POSITIVE'] / n * 100:.1f}%)\n"
        f"Нейтральных: {counts['NEUTRAL']} ({counts['NEUTRAL'] / n * 100:.1f}%)\n"
        f"Негативных: {counts['NEGATIVE']} ({counts['NEGATIVE'] / n * 100:.1f}%)"
    )

    formula_bar = (f"Happiness Index = 0.30 × {friends_norm:.3f} + 0.20 × {activity_norm:.3f} + 0.50 × {positive_ratio:.3f}" + ("\n× 0.85 (штраф)" if has_toxic else "") + f"\n= {happiness_index:.3f}")
    return "\n\n".join(sentiment_lines), index_output, summary, formula_bar


with gr.Blocks(title="Формула цифрового счастья", theme=gr.themes.Soft()) as demo:
    with gr.Row():
        with gr.Column(scale=2):
            posts_input = gr.Textbox(
                label="Посты пользователя (каждый с новой строки, до 50 постов)",
                placeholder="Сегодня отличный день!\nВсё как-то грустно и уныло...\nЗакончил большой проект, доволен результатом.",
                lines=10
            )
            with gr.Row():
                friends_input = gr.Slider(label="Количество друзей", minimum=0, maximum=5000, value=300, step=10)
                posts_num_input = gr.Slider(label="Собственных постов", minimum=0, maximum=500, value=50, step=1)
            with gr.Row():
                reposts_input = gr.Slider(label="Репостов", minimum=0, maximum=500, value=20, step=1)
                groups_input = gr.Textbox(
                    label="Группы/интересы (через запятую)",
                    placeholder="музыка, путешествия, спорт, депрессия...",
                    lines=1
                )
            submit_btn = gr.Button("Рассчитать Happiness Index", variant="primary", size="lg")

        with gr.Column(scale=2):
            index_output = gr.Textbox(label="Индекс счастья и компоненты", lines=12, interactive=False)
            summary_output = gr.Textbox(label="Сводка по тональности", lines=5, interactive=False)
            formula_output = gr.Textbox(label="Расчёт по формуле", lines=4, interactive=False)
            sentiment_output = gr.Textbox(label="Тональность каждого поста (RuBERT)", lines=12, interactive=False)

    submit_btn.click(
        fn=compute_happiness,
        inputs=[posts_input, friends_input, posts_num_input, reposts_input, groups_input],
        outputs=[sentiment_output, index_output, summary_output, formula_output]
    )

    gr.Examples(
        examples=EXAMPLES,
        inputs=[posts_input, friends_input, posts_num_input, reposts_input, groups_input],
        label="Примеры для тестирования"
    )

    gr.Markdown("""
---
**Формула:** `Happiness_Index = 0.30 × S_network + 0.20 × S_activity + 0.50 × S_sentiment`

| Компонент | Признак | Вес |
|-----------|---------|-----|
| S_network | Кол-во друзей / 5000 | 0.30 |
| S_activity | (Посты + Репосты) / 200 | 0.20 |
| S_sentiment | Доля позитивных постов | 0.50 |

При наличии токсичных сообществ — штраф ×0.85. Модель: [blanchefort/rubert-base-cased-sentiment](https://huggingface.co/blanchefort/rubert-base-cased-sentiment)
""")

if __name__ == "__main__":
    demo.launch()
