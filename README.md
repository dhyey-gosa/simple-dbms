# Simple Student DBMS

Python + SQL (SQLite) + Streamlit. Two related tables, full CRUD, search/filter, aggregates, grades, and a live JOIN.

## Schema

```sql
CREATE TABLE courses (
    course_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name TEXT NOT NULL UNIQUE
);

CREATE TABLE students (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    course_id INTEGER NOT NULL,
    marks     INTEGER NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(course_id)
);
```

Grades (computed): **A** ≥ 85, **B** ≥ 70, **C** ≥ 55, else **F**.

## Features

- **Add** courses and students (`INSERT`)
- **Search by name** + **filter by course** (`WHERE … LIKE`)
- **Edit** name / course / marks (`UPDATE`)
- **Delete** (`DELETE`)
- **Dashboard**: AVG / MAX / MIN / COUNT + bar charts (`GROUP BY`)
- **Grade** column (SQL `CASE` + Python helper)
- **Validation**: required name, marks 0–100
- **Sort by marks** toggle
- **JOIN** of `students` and `courses` shown live in the SQL tab
- Old single-table DBs are migrated automatically (adds `FOREIGN KEY`)

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Host it (free)

**Streamlit Community Cloud:**

1. Push this folder to a GitHub repo.
2. Go to https://share.streamlit.io → "New app"
3. Pick the repo, main file path `app.py`, click **Deploy**.

**Netlify:** static sites only — use Streamlit Cloud for this Python app.
