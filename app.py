import sqlite3
import streamlit as st

DB_NAME = "college.db"

# ---------- Database layer (SQL) ----------

def get_conn():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the table if it does not exist yet."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT NOT NULL,
                course  TEXT NOT NULL,
                marks   INTEGER NOT NULL
            )
            """
        )


def add_student(name: str, course: str, marks: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO students (name, course, marks) VALUES (?, ?, ?)",
            (name, course, marks),
        )


def fetch_students():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM students ORDER BY id").fetchall()


def delete_student(student_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))


def student_count() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM students").fetchone()["c"]


# ---------- UI ----------

st.set_page_config(page_title="Simple DBMS", page_icon="🏫", layout="centered")
st.title("🏫 Simple Student DBMS")
st.caption("Python + SQL (SQLite) + Streamlit")

init_db()

tab_add, tab_view = st.tabs(["➕ Add Data", "📋 View Data"])

with tab_add:
    st.subheader("Insert a new student")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Name")
        course = st.text_input("Course", placeholder="e.g. BCA")
        marks = st.number_input("Marks", min_value=0, max_value=100, step=1)
        submitted = st.form_submit_button("Add to Database", use_container_width=True)

    if submitted:
        if not name.strip() or not course.strip():
            st.error("Name and course cannot be empty.")
        else:
            add_student(name.strip(), course.strip(), int(marks))
            st.success(f"Saved **{name}** to the database.")

with tab_view:
    st.subheader(f"All records ({student_count()} rows)")
    rows = fetch_students()

    if not rows:
        st.info("No data yet. Add a student in the **Add Data** tab.")
    else:
        # Show as a table
        st.dataframe(
            [{"ID": r["id"], "Name": r["name"], "Course": r["course"], "Marks": r["marks"]} for r in rows],
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.markdown("**Delete a record**")
        col1, col2 = st.columns([3, 1])
        options = {f'{r["id"]} — {r["name"]}': r["id"] for r in rows}
        with col1:
            choice = st.selectbox("Select student", list(options.keys()))
        with col2:
            if st.button("🗑 Delete", use_container_width=True):
                delete_student(options[choice])
                st.warning("Deleted. Refreshing...")
                st.rerun()

st.divider()
st.markdown(
    """
    **SQL running behind the scenes**
    ```sql
    CREATE TABLE students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        course TEXT NOT NULL,
        marks INTEGER NOT NULL
    );
    INSERT INTO students (name, course, marks) VALUES ('Amit', 'BCA', 88);
    SELECT * FROM students;
    ```
    """
)
