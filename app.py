import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import requests

app = FastAPI()

# Убедитесь, что переменная среды OPENAI_API_KEY установлена
openai.api_key = os.environ.get("OPENAI_API_KEY")
if openai.api_key is None:
    raise ValueError("Необходимо установить переменную среды OPENAI_API_KEY")

class Topic(BaseModel):
    topic: str

def get_recent_news(topic):
    # Заглушка для функции получения последних новостей
    # В реальном применении здесь должен быть код для получения новостей по API
    return f"Последние новости на тему {topic}: ..."

def generate_post(topic):
    recent_news = get_recent_news(topic)
    try:
        prompt_title = f"Придумайте привлекательный заголовок для поста на тему: {topic}"
        response_title = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_title}],
            max_tokens=50,
            n=1,
            temperature=0.7,
        )
        title = response_title['choices'][0]['message']['content'].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации заголовка: {e}")

    try:
        prompt_meta = f"Напишите краткое, но информативное мета-описание для поста с заголовком: {title}"
        response_meta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_meta}],
            max_tokens=100,
            n=1,
            temperature=0.7,
        )
        meta_description = response_meta['choices'][0]['message']['content'].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации мета-описания: {e}")

    try:
        prompt_post = (
            f"Напишите подробный и увлекательный пост для блога на тему: {topic}, "
            f"учитывая следующие последние новости:\n{recent_news}\n\n"
            "Используйте короткие абзацы, подзаголовки, примеры и ключевые слова "
            "для лучшего восприятия и SEO-оптимизации."
        )
        response_post = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt_post}],
            max_tokens=2048,
            n=1,
            temperature=0.7,
        )
        post_content = response_post['choices'][0]['message']['content'].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации контента поста: {e}")

    return {
        "title": title,
        "meta_description": meta_description,
        "post_content": post_content
    }

@app.post("/generate-post")
async def generate_post_api(topic: Topic):
    return generate_post(topic.topic)

@app.get("/heartbeat")
async def heartbeat_api():
    return {"status": "OK"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
