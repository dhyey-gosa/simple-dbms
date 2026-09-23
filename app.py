import sqlite3
import streamlit as st

DB_NAME = "college.db"

GRADE_SQL = (
    "CASE "
    "WHEN marks >= 85 THEN 'A' "
    "WHEN marks >= 70 THEN 'B' "
    "WHEN marks >= 55 THEN 'C' "
    "ELSE 'F' END"
)

JOIN_SQL = """
SELECT
    s.id,
    s.name,
    c.course_name AS course,
    s.marks,
    CASE
        WHEN s.marks >= 85 THEN 'A'
        WHEN s.marks >= 70 THEN 'B'
        WHEN s.marks >= 55 THEN 'C'
        ELSE 'F'
    END AS grade
FROM students AS s
JOIN courses AS c ON s.course_id = c.course_id
ORDER BY s.marks DESC;
"""


def grade_of(marks: int) -> str:
    if marks >= 85:
        return "A"
    if marks >= 70:
        return "B"
    if marks >= 55:
        return "C"
    return "F"


# ---------- Database layer (SQL) ----------

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables (with FOREIGN KEY) and migrate old schema if needed."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                course_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL UNIQUE
            )
            """
        )

        cols = [
            r["name"]
            for r in conn.execute("PRAGMA table_info(students)").fetchall()
        ]

        if cols and "course_id" not in cols:
            # Old schema: students(id, name, course TEXT, marks) -> new schema
            conn.execute("ALTER TABLE students RENAME TO students_old")
            conn.execute(
                """
                CREATE TABLE students (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    name      TEXT NOT NULL,
                    course_id INTEGER NOT NULL,
                    marks     INTEGER NOT NULL,
                    FOREIGN KEY (course_id) REFERENCES courses(course_id)
                )
                """
            )
            for row in conn.execute(
                "SELECT name, course, marks FROM students_old"
            ).fetchall():
                cur = conn.execute(
                    "INSERT OR IGNORE INTO courses (course_name) VALUES (?)",
                    (row["course"],),
                )
                if cur.lastrowid == 0:
                    cid = conn.execute(
                        "SELECT course_id FROM courses WHERE course_name = ?",
                        (row["course"],),
                    ).fetchone()["course_id"]
                else:
                    cid = cur.lastrowid
                conn.execute(
                    "INSERT INTO students (name, course_id, marks) VALUES (?, ?, ?)",
                    (row["name"], cid, row["marks"]),
                )
            conn.execute("DROP TABLE students_old")
        elif not cols:
            conn.execute(
                """
                CREATE TABLE students (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    name      TEXT NOT NULL,
                    course_id INTEGER NOT NULL,
                    marks     INTEGER NOT NULL,
                    FOREIGN KEY (course_id) REFERENCES courses(course_id)
                )
                """
            )

        # Seed default courses on first run
        if conn.execute("SELECT COUNT(*) AS c FROM courses").fetchone()["c"] == 0:
            conn.executemany(
                "INSERT INTO courses (course_name) VALUES (?)",
                [("BCA",), ("BSC",), ("MCA",)],
            )


def fetch_courses():
    with get_conn() as conn:
        return conn.execute(
            "SELECT course_id, course_name FROM courses ORDER BY course_name"
        ).fetchall()


def add_course(course_name: str) -> str | None:
    """Returns error message, or None on success."""
    name = course_name.strip()
    if not name:
        return "Course name cannot be empty."
    with get_conn() as conn:
        try:
            conn.execute(
                "INSERT INTO courses (course_name) VALUES (?)", (name,)
            )
        except sqlite3.IntegrityError:
            return f"Course **{name}** already exists."
    return None


def add_student(name: str, course_id: int, marks: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO students (name, course_id, marks) VALUES (?, ?, ?)",
            (name, course_id, marks),
        )


def fetch_students(search: str = "", course_id: int | None = None, sort_by_marks: bool = False):
    """JOIN query with optional WHERE filters (name search + course)."""
    sql = (
        "SELECT s.id, s.name, c.course_name AS course, s.marks, "
        f"{GRADE_SQL} AS grade, s.course_id "
        "FROM students AS s "
        "JOIN courses AS c ON s.course_id = c.course_id WHERE 1=1"
    )
    params: list = []
    if search.strip():
        sql += " AND s.name LIKE ?"
        params.append(f"%{search.strip()}%")
    if course_id is not None:
        sql += " AND s.course_id = ?"
        params.append(course_id)
    sql += " ORDER BY s.marks DESC" if sort_by_marks else " ORDER BY s.id"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def fetch_student(student_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, name, course_id, marks FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()


def update_student(student_id: int, name: str, course_id: int, marks: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE students SET name = ?, course_id = ?, marks = ? WHERE id = ?",
            (name, course_id, marks, student_id),
        )


def delete_student(student_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))


def get_stats() -> dict:
    with get_conn() as conn:
        overall = conn.execute(
            """
            SELECT COUNT(*) AS n,
                   COALESCE(AVG(marks), 0) AS avg_m,
                   COALESCE(MAX(marks), 0) AS max_m,
                   COALESCE(MIN(marks), 0) AS min_m
            FROM students
            """
        ).fetchone()
        by_course = conn.execute(
            """
            SELECT c.course_name AS course,
                   COUNT(s.id) AS students,
                   COALESCE(AVG(s.marks), 0) AS avg_m
            FROM courses AS c
            LEFT JOIN students AS s ON s.course_id = c.course_id
            GROUP BY c.course_id
            ORDER BY c.course_name
            """
        ).fetchall()
    return {"overall": overall, "by_course": by_course}


def validate_student(name: str, marks: float) -> str | None:
    if not name.strip():
        return "Name cannot be empty."
    if len(name.strip()) > 50:
        return "Name must be 50 characters or fewer."
    if not (0 <= marks <= 100):
        return "Marks must be between 0 and 100."
    return None


# ---------- UI ----------

st.set_page_config(page_title="Simple DBMS", page_icon="🏫", layout="wide")
st.title("🏫 Simple Student DBMS")
st.caption("Python + SQL (SQLite) + Streamlit · CRUD · JOIN · Aggregates")

init_db()
courses = fetch_courses()
course_names = [c["course_name"] for c in courses]
course_ids = {c["course_name"]: c["course_id"] for c in courses}

tab_dash, tab_add, tab_view, tab_edit, tab_sql = st.tabs(
    ["📊 Dashboard", "➕ Add Data", "🔍 View / Search", "✏️ Edit", "🗄 SQL"]
)

# ----- Dashboard: aggregate stats + bar chart -----
with tab_dash:
    stats = get_stats()
    o = stats["overall"]
    st.subheader("Aggregate stats")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", o["n"])
    c2.metric("Average marks", f"{o['avg_m']:.1f}")
    c3.metric("Highest", o["max_m"])
    c4.metric("Lowest", o["min_m"])

    st.markdown("**Students per course** (`COUNT … GROUP BY course`)")
    counts = {r["course"]: r["students"] for r in stats["by_course"]}
    st.bar_chart(counts)

    st.markdown("**Average marks by course** (`AVG(marks) … GROUP BY course`)")
    avgs = {r["course"]: round(r["avg_m"], 1) for r in stats["by_course"]}
    st.bar_chart(avgs)

# ----- Add: course + student -----
with tab_add:
    st.subheader("Add a course")
    with st.form("course_form", clear_on_submit=True):
        new_course = st.text_input("Course name", placeholder="e.g. MCA")
        ok = st.form_submit_button("Add course", width="stretch")
    if ok:
        err = add_course(new_course)
        if err:
            st.error(err)
        else:
            st.success(f"Course **{new_course.strip()}** added.")
            st.rerun()

    st.divider()
    st.subheader("Add a student")
    if not courses:
        st.warning("Add a course first.")
    else:
        with st.form("student_form", clear_on_submit=True):
            name = st.text_input("Name", max_chars=50)
            course_choice = st.selectbox("Course", course_names)
            marks = st.number_input("Marks", min_value=0, max_value=100, step=1)
            submitted = st.form_submit_button(
                "Insert into database", width="stretch"
            )
        if submitted:
            err = validate_student(name, marks)
            if err:
                st.error(err)
            else:
                add_student(name.strip(), course_ids[course_choice], int(marks))
                st.success(
                    f"Saved **{name.strip()}** → {course_choice} "
                    f"(grade {grade_of(int(marks))})."
                )

# ----- View: search + filter + sort -----
with tab_view:
    st.subheader("Search & filter")
    f1, f2, f3 = st.columns([3, 2, 1])
    with f1:
        search = st.text_input("Search by name", placeholder="type a name…")
    with f2:
        filter_choice = st.selectbox("Filter by course", ["All courses"] + course_names)
    with f3:
        sort_marks = st.checkbox("Sort by marks", value=True)

    cid_filter = (
        None if filter_choice == "All courses" else course_ids[filter_choice]
    )
    rows = fetch_students(
        search=search, course_id=cid_filter, sort_by_marks=sort_marks
    )

    st.markdown(f"### Results ({len(rows)} rows)")
    if not rows:
        st.info("No matching records.")
    else:
        st.dataframe(
            [
                {
                    "ID": r["id"],
                    "Name": r["name"],
                    "Course": r["course"],
                    "Marks": r["marks"],
                    "Grade": r["grade"],
                }
                for r in rows
            ],
            width="stretch",
            hide_index=True,
        )

        st.divider()
        st.markdown("**Delete a record**")
        d1, d2 = st.columns([3, 1])
        options = {f'{r["id"]} — {r["name"]} ({r["course"]})': r["id"] for r in rows}
        with d1:
            choice = st.selectbox("Select student", list(options.keys()))
        with d2:
            if st.button("🗑 Delete", width="stretch"):
                delete_student(options[choice])
                st.warning("Deleted.")
                st.rerun()

# ----- Edit (UPDATE) -----
with tab_edit:
    st.subheader("Update a student (UPDATE query)")
    all_students = fetch_students()
    if not all_students:
        st.info("No students to edit yet.")
    else:
        labels = {
            f'{r["id"]} — {r["name"]} ({r["course"]})': r["id"]
            for r in all_students
        }
        with st.form("edit_form"):
            pick = st.selectbox("Student", list(labels.keys()))
            sid = labels[pick]
            current = fetch_student(sid)
            new_name = st.text_input("Name", value=current["name"], max_chars=50)
            current_course_name = next(
                (n for n, i in course_ids.items() if i == current["course_id"]),
                course_names[0],
            )
            new_course = st.selectbox(
                "Course",
                course_names,
                index=course_names.index(current_course_name),
            )
            new_marks = st.number_input(
                "Marks",
                min_value=0,
                max_value=100,
                value=int(current["marks"]),
                step=1,
            )
            saved = st.form_submit_button("Save changes", width="stretch")

        if saved:
            err = validate_student(new_name, new_marks)
            if err:
                st.error(err)
            else:
                update_student(
                    sid, new_name.strip(), course_ids[new_course], int(new_marks)
                )
                st.success(
                    f"Updated student **{sid}** → grade {grade_of(int(new_marks))}."
                )
                st.rerun()

# ----- SQL explorer -----
with tab_sql:
    st.subheader("SQL running behind the scenes")
    st.markdown(
        f"""
```sql
-- Schema (2 tables, FOREIGN KEY)
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

-- INSERT
INSERT INTO courses (course_name) VALUES ('BCA');
INSERT INTO students (name, course_id, marks) VALUES ('Amit', 1, 88);

-- Search + filter (View tab)
SELECT s.id, s.name, c.course_name, s.marks
FROM students AS s
JOIN courses AS c ON s.course_id = c.course_id
WHERE s.name LIKE '%am%' AND s.course_id = 1
ORDER BY s.marks DESC;

-- UPDATE (Edit tab)
UPDATE students SET name = 'Amit', marks = 91, course_id = 1 WHERE id = 1;

-- DELETE
DELETE FROM students WHERE id = 1;

-- Aggregates (Dashboard)
SELECT c.course_name, COUNT(s.id), AVG(s.marks)
FROM courses AS c
LEFT JOIN students AS s ON s.course_id = c.course_id
GROUP BY c.course_id;
```
"""
    )
    st.markdown("### Live JOIN result")
    st.code(JOIN_SQL, language="sql")
    joined = fetch_students(sort_by_marks=True)
    if joined:
        st.dataframe(
            [
                {
                    "ID": r["id"],
                    "Name": r["name"],
                    "Course": r["course"],
                    "Marks": r["marks"],
                    "Grade": r["grade"],
                }
                for r in joined
            ],
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No rows yet for the JOIN.")
