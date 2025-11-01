from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from utils import fetch_article, analyze_article

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
    title, text = fetch_article(payload.url)
    result = analyze_article(title, text)
    return result
