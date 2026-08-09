import json
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
PHOTO_DIR = UPLOAD_DIR / "photos"
RESUME_DIR = UPLOAD_DIR / "resumes"
DATA_FILE = BASE_DIR / "data.json"

PHOTO_DIR.mkdir(parents=True, exist_ok=True)
RESUME_DIR.mkdir(parents=True, exist_ok=True)

RESUME_EXT = {".pdf", ".doc", ".docx"}
PHOTO_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

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


def default_data():
    return {
        "profile": {
            "name": "",
            "title": "",
            "bio": "",
            "photo": "",
            "resume": "",
            "linkedInConnected": False,
        },
        "saved": [],
        "applied": [],
        "matches": [],
    }


def load_data():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return default_data()


def save_data(data):
    DATA_FILE.write_text(json.dumps(data, indent=2))


def compatibility(profile, company):
    bio_text = f"{profile.get('title','')} {profile.get('bio','')}".lower()
    if not bio_text.strip():
        return 0
    skills = company["requiredSkills"]
    matched = sum(1 for s in skills if s.lower() in bio_text)
    base = int((matched / len(skills)) * 100)
    return min(100, base + (10 if profile.get("resume") else 0))


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/api/jobs")
def get_jobs():
    data = load_data()
    profile = data["profile"]
    jobs = []
    for c in COMPANIES:
        jobs.append({
            **c,
            "compatibility": compatibility(profile, c),
            "saved": c["id"] in data["saved"],
            "applied": c["id"] in data["applied"],
        })
    return jsonify(jobs)


@app.route("/api/jobs/<int:job_id>/save", methods=["POST"])
def save_job(job_id):
    data = load_data()
    if job_id not in data["saved"]:
        data["saved"].append(job_id)
    save_data(data)
    return jsonify({"ok": True})


@app.route("/api/jobs/<int:job_id>/apply", methods=["POST"])
def apply_job(job_id):
    data = load_data()
    company = next((c for c in COMPANIES if c["id"] == job_id), None)
    if not company:
        return jsonify({"error": "Job not found."}), 404
    if job_id not in data["applied"]:
        data["applied"].append(job_id)
    if job_id not in data["matches"]:
        data["matches"].append(job_id)
    save_data(data)
    return jsonify({"ok": True, "message": f"Quick apply sent to {company['name']}!"})


@app.route("/api/matches")
def get_matches():
    data = load_data()
    matched = [c for c in COMPANIES if c["id"] in data["matches"]]
    return jsonify(matched)


@app.route("/api/profile", methods=["GET"])
def get_profile():
    return jsonify(load_data()["profile"])


@app.route("/api/profile", methods=["POST"])
def update_profile():
    data = load_data()
    body = request.form
    data["profile"]["name"] = body.get("name", data["profile"]["name"])
    data["profile"]["title"] = body.get("title", data["profile"]["title"])
    data["profile"]["bio"] = body.get("bio", data["profile"]["bio"])

    photo = request.files.get("photo")
    if photo and photo.filename:
        ext = os.path.splitext(photo.filename)[1].lower()
        if ext in PHOTO_EXT:
            old = data["profile"].get("photo")
            if old:
                old_path = PHOTO_DIR / old
                if old_path.exists():
                    old_path.unlink()
            filename = secure_filename(photo.filename)
            photo.save(PHOTO_DIR / filename)
            data["profile"]["photo"] = filename

    resume = request.files.get("resume")
    if resume and resume.filename:
        ext = os.path.splitext(resume.filename)[1].lower()
        if ext in RESUME_EXT:
            old = data["profile"].get("resume")
            if old:
                old_path = RESUME_DIR / old
                if old_path.exists():
                    old_path.unlink()
            filename = secure_filename(resume.filename)
            resume.save(RESUME_DIR / filename)
            data["profile"]["resume"] = filename

    save_data(data)
    return jsonify(data["profile"])


@app.route("/api/profile/linkedin", methods=["POST"])
def toggle_linkedin():
    data = load_data()
    data["profile"]["linkedInConnected"] = not data["profile"]["linkedInConnected"]
    save_data(data)
    message = "LinkedIn connected!" if data["profile"]["linkedInConnected"] else "LinkedIn disconnected!"
    return jsonify({"linkedInConnected": data["profile"]["linkedInConnected"], "message": message})


@app.route("/uploads/photos/<path:filename>")
def get_photo(filename):
    return send_from_directory(PHOTO_DIR, filename)


@app.route("/uploads/resumes/<path:filename>")
def get_resume(filename):
    return send_from_directory(RESUME_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
