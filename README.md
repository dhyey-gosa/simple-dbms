# Simple Student DBMS

Python + SQL (SQLite) + Streamlit. One table, add and view data, done.

## Table

```sql
CREATE TABLE students (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    name   TEXT NOT NULL,
    course TEXT NOT NULL,
    marks  INTEGER NOT NULL
);
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Host it (free)

**Streamlit Community Cloud (recommended, works with this Python app):**

1. Push this folder to a GitHub repo.
2. Go to https://share.streamlit.io → "New app"
3. Pick the repo, set main file path to `app.py`, click **Deploy**.

**Netlify:** Netlify hosts static sites and serverless functions, not long-running Python/Streamlit apps.
If you must use Netlify, deploy a static frontend there and keep this Streamlit app on Streamlit Cloud.
