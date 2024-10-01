# app.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import httpx  # Асинхронная библиотека для HTTP-запросов

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

# Асинхронная функция для получения новостей
async def get_recent_news(topic):
    url = f"https://newsapi.org/v2/everything?q={topic}&apiKey={newsapi_key}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=500, detail=f"Ошибка при получении данных из NewsAPI: {exc}")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=f"Ошибка сети при обращении к NewsAPI: {exc}")
    
    articles = response.json().get("articles", [])
    if not articles:
        return "Свежих новостей не найдено."
    recent_news = [article["title"] for article in articles[:1]]  # Берем только 1 статью
    return "\n".join(recent_news)

# Синхронная функция для генерации заголовка, мета-описания и контента
def generate_post(topic):
    recent_news = get_recent_news(topic)  # Вызов новостей остаётся асинхронным

    # Генерация заголовка
    prompt_title = f"Придумайте привлекательный заголовок для поста на тему: {topic}"
    try:
        response_title = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_title}],
            max_tokens=15,
            n=1,
            temperature=0.7,
        )
        title = response_title.choices[0].message['content'].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации заголовка: {str(e)}")

    # Генерация мета-описания
    prompt_meta = f"Напишите краткое, но информативное мета-описание для поста с заголовком: {title}"
    try:
        response_meta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_meta}],
            max_tokens=30,
            n=1,
            temperature=0.7,
        )
        meta_description = response_meta.choices[0].message['content'].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации мета-описания: {str(e)}")

    # Генерация контента поста
    prompt_post = (
        f"Напишите подробный и увлекательный пост для блога на тему: {topic}, учитывая следующие последние новости:\n"
        f"{recent_news}\n\n"
        "Используйте короткие абзацы, подзаголовки, примеры и ключевые слова для лучшего восприятия и SEO-оптимизации."
    )
    try:
        response_post = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_post}],
            max_tokens=300,
            n=1,
            temperature=0.7,
        )
        post_content = response_post.choices[0].message['content'].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента поста: {str(e)}")

    return {
        "title": title,
        "meta_description": meta_description,
        "post_content": post_content
    }

@app.post("/generate-post")
async def generate_post_api(topic: Topic):
    # Поскольку OpenAI методы синхронные, мы вызываем синхронную функцию через `run_in_threadpool`
    from starlette.concurrency import run_in_threadpool
    generated_post = await run_in_threadpool(generate_post, topic.topic)
    return generated_post

@app.get("/heartbeat")
async def heartbeat_api():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)
