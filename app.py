import os
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from db import get_db, init_db
from skills import extract_text_from_file, detect_skills, detect_skill_counts

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

import json as _json

with open(BASE_DIR / "companies.json") as _f:
    COMPANIES = _json.load(_f)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Not logged in."}), 401
        return f(*args, **kwargs)
    return wrapper


def compatibility(skill_weights: dict, company: dict) -> int:
    """
    skill_weights: {skill_name: weight}, weight > 1 means it came from the
    resume (stronger signal) or was mentioned multiple times.
    """
    if not skill_weights:
        return 0
    required = company["requiredSkills"]
    if not required:
        return 0

    lower_weights = {k.lower(): v for k, v in skill_weights.items()}
    earned = 0.0
    for skill in required:
        earned += lower_weights.get(skill.lower(), 0)

    # each required skill is worth 1 "point" baseline; resume/frequency weighting
    # can push a single matched skill above 1, so cap contribution per skill at 1.3
    earned_capped = 0.0
    for skill in required:
        earned_capped += min(lower_weights.get(skill.lower(), 0), 1.3)

    score = (earned_capped / len(required)) * 100

    # small bonus for broad overall skill coverage beyond just this job's requirements
    breadth_bonus = min(len(skill_weights) * 0.5, 8)
    return int(min(100, round(score + breadth_bonus)))


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

    profile_weights = _json.loads(profile["skill_weights"]) if profile and profile["skill_weights"] else {}

    jobs = []
    for c in COMPANIES:
        jobs.append({
            **c,
            "compatibility": compatibility(profile_weights, c),
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
    weights = _json.loads(result.get("skill_weights") or "{}")
    result["skills"] = sorted(weights.keys())
    result["resumeSkills"] = sorted([s for s, w in weights.items() if w > 1.0])
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

    # Existing weights carry forward; re-derive from title/bio each save so
    # edits are reflected immediately.
    weights = {}
    for skill, count in detect_skill_counts(f"{title} {bio}").items():
        weights[skill] = 1.0  # bio/title mention: baseline signal

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
    resume_counts = {}
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
            resume_counts = detect_skill_counts(resume_text)
    elif resume:
        # No new upload this save, but a resume already exists on disk —
        # keep its skill signal alive by re-reading it.
        existing_path = RESUME_DIR / resume
        if existing_path.exists():
            resume_counts = detect_skill_counts(extract_text_from_file(existing_path))

    # Resume mentions are a stronger, more credible signal than free-text bio.
    # Weight = 1.0 base + up to +0.3 for repeated mentions (capped).
    for skill, count in resume_counts.items():
        boost = min((count - 1) * 0.1, 0.3)
        weights[skill] = max(weights.get(skill, 0), 1.0 + boost)

    skills_str = ",".join(sorted(weights.keys()))

    conn.execute(
        "UPDATE profiles SET name=?, title=?, bio=?, photo=?, resume=?, skills=?, skill_weights=? WHERE user_id=?",
        (name, title, bio, photo, resume, skills_str, _json.dumps(weights), user_id),
    )
    conn.commit()
    conn.close()

    return jsonify({
        "name": name, "title": title, "bio": bio,
        "photo": photo, "resume": resume,
        "skills": sorted(weights.keys()),
        "resumeSkills": sorted([s for s, w in weights.items() if w > 1.0]),
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
