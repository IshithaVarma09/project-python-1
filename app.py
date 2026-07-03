from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import database as db
from datetime import date, datetime, timedelta
import pandas as pd
import json

app = Flask(__name__)
app.secret_key = "super_secret_session_key_for_academic_system"

# Initialize DB on startup
db.init_db()

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user_id = db.verify_user(username, password)
        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials. Please try again.", "error")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        age = request.form.get("age")
        dob = request.form.get("dob")
        gender = request.form.get("gender")
        study = request.form.get("study")
        
        if db.create_user(username, password, email, age, dob, gender, study):
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Username already exists.", "error")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session: return redirect(url_for("login"))
    user_id = session["user_id"]
    
    tasks_df = db.get_tasks(user_id)
    pending_tasks = tasks_df[tasks_df["status"] == "Pending"]
    completed_tasks = tasks_df[tasks_df["status"] == "Completed"]
    subjects_df = db.get_subjects(user_id)
    
    total_subjects = len(subjects_df)
    total_pending = len(pending_tasks)
    total_completed = len(completed_tasks)
    avg_readiness = subjects_df["preparation_progress"].mean() if not subjects_df.empty else 0.0

    return render_template("dashboard.html", 
        username=session["username"],
        total_subjects=total_subjects, 
        total_pending=total_pending, 
        total_completed=total_completed, 
        avg_readiness=round(avg_readiness, 1)
    )

@app.route("/tasks", methods=["GET", "POST"])
def tasks_page():
    if "user_id" not in session: return redirect(url_for("login"))
    user_id = session["user_id"]
    
    if request.method == "POST":
        title = request.form.get("title")
        task_type = request.form.get("type")
        subject = request.form.get("subject")
        deadline = request.form.get("deadline")
        status = "Pending"
        est_hours = int(request.form.get("estimated_hours", 2))
        
        db.add_task(user_id, title, task_type, deadline, status, subject, est_hours)
        flash("Task added successfully!", "success")
        return redirect(url_for("tasks_page"))
    
    pending_tasks = db.get_tasks(user_id, "Pending").to_dict('records')
    completed_tasks = db.get_tasks(user_id, "Completed").to_dict('records')
    subjects = db.get_subjects(user_id)["name"].tolist()
    
    return render_template("tasks.html", 
                           pending_tasks=pending_tasks, 
                           completed_tasks=completed_tasks,
                           subjects=subjects)

@app.route("/tasks/complete/<int:task_id>")
def complete_task(task_id):
    if "user_id" not in session: return redirect(url_for("login"))
    db.update_task_status(task_id, session["user_id"], "Completed")
    flash("Task marked as completed!", "success")
    return redirect(url_for("tasks_page"))

@app.route("/exam", methods=["GET", "POST"])
def exam_page():
    if "user_id" not in session: return redirect(url_for("login"))
    user_id = session["user_id"]
    
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_subject":
            name = request.form.get("name")
            target = int(request.form.get("target_score", 80))
            if db.add_subject(user_id, name, target):
                flash(f"Subject '{name}' added successfully!", "success")
            else:
                flash("Subject already exists.", "error")
        elif action == "update_progress":
            subject_id = request.form.get("subject_id")
            progress = int(request.form.get("progress"))
            db.update_preparation_progress(user_id, subject_id, progress)
            flash("Progress updated!", "success")
            
        return redirect(url_for("exam_page"))

    subjects = db.get_subjects(user_id).to_dict('records')
    return render_template("exam.html", subjects=subjects)


# --- API Routes for Charts ---

@app.route("/api/dashboard_data")
def api_dashboard_data():
    if "user_id" not in session: return jsonify({"error": "Unauthorized"}), 401
    user_id = session["user_id"]
    
    tasks_df = db.get_tasks(user_id)
    pending_df = tasks_df[tasks_df["status"] == "Pending"]
    subjects_df = db.get_subjects(user_id)
    
    # Workload Distribution
    workload = pending_df.groupby('subject')['estimated_hours'].sum().reset_index() if not pending_df.empty else pd.DataFrame(columns=['subject', 'estimated_hours'])
    workload_data = {"labels": workload['subject'].tolist(), "data": workload['estimated_hours'].tolist()}
    
    # Stress Score Calculation
    stress_score = 0
    num_pending = len(pending_df)
    stress_score += min(num_pending * 5, 40)
    
    if num_pending > 0:
        pending_df['deadline'] = pd.to_datetime(pending_df['deadline']).dt.date
        today = date.today()
        urgent_tasks = pending_df[pending_df['deadline'] <= (today + pd.Timedelta(days=3))].shape[0]
        stress_score += min(urgent_tasks * 10, 30)
        
    if not subjects_df.empty:
        avg_prep = subjects_df['preparation_progress'].mean()
        if avg_prep < 50:
            stress_score += min((50 - avg_prep) * 0.6, 30)
            
    stress_score = min(stress_score, 100)
    stress_label = "Low" if stress_score < 30 else "Moderate" if stress_score < 70 else "High"
    stress_color = "#4CAF50" if stress_score < 30 else "#FF9800" if stress_score < 70 else "#F44336"
    stress_data = {"score": stress_score, "label": stress_label, "color": stress_color}
    
    # Exam Readiness
    exam_readiness = {"labels": subjects_df['name'].tolist(), "data": subjects_df['preparation_progress'].tolist()} if not subjects_df.empty else {"labels": [], "data": []}
    
    return jsonify({
        "workload": workload_data,
        "stress": stress_data,
        "exam_readiness": exam_readiness
    })

@app.route("/api/reminders")
def api_reminders():
    if "user_id" not in session: return jsonify({"error": "Unauthorized"}), 401
    user_id = session["user_id"]
    
    tasks_df = db.get_tasks(user_id)
    pending_df = tasks_df[tasks_df["status"] == "Pending"]
    subjects_df = db.get_subjects(user_id)
    
    reminders = []
    
    if not pending_df.empty:
        pending_df['deadline'] = pd.to_datetime(pending_df['deadline']).dt.date
        today = date.today()
        urgent = pending_df[pending_df['deadline'] <= (today + pd.Timedelta(days=3))]
        for _, row in urgent.iterrows():
            days_left = (row['deadline'] - today).days
            if days_left < 0:
                reminders.append({"type": "danger", "message": f"Overdue: '{row['title']}' was due {-days_left} days ago! Please submit it or mark it complete."})
            elif days_left == 0:
                reminders.append({"type": "danger", "message": f"Urgent: '{row['title']}' is due TODAY!"})
            else:
                reminders.append({"type": "warning", "message": f"Reminder: '{row['title']}' is due in {days_left} days."})
    
    if not subjects_df.empty:
        for _, row in subjects_df.iterrows():
            if row['preparation_progress'] < row['target_score'] - 20:
                reminders.append({"type": "info", "message": f"Exam Prep: You are far from your target in {row['name']}. Dedicate some study time soon!"})
            elif row['preparation_progress'] < 50:
                reminders.append({"type": "warning", "message": f"Exam Prep: Your readiness for {row['name']} is below 50%."})

    import random
    random.shuffle(reminders)
    return jsonify({"reminders": reminders[:3]})

if __name__ == "__main__":
    app.run(debug=True, port=8501)
