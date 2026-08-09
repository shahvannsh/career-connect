import re
from pathlib import Path

KNOWN_SKILLS = [
    "Swift", "iOS", "Objective-C", "Product Design",
    "AWS", "Java", "Python", "Distributed Systems",
    "Machine Learning", "Go", "Kubernetes",
    "C#", ".NET", "Azure", "TypeScript",
    "Android", "Kotlin", "Embedded Systems", "C++",
    "React", "PHP", "GraphQL", "PyTorch",
    "Robotics", "Node.js", "Microservices",
    "JavaScript", "SQL", "Docker", "Linux", "Git",
    "HTML", "CSS", "Flask", "Django", "REST", "Agile", "Ruby",
]


def extract_text_from_file(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            import pdfplumber
            text = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text.append(t)
            return "\n".join(text)
        elif ext == ".docx":
            import docx
            d = docx.Document(path)
            return "\n".join(p.text for p in d.paragraphs)
        elif ext == ".doc":
            return ""  # legacy binary format, skip parsing
    except Exception:
        return ""
    return ""


def detect_skills(text: str) -> list:
    """Returns list of matched skill names (order preserved from KNOWN_SKILLS)."""
    return list(detect_skill_counts(text).keys())


def detect_skill_counts(text: str) -> dict:
    """Returns {skill_name: occurrence_count} for skills found in text."""
    if not text:
        return {}
    text_low = text.lower()
    counts = {}
    for skill in KNOWN_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        matches = re.findall(pattern, text_low)
        if matches:
            counts[skill] = len(matches)
    return counts
