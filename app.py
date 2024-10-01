import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests
import tiktoken

app = FastAPI()

# Получаем API ключи из переменных окружения
openai.api_key = os.environ.get("OPENAI_API_KEY")
newsapi_key = os.environ.get("NEWSAPI_KEY")

if not openai.api_key:
    raise ValueError("Переменная окружения OPENAI_API_KEY не установлена")
if not newsapi_key:
    raise ValueError("Переменная окружения NEWSAPI_KEY не установлена")

class Topic(BaseModel):
    topic: str

# Функция для подсчета токенов
def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# Ограничение по токенам
MAX_TOKENS = 8192
TOKENS_FOR_RESPONSE = 300  # Оставляем запас токенов для ответа (пост)
TOKENS_FOR_PROMPT = 8192 - TOKENS_FOR_RESPONSE  # Остальные токены для запроса и входных данных

def get_recent_news(topic):
    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={newsapi_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Ошибка при получении данных из NewsAPI")
    articles = response.json().get("articles", [])
    if not articles:
        return "Свежих новостей не найдено."
    
    # Ограничиваем количество заголовков, чтобы не перегрузить модель
    recent_news = [article["title"] for article in articles[:1]]  # Ограничиваем до одного заголовка
    return "\n".join(recent_news)

def generate_post(topic):
    recent_news = get_recent_news(topic)

    # Генерация заголовка
    prompt_title = f"Придумайте привлекательный заголовок для поста на тему: {topic}"
    
    # Проверка количества токенов в запросе
    if count_tokens(prompt_title) > TOKENS_FOR_PROMPT:
        raise ValueError("Слишком длинный запрос для заголовка.")

    try:
        response_title = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_title}],
            max_tokens=30,
            n=1,
            temperature=0.7,
        )
        title = response_title.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации заголовка: {str(e)}")

    # Генерация мета-описания
    prompt_meta = f"Напишите краткое, но информативное мета-описание для поста с заголовком: {title}"
    
    if count_tokens(prompt_meta) > TOKENS_FOR_PROMPT:
        raise ValueError("Слишком длинный запрос для мета-описания.")

    try:
        response_meta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_meta}],
            max_tokens=50,
            n=1,
            temperature=0.7,
        )
        meta_description = response_meta.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации мета-описания: {str(e)}")

    # Ограничиваем количество токенов для поста до 300, и уменьшаем количество новостных данных
    recent_news = get_recent_news(topic)

    # Сокращаем новостной контент, если он слишком длинный
    if count_tokens(recent_news) > TOKENS_FOR_PROMPT - 100:  # Оставляем запас для запроса
        recent_news = recent_news[:TOKENS_FOR_PROMPT - 100]

    # Генерация контента поста
    prompt_post = (
        f"Напишите подробный и увлекательный пост для блога на тему: {topic}, учитывая следующие последние новости:\n"
        f"{recent_news}\n\n"
        "Используйте короткие абзацы, подзаголовки, примеры и ключевые слова для лучшего восприятия и SEO-оптимизации."
    )
    
    # Проверка общего количества токенов (новости + запрос)
    total_tokens = count_tokens(prompt_post)
    if total_tokens > TOKENS_FOR_PROMPT:
        raise ValueError(f"Слишком длинный запрос для генерации поста. Текущие токены: {total_tokens}")

    try:
        response_post = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_post}],
            max_tokens=TOKENS_FOR_RESPONSE,  # Ограничиваем токены для текста поста
            n=1,
            temperature=0.7,
        )
        post_content = response_post.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента поста: {str(e)}")

    return {
        "title": title,
        "meta_description": meta_description,
        "post_content": post_content
    }

@app.post("/generate-post")
async def generate_post_api(topic: Topic):
    generated_post = generate_post(topic.topic)
    return generated_post

@app.get("/heartbeat")
async def heartbeat_api():
    return {"status": "OK"}

if __name__ == "__main__":
    impor
