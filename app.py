import os
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from db import get_db, init_db
from skills import extract_text_from_file, detect_skills

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
PHOTO_DIR = UPLOAD_DIR / "photos"
RESUME_DIR = UPLOAD_DIR / "resumes"
PHOTO_DIR.mkdir(parents=True, exist_ok=True)
RESUME_DIR.mkdir(parents=True, exist_ok=True)

RESUME_EXT = {".pdf", ".doc", ".docx"}
PHOTO_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

init_db()

COMPANIES = [
    {"id": 1, "name": "Apple Inc.", "industry": "Technology", "marketCap": "$391.04 billion",
     "logo": "🍎", "salary": "$165,000/year", "requiredSkills": ["Swift", "iOS", "Objective-C", "Product Design"]},
    {"id": 2, "name": "Amazon.com Inc.", "industry": "E-commerce & Cloud Computing", "marketCap": "$637.96 billion",
     "logo": "📦", "salary": "$155,000/year", "requiredSkills": ["AWS", "Java", "Python", "Distributed Systems"]},
    {"id": 3, "name": "Alphabet Inc. (Google)", "industry": "Technology", "marketCap": "$350.02 billion",
     "logo": "🔍", "salary": "$180,000/year", "requiredSkills": ["Python", "Machine Learning", "Go", "Kubernetes"]},
    {"id": 4, "name": "Microsoft Corporation", "industry": "Technology", "marketCap": "$412.87 billion",
     "logo": "🪟", "salary": "$170,000/year", "requiredSkills": ["C#", ".NET", "Azure", "TypeScript"]},
    {"id": 5, "name": "Samsung Electronics", "industry": "Electronics & Technology", "marketCap": "$298.5 billion",
     "logo": "📱", "salary": "$140,000/year", "requiredSkills": ["Android", "Kotlin", "Embedded Systems", "C++"]},
    {"id": 6, "name": "Meta Platforms Inc.", "industry": "Social Media & Technology", "marketCap": "$310.4 billion",
     "logo": "👥", "salary": "$175,000/year", "requiredSkills": ["React", "PHP", "GraphQL", "PyTorch"]},
    {"id": 7, "name": "Tesla Inc.", "industry": "Automotive & Energy", "marketCap": "$220.1 billion",
     "logo": "🚗", "salary": "$150,000/year", "requiredSkills": ["C++", "Robotics", "Embedded Systems", "Python"]},
    {"id": 8, "name": "Netflix Inc.", "industry": "Media & Entertainment", "marketCap": "$95.3 billion",
     "logo": "🎬", "salary": "$190,000/year", "requiredSkills": ["Java", "Microservices", "AWS", "Node.js"]},
]


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Not logged in."}), 401
        return f(*args, **kwargs)
    return wrapper


def compatibility(profile_skills, company):
    if not profile_skills:
        return 0
    skills_lower = {s.lower() for s in profile_skills}
    required = company["requiredSkills"]
    matched = sum(1 for s in required if s.lower() in skills_lower)
    return int((matched / len(required)) * 100)


# ---------- Auth ----------

@app.route("/api/signup", methods=["POST"])
def signup():
    body = request.get_json(force=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    if not username or not password:
        return jsonify({"error": "Username and password required."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Username already taken."}), 400

    cur = conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, generate_password_hash(password)),
    )
    user_id = cur.lastrowid
    conn.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    session["user_id"] = user_id
    session["username"] = username
    return jsonify({"id": user_id, "username": username})


@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json(force=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password."}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify({"id": user["id"], "username": user["username"]})


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/api/me")
def me():
    if "user_id" not in session:
        return jsonify({"loggedIn": False})
    return jsonify({"loggedIn": True, "username": session["username"]})


# ---------- Jobs ----------

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/api/jobs")
@login_required
def get_jobs():
    user_id = session["user_id"]
    conn = get_db()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    saved_ids = {r["job_id"] for r in conn.execute("SELECT job_id FROM saved WHERE user_id = ?", (user_id,))}
    applied_ids = {r["job_id"] for r in conn.execute("SELECT job_id FROM applied WHERE user_id = ?", (user_id,))}
    skipped_ids = {r["job_id"] for r in conn.execute("SELECT job_id FROM skipped WHERE user_id = ?", (user_id,))}
    conn.close()

    profile_skills = (profile["skills"] or "").split(",") if profile else []
    profile_skills = [s for s in profile_skills if s]

    jobs = []
    for c in COMPANIES:
        jobs.append({
            **c,
            "compatibility": compatibility(profile_skills, c),
            "saved": c["id"] in saved_ids,
            "applied": c["id"] in applied_ids,
            "skipped": c["id"] in skipped_ids,
        })
    return jsonify(jobs)


@app.route("/api/jobs/<int:job_id>/save", methods=["POST"])
@login_required
def save_job(job_id):
    user_id = session["user_id"]
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO saved (user_id, job_id) VALUES (?, ?)", (user_id, job_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/jobs/<int:job_id>/skip", methods=["POST"])
@login_required
def skip_job(job_id):
    user_id = session["user_id"]
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO skipped (user_id, job_id) VALUES (?, ?)", (user_id, job_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/jobs/<int:job_id>/apply", methods=["POST"])
@login_required
def apply_job(job_id):
    user_id = session["user_id"]
    company = next((c for c in COMPANIES if c["id"] == job_id), None)
    if not company:
        return jsonify({"error": "Job not found."}), 404

    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO applied (user_id, job_id) VALUES (?, ?)", (user_id, job_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "message": f"Quick apply sent to {company['name']}!"})


@app.route("/api/matches")
@login_required
def get_matches():
    user_id = session["user_id"]
    conn = get_db()
    rows = conn.execute("SELECT job_id FROM applied WHERE user_id = ?", (user_id,)).fetchall()
    conn.close()
    ids = {r["job_id"] for r in rows}
    matched = [c for c in COMPANIES if c["id"] in ids]
    return jsonify(matched)


# ---------- Profile ----------

@app.route("/api/profile", methods=["GET"])
@login_required
def get_profile():
    user_id = session["user_id"]
    conn = get_db()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    if not profile:
        return jsonify({})
    result = dict(profile)
    result["linkedin_connected"] = bool(result["linkedin_connected"])
    result["skills"] = [s for s in (result["skills"] or "").split(",") if s]
    return jsonify(result)


@app.route("/api/profile", methods=["POST"])
@login_required
def update_profile():
    user_id = session["user_id"]
    body = request.form
    conn = get_db()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()

    name = body.get("name", profile["name"])
    title = body.get("title", profile["title"])
    bio = body.get("bio", profile["bio"])
    photo = profile["photo"]
    resume = profile["resume"]
    skills_set = set((profile["skills"] or "").split(","))
    skills_set.discard("")

    # detect skills from title + bio text too
    skills_set.update(detect_skills(f"{title} {bio}"))

    photo_file = request.files.get("photo")
    if photo_file and photo_file.filename:
        ext = os.path.splitext(photo_file.filename)[1].lower()
        if ext in PHOTO_EXT:
            if photo:
                old_path = PHOTO_DIR / photo
                if old_path.exists():
                    old_path.unlink()
            filename = f"{user_id}_{secure_filename(photo_file.filename)}"
            photo_file.save(PHOTO_DIR / filename)
            photo = filename

    resume_file = request.files.get("resume")
    if resume_file and resume_file.filename:
        ext = os.path.splitext(resume_file.filename)[1].lower()
        if ext in RESUME_EXT:
            if resume:
                old_path = RESUME_DIR / resume
                if old_path.exists():
                    old_path.unlink()
            filename = f"{user_id}_{secure_filename(resume_file.filename)}"
            save_path = RESUME_DIR / filename
            resume_file.save(save_path)
            resume = filename

            resume_text = extract_text_from_file(save_path)
            skills_set.update(detect_skills(resume_text))

    skills_str = ",".join(sorted(skills_set))

    conn.execute(
        "UPDATE profiles SET name=?, title=?, bio=?, photo=?, resume=?, skills=? WHERE user_id=?",
        (name, title, bio, photo, resume, skills_str, user_id),
    )
    conn.commit()
    conn.close()

    return jsonify({
        "name": name, "title": title, "bio": bio,
        "photo": photo, "resume": resume,
        "skills": [s for s in skills_str.split(",") if s],
    })


@app.route("/api/profile/linkedin", methods=["POST"])
@login_required
def toggle_linkedin():
    user_id = session["user_id"]
    conn = get_db()
    profile = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    new_val = 0 if profile["linkedin_connected"] else 1
    conn.execute("UPDATE profiles SET linkedin_connected=? WHERE user_id=?", (new_val, user_id))
    conn.commit()
    conn.close()
    message = "LinkedIn connected!" if new_val else "LinkedIn disconnected!"
    return jsonify({"linkedInConnected": bool(new_val), "message": message})


@app.route("/uploads/photos/<path:filename>")
def get_photo(filename):
    return send_from_directory(PHOTO_DIR, filename)


@app.route("/uploads/resumes/<path:filename>")
def get_resume(filename):
    return send_from_directory(RESUME_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
