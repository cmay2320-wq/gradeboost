from flask import Flask, render_template
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from google import genai
from dotenv import load_dotenv
import os
import markdown


app = Flask(__name__)
app.secret_key = "change-this-secret-key"
load_dotenv()
def generate_study_plan(profile):
    client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
    )
    prompt = f"""
    Create a visually structured smart study plan.

    Student info:
    Education level: {profile[2]}
    Grade/year: {profile[3]}
    Subjects: {profile[4]}
    Main focus subject: {profile[5]}
    Biggest struggle: {profile[6]}
    Goal: {profile[7]}
    Daily study time: {profile[8]}

    FORMAT RULES:
    - Use headings with emojis
    - Keep sections short and clean
    - Use bullet points
    - Add spacing between sections
    - Make it feel motivational and modern
    - Avoid giant paragraphs
    - Inculde users name for personal effect

    Include these sections:

    # 🚀 Motivation
    # 📅 Today's Study Plan
    # 🎯 Weekly Goals
    # 📚 Subject Focus
    # 🧠 Smart Study Tips
    # 🔥 Final Motivation

    Make it friendly and inspiring.
    """

    

        

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text
def generate_assignment_breakdown(assignment, profile):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""
    Create a simple assignment breakdown for this student.

    Student profile:
    Education level: {profile[2]}
    Grade/year: {profile[3]}
    Subjects: {profile[4]}
    Biggest struggle: {profile[6]}
    Daily study time: {profile[8]}

    Assignment:
    Subject: {assignment[1]}
    Title: {assignment[2]}
    Description: {assignment[3]}
    Due date: {assignment[4]}
    Priority: {assignment[5]}

    Give:
    # 📌 Assignment Plan
    # 📅 Daily Breakdown
    # ✅ Checklist
    # 🔥 Motivation

    Keep it clear, friendly, and easy for a student to follow.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text

def init_db():
    conn = sqlite3.connect("gradeboost.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS onboarding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            education_level TEXT NOT NULL,
            grade_or_year TEXT NOT NULL,
            subjects TEXT NOT NULL,
            main_subject TEXT NOT NULL,
            biggest_struggle TEXT NOT NULL,
            study_goal TEXT NOT NULL,
            study_time TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    #geminai intergration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            plan_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    #study tracker 
    cursor.execute("""
         CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT DEFAULT 'To Do',
            progress INTEGER DEFAULT 0,
            ai_breakdown TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)    
    try:
        cursor.execute("ALTER TABLE assignments ADD COLUMN ai_breakdown TEXT")
    except sqlite3.OperationalError:
        pass                                   

    conn.commit()
    conn.close()

init_db()


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/create-account", methods=["GET", "POST"])
def create_account():
    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect("gradeboost.db")
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)",
                (full_name, email, hashed_password)
            )

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            return "Email already exists. Please use another email."

    return render_template("create_account.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("gradeboost.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["full_name"] = user[1]
            conn = sqlite3.connect("gradeboost.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM onboarding WHERE user_id = ?", (user[0],))
            onboarding_done = cursor.fetchone()
            conn.close()

            if onboarding_done:
                return redirect(url_for("dashboard"))
            else:
                return redirect(url_for("onboarding"))
                                    

        return "Invalid email or password."

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        education_level = request.form["education_level"]
        grade_or_year = request.form["grade_or_year"]
        subjects = request.form["subjects"]
        main_subject = request.form["main_subject"]
        biggest_struggle = request.form["biggest_struggle"]
        study_goal = request.form["study_goal"]
        study_time = request.form["study_time"]

        conn = sqlite3.connect("gradeboost.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO onboarding
            (user_id, education_level, grade_or_year, subjects, main_subject, biggest_struggle, study_goal, study_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            education_level,
            grade_or_year,
            subjects,
            main_subject,
            biggest_struggle,
            study_goal,
            study_time
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("onboarding.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("gradeboost.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM onboarding WHERE user_id = ?", (session["user_id"],))
    profile = cursor.fetchone()

    conn.close()

    if not profile:
        return redirect(url_for("onboarding"))

    return render_template("dashboard.html", profile=profile)



#assignment tracker route
@app.route("/assignments", methods=["GET", "POST"])
def assignments():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("gradeboost.db")
    cursor = conn.cursor()

    if request.method == "POST":
        subject = request.form["subject"]
        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]
        priority = request.form["priority"]

        cursor.execute("""
            INSERT INTO assignments
            (user_id, subject, title, description, due_date, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            subject,
            title,
            description,
            due_date,
            priority
        ))

        conn.commit()
        flash("Assignment added successfully.", "success")
        return redirect(url_for("assignments"))

    cursor.execute("""
        SELECT id, subject, title, description, due_date, priority, status, progress, CAST(julianday(due_date) - julianday('now') AS INTEGER) AS days_left
        FROM assignments
        WHERE user_id = ?
        ORDER BY due_date ASC
    """, (session["user_id"],))

    assignments = cursor.fetchall()
    conn.close()

    return render_template("assignments.html", assignments=assignments)


#AI assignments
@app.route("/assignment/complete/<int:assignment_id>")
def complete_assignment(assignment_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("gradeboost.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE assignments
        SET status = 'Completed', progress = 100
        WHERE id = ? AND user_id = ?
    """, (assignment_id, session["user_id"]))

    conn.commit()
    conn.close()

    flash("Assignment marked as completed.", "success")
    return redirect(url_for("assignments"))


@app.route("/assignment/delete/<int:assignment_id>")
def delete_assignment(assignment_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("gradeboost.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM assignments
        WHERE id = ? AND user_id = ?
    """, (assignment_id, session["user_id"]))

    conn.commit()
    conn.close()

    flash("Assignment deleted.", "success")
    return redirect(url_for("assignments"))


@app.route("/assignment/progress/<int:assignment_id>/<action>")
def update_assignment_progress(assignment_id, action):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("gradeboost.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT progress FROM assignments
        WHERE id = ? AND user_id = ?
    """, (assignment_id, session["user_id"]))

    item = cursor.fetchone()

    if item:
        progress = item[0]

        if action == "increase":
            progress = min(progress + 10, 100)
        elif action == "decrease":
            progress = max(progress - 10, 0)

        status = "Completed" if progress == 100 else "In Progress" if progress > 0 else "To Do"

        cursor.execute("""
            UPDATE assignments
            SET progress = ?, status = ?
            WHERE id = ? AND user_id = ?
        """, (progress, status, assignment_id, session["user_id"]))

        conn.commit()

    conn.close()
    return redirect(url_for("assignments"))


@app.route("/assignment/breakdown/<int:assignment_id>")
def assignment_breakdown(assignment_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("gradeboost.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, subject, title, description, due_date, priority, ai_breakdown
        FROM assignments
        WHERE id = ? AND user_id = ?
    """, (assignment_id, session["user_id"]))

    assignment = cursor.fetchone()

    cursor.execute("""
        SELECT * FROM onboarding
        WHERE user_id = ?
    """, (session["user_id"],))

    profile = cursor.fetchone()

    if not assignment or not profile:
        conn.close()
        return redirect(url_for("assignments"))

    if assignment[6]:
        breakdown = assignment[6]
    else:
        breakdown = generate_assignment_breakdown(assignment, profile)

        cursor.execute("""
            UPDATE assignments
            SET ai_breakdown = ?
            WHERE id = ? AND user_id = ?
        """, (breakdown, assignment_id, session["user_id"]))

        conn.commit()

    conn.close()

    formatted_breakdown = markdown.markdown(breakdown)

    return render_template(
        "assignment_breakdown.html",
        assignment=assignment,
        breakdown=formatted_breakdown
    )


#pricing route
@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

#contacts route
@app.route("/contact")
def contact():
    return render_template("contact.html")

#study planner route
@app.route("/study-plan")
def study_plan():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("gradeboost.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM onboarding WHERE user_id = ?", (session["user_id"],))
    profile = cursor.fetchone()

    if not profile:
        conn.close()
        return redirect(url_for("onboarding"))

    cursor.execute("SELECT plan_text FROM study_plans WHERE user_id = ?", (session["user_id"],))
    saved_plan = cursor.fetchone()

    if saved_plan:
        plan_text = saved_plan[0]
    else:
        plan_text = generate_study_plan(profile)

        cursor.execute("""
            INSERT INTO study_plans (user_id, plan_text)
            VALUES (?, ?)
        """, (session["user_id"], plan_text))

        conn.commit()

    conn.close()
    formatted_plan = markdown.markdown(plan_text)

    return render_template("study_plan.html", plan_text=formatted_plan)

if __name__ == "__main__":
    app.run(debug=True)


