from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from backend.utils import fetch_article, analyze_article

load_dotenv()

app = FastAPI()

# CORS for frontend / extension testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class CheckRequest(BaseModel):
    url: str


@app.post("/check")
def check_article(payload: CheckRequest):
    # fetch_article now returns a dict with title, text and metadata
    article = fetch_article(payload.url)
    title = article.get("title", "")
    text = article.get("text", "")
    result = analyze_article(title, text, metadata=article)
    return result
