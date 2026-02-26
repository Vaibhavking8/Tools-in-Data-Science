from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
from openai import OpenAI
import json
import numpy as np
import os

# ---------------------------
# Vercel-compatible FastAPI app
# ---------------------------
app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ---------------------------
# Load telemetry data 
# ---------------------------
try:
    with open("q-vercel-latency.json", "r", encoding="utf-8") as f:
        telemetry = json.load(f)
except FileNotFoundError:
    telemetry = []

@app.post("/")
async def latency_metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    results = {}
    for region in regions:
        region_data = [r for r in telemetry if r["region"] == region]
        if not region_data:
            continue

        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_pct"] for r in region_data]

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = sum(1 for l in latencies if l > threshold)

        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": breaches
        }

    return {"regions": results}

# ---------------------------
# Sentiment API (added)
# ---------------------------

class CommentRequest(BaseModel):
    comment: str

class SentimentResponse(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
    rating: int  # Must be 1–5

# Configure AIPipe base URL and token
os.environ["OPENAI_BASE_URL"] = "https://aipipe.org/openai/v1/"
client = OpenAI(api_key=os.getenv("AIPIPE_TOKEN"))

@app.post("/comment", response_model=SentimentResponse)
async def analyze_comment(request: CommentRequest):
    try:
        response_schema = {
            "name": "sentiment_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "sentiment": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral"]
                    },
                    "rating": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5
                    }
                },
                "required": ["sentiment", "rating"],
                "additionalProperties": False
            }
        }

        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a sentiment analysis model."},
                {"role": "user", "content": f"Analyze this comment:\n\n{request.comment}"}
            ],
            response_format={"type": "json_schema", "json_schema": response_schema},
            temperature=0.1
        )

        json_content = completion.choices[0].message.content
        result = SentimentResponse.model_validate_json(json_content)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

# ---------------------------
# Health Check
# ---------------------------
@app.get("/health")
def health():
    return {"status": "ok", "message": "Vercel FastAPI service active"}
