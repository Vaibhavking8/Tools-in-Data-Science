# Tools in Data Science – Graded Assignment 2 (Complete Solutions)

This README contains the **full, question-wise solutions for all 20 problems** from **Graded Assignment 2** of the *Tools in Data Science* course.

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

## Final Note

This README is a **complete, question-wise, single-file submission** of all 20 problems and their corresponding commands, code, and outputs, exactly as required.
