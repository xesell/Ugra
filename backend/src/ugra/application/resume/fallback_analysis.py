"""Heuristic resume analysis when LLM is unavailable."""

from __future__ import annotations

import re

COMMON_TECH = [
    "Python", "Java", "C#", ".NET", "JavaScript", "TypeScript", "Go", "Rust", "Kotlin",
    "React", "Vue", "Angular", "Node.js", "FastAPI", "Django", "Spring", "ASP.NET",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes", "AWS", "Azure",
    "Git", "CI/CD", "Kafka", "RabbitMQ", "LLM", "OpenAI", "TensorFlow", "PyTorch",
]

DOMAIN_HINTS = [
    "FinTech", "Betting", "HRTech", "Enterprise", "E-commerce", "Banking", "Insurance",
    "Healthcare", "Gaming", "EdTech", "Logistics", "Telecom",
]


def build_fallback_analysis(resume_text: str) -> dict:
    """Build minimal structured profile from resume text without LLM."""
    text_lower = resume_text.lower()
    lines = [ln.strip() for ln in resume_text.splitlines() if ln.strip()]

    full_name = ""
    for line in lines[:8]:
        if 2 <= len(line.split()) <= 4 and line[0].isupper() and "@" not in line:
            if not any(kw in line.lower() for kw in ("опыт", "experience", "resume", "резюме")):
                full_name = line
                break

    skills = [
        {"name": tech, "category": "Tech", "confidence": 55.0}
        for tech in COMMON_TECH
        if tech.lower() in text_lower
    ][:24]

    domains = [d for d in DOMAIN_HINTS if d.lower() in text_lower][:6]

    years_match = re.search(r"(\d+)\+?\s*(?:лет|years?)", text_lower)
    years = float(years_match.group(1)) if years_match else 3.0

    title_guess = "Backend Developer"
    for hint, title in [
        ("architect", "Solution Architect"),
        ("devops", "DevOps Engineer"),
        ("frontend", "Frontend Developer"),
        (".net", ".NET Developer"),
        ("python", "Python Developer"),
        ("data", "Data Engineer"),
    ]:
        if hint in text_lower:
            title_guess = title
            break

    return {
        "full_name": full_name,
        "primary_specialization": title_guess,
        "secondary_specializations": [],
        "level": "middle",
        "level_rationale": "Предварительная оценка без AI (лимит API)",
        "experience": {
            "total_years": years,
            "commercial_years": years,
            "leadership_years": 0,
            "architecture_years": 0,
            "ai_years": 0,
            "devops_years": 0,
            "backend_years": years if "backend" in title_guess.lower() else 0,
            "frontend_years": 0,
            "analytics_years": 0,
        },
        "skills": skills,
        "domains": domains,
        "strengths": skills[:5] and [f"Опыт с {skills[0]['name']}"] or ["Требуется полный AI-анализ"],
        "weaknesses": ["Полный анализ не выполнен — лимит AI API"],
        "preferred_roles": [{"title": title_guess, "priority": "high"}],
        "search_strategy": {
            "include_keywords": [title_guess.split()[0]],
            "exclude_keywords": ["junior"],
            "preferred_roles": [title_guess],
            "excluded_roles": [],
        },
        "ai_summary": [
            "Полный AI-анализ временно недоступен из-за лимита запросов (429).",
            f"Из резюме извлечено {len(skills)} технологий и базовая информация об опыте.",
            "Нажмите «Пересканировать» через 1–2 минуты для полного профиля.",
        ],
        "companies_count": len(re.findall(r"(?:llc|ltd|ооо|зао|inc\b|company|компан)", text_lower)),
        "projects_count": len(re.findall(r"(?:project|проект)", text_lower)),
        "prompt_context": "",
    }


def is_rate_limit_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "too many requests" in msg
