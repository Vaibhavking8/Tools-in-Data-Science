from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
from openai import OpenAI
import json
import numpy as np
import subprocess, os, time, tempfile
from google import genai  # pip install google-genai
import yt_dlp
import mimetypes


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
openai_client = OpenAI(api_key=os.getenv("AIPIPE_TOKEN"))

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

        completion = openai_client.chat.completions.create(
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

# ------------------------------------
# Audio Processing - Timestamp Finder
# ------------------------------------

def normalize_url(url: str) -> str:
    # Redirect known YouTube URLs to a public mirror
    if "youtube.com" in url or "youtu.be" in url:
        return url.replace("youtube.com", "yewtu.be")
    return url
    
def download_audio(url: str) -> str:
    tmp_dir = tempfile.mkdtemp()
    out_path = os.path.join(tmp_dir, "audio.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_path,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # find the mp3 file
    for f in os.listdir(tmp_dir):
        if f.endswith(".mp3"):
            return os.path.join(tmp_dir, f)
    raise FileNotFoundError("Audio file not found after download")

# Initialize Gemini client (requires GOOGLE_API_KEY)
gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

class AskRequest(BaseModel):
    video_url: str
    topic: str

class AskResponse(BaseModel):
    timestamp: str  # HH:MM:SS
    video_url: str
    topic: str

@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    # Step 1: Download audio only
    tmp_dir = tempfile.mkdtemp()
    out_path = os.path.join(tmp_dir, "audio.%(ext)s")

    try:
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "-o", out_path,
            request.video_url
        ]
        video_url = normalize_url(request.video_url)
        audio_file = download_audio(video_url)
        if not audio_file:
            raise HTTPException(status_code=500, detail="Audio download failed")

        # Step 2: Upload to Gemini Files API
        file_ref = gemini_client.files.upload(path=audio_file)

        # Step 3: Poll until ACTIVE
        for _ in range(20):
            f = client.files.get(name=file_ref.name)
            if f.state == "ACTIVE":
                break
            time.sleep(2)
        else:
            raise HTTPException(status_code=500, detail="File not activated in Gemini")

        # Step 4: Ask Gemini with structured output

        result = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "file_data": {
                                "file_uri": f.uri,
                                "mime_type": "audio/mpeg"
                            }
                        },
                        {
                            "text": (
                                f"Find when the topic '{request.topic}' "
                                f"is first mentioned in this audio. "
                                f"Respond with JSON using the schema below."
                            )
                        },
                    ],
                }
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "timestamp": {
                            "type": "string",
                            "pattern": "^[0-9]{2}:[0-9]{2}:[0-9]{2}$"
                        }
                    },
                    "required": ["timestamp"],
                    "additionalProperties": False,
                },
            },
        )

        try:
            data = json.loads(result.text)
            ts = data.get("timestamp")
        except Exception:
            raise HTTPException(status_code=500, detail="Invalid JSON returned by Gemini")
        return AskResponse(timestamp=ts, video_url=request.video_url, topic=request.topic)

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"yt-dlp failed: {e.stderr.decode()}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Step 6: Clean up
        try:
            for f in os.listdir(tmp_dir):
                os.remove(os.path.join(tmp_dir, f))
            os.rmdir(tmp_dir)
        except Exception:
            pass

# ---------------------------
# Health Check
# ---------------------------
@app.get("/health")
def health():
    return {"status": "ok", "message": "Vercel FastAPI service active"}
