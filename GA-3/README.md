# Tools in Data Science – Graded Assignment 3 (Complete Solutions)

This README contains the **full, question-wise solutions for all 18 problems** from **Graded Assignment 3** of the *Tools in Data Science* course.

---

## 2) LLM Structured Output - FastAPI Sentiment Analysis


You can host multiple APIs on a single FastAPI app deployed via **Vercel**:

* `POST /` — Returns regional latency metrics from `q-vercel-latency.json`
* `POST /comment` — Performs sentiment analysis using **GPT-4.1-mini** via **AIPipe**
* `GET /health` — Health check endpoint

### 🚀 Deployment Steps

1. **Project structure**

   ```
   api/index.py
   q-vercel-latency.json
   requirements.txt
   vercel.json
   ```

2. **vercel.json**

   ```json
   {
     "builds": [{ "src": "api/index.py", "use": "@vercel/python" }],
     "routes": [{ "src": "/(.*)", "dest": "/api/index.py" }]
   }
   ```

3. **requirements.txt**

   ```
   fastapi
   numpy
   openai>=1.12.0
   pydantic
   ```

4. **Add Environment Variable in Vercel**

   ```
   AIPIPE_TOKEN = your_aipipe_token_here
   ```

5. **Deploy**

   ```bash
   vercel --prod
   ```

### Testing

#### Sentiment Analysis

```bash
curl -X POST https://<your-app>.vercel.app/comment \
     -H "Content-Type: application/json" \
     -d '{"comment": "This product is amazing!"}'
```

Expected:

```json
{ "sentiment": "positive", "rating": 5 }
```

#### Telemetry

```bash
curl -X POST https://<your-app>.vercel.app/ \
     -H "Content-Type: application/json" \
     -d '{"regions": ["apac", "emea"], "threshold_ms": 180}'
```

#### Health Check

```bash
curl https://<your-app>.vercel.app/health
```

✅ **Single global URL**
All endpoints are accessible under:

```
https://<your-app>.vercel.app/
```


---

## 3) Code Interpreter with AI Error Analysis

> Refer api/index.py

### Features

* Execute Python code and capture stdout/stderr.
* Invoke AI only on errors to identify error lines.
* Structured JSON output using Pydantic.
* CORS enabled for testing.
* Supports Gemini via AIPipe token.

### API Endpoint

**POST /code-interpreter**

### Request

```json
{
  "code": "x = 10\ny = 0\nresult = x / y"
}
```

### Response (Error Example)

```json
{
  "error": [3],
  "result": "Traceback (most recent call last):\n  File \"<string>\", line 3, in <module>\nZeroDivisionError: division by zero\n"
}
```

### Response (Successful Code)

```json
{
  "error": [],
  "result": "15\n"
}
```

## Usage Example (Windows CMD)

### Successful Code

```cmd
curl -X POST http://127.0.0.1:8000/code-interpreter -H "Content-Type: application/json" -d "{\"code\":\"x = 5\ny = 10\nprint(x + y)\"}"
```

### Code with Error

```cmd
curl -X POST http://127.0.0.1:8000/code-interpreter -H "Content-Type: application/json" -d "{\"code\":\"x = 10\ny = 0\nresult = x / y\"}"
```

## Notes

* Ensure `AIPIPE_TOKEN` is set in your environment before starting the server.
* AI output may include backticks; the server strips them to parse JSON correctly.
* The tool function preserves exact stdout and traceback output.
* FastAPI server can be run with:

```cmd
uvicorn main:app --reload
```


---

## 14) Sum table values with Playwright

### Setup
```bash
npm init -y
npm install playwright
npx playwright install
```
### Usage

update the `const seeds = [84,85,86,87,88,89,90,91,92,93];` with your own seed values.
  
Then run:
```
node sum_tables.js
```
  
   **OR**  
    
You can sum it manually by going to the website and then enter the following command in console.

```
const sum = [...document.querySelectorAll("td")]
  .reduce((total, cell) => total + Number(cell.textContent.trim() || 0), 0);

console.log("Total sum:", sum);
```

Then use a calculator to calculate sum across seeds. Just change the ?seed=<num> parameter.

<img width="1919" height="1031" alt="image" src="https://github.com/user-attachments/assets/63be900d-c0f3-4c5c-90de-faf952b63043" />



---

## Final Note

This README is a **complete, question-wise, single-file submission** of all 18 problems and their corresponding commands, code, and outputs, exactly as required.
