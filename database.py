import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "app.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT,
            age INTEGER,
            dob DATE,
            gender TEXT,
            field_of_study TEXT
        )
    ''')
    
    # Create Tasks Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            type TEXT NOT NULL, 
            deadline DATE NOT NULL,
            status TEXT NOT NULL,
            subject TEXT NOT NULL,
            estimated_hours INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Create Subjects Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target_score INTEGER NOT NULL,
            preparation_progress INTEGER DEFAULT 0,
            UNIQUE(user_id, name),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# --- Auth ---
def create_user(username, password, email=None, age=None, dob=None, gender=None, study=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        pw_hash = generate_password_hash(password)
        c.execute("INSERT INTO users (username, password, email, age, dob, gender, field_of_study) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                  (username, pw_hash, email, age, dob, gender, study))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # User exists
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[1], password):
         return user[0] # Return user_id
    return None

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

# --- Tasks CRUD ---
def add_task(user_id, title, task_type, deadline, status, subject, estimated_hours):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO tasks (user_id, title, type, deadline, status, subject, estimated_hours) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, title, task_type, deadline, status, subject, estimated_hours)
    )
    conn.commit()
    conn.close()

def get_tasks(user_id, status=None):
    conn = sqlite3.connect(DB_NAME)
    query = f"SELECT * FROM tasks WHERE user_id={user_id}"
    if status:
        query += f" AND status='{status}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def update_task_status(task_id, user_id, new_status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE tasks SET status=? WHERE id=? AND user_id=?", (new_status, task_id, user_id))
    conn.commit()
    conn.close()

def delete_task(task_id, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user_id))
    conn.commit()
    conn.close()

# --- Subjects CRUD ---
def add_subject(user_id, name, target_score):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO subjects (user_id, name, target_score) VALUES (?, ?, ?)", (user_id, name, target_score))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Subject already exists for this user
    finally:
        conn.close()

def get_subjects(user_id):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(f"SELECT * FROM subjects WHERE user_id={user_id}", conn)
    conn.close()
    return df

def update_preparation_progress(user_id, subject_id, progress):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE subjects SET preparation_progress=? WHERE id=? AND user_id=?", (progress, subject_id, user_id))
    conn.commit()
    conn.close()
