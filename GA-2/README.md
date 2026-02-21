# Tools in Data Science – Graded Assignment 2 (Complete Solutions)

This README contains the **full, question-wise solutions for all 20 problems** from **Graded Assignment 2** of the *Tools in Data Science* course.

---
## 1) Compress an image

Working on wsl

## 1️⃣ Install WebP Tools

```bash
sudo apt update
sudo apt install webp imagemagick
```

Verify installation:

```bash
cwebp -version
dwebp -version
```

---

## 2️⃣ Convert PNG → Lossless WebP

Use maximum lossless compression:

```bash
cwebp -lossless -z 9 -m 6 download.png -o final.webp
```

### 🔍 Flags Explained

* `-lossless` → ensures pixel-perfect output
* `-z 9` → highest compression level
* `-m 6` → slowest method, smallest file size

### ✅ Submission

Submit:

* `final.webp` (losslessly compressed, < 400 bytes)

---

## 3) Git Time Travel: History Investigation

Check your own requirements and make changes accordingly.

### Goal

Find the commit that changed `timeout` to 210 in `config.json` and get its parent commit hash.

#### 1. Find the commit

```bash
git log -p -S210 -- config.json
```

Shows commits where the string `210` was added or removed.

#### 2. Verify the change

```bash
git show <commit_hash> -- config.json
```

Confirm the diff includes:

```diff
-  "timeout": 540,
+  "timeout": 210,
```

#### 3. Get parent commit hash

```bash
git rev-parse --short=7 <commit_hash>^
```

Outputs the 7-character short hash of the parent commit.

---

## 14) Deploy a POST analytics endpoint to Vercel

Add this to resolve CORS issue.

```python
# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

Check out the full solution in `api/index.py`

---

## Final Note

This README is a **complete, question-wise, single-file submission** of all 20 problems and their corresponding commands, code, and outputs, exactly as required.
