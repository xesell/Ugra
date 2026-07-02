"""Heuristic cover letter when LLM is unavailable."""

from __future__ import annotations

import re


def build_fallback_cover_letter(
    *,
    job_title: str,
    company: str,
    job_description: str = "",
    experience: str = "",
    resume_content: str = "",
    template_content: str = "",
) -> str:
    """Build a usable Russian cover letter without calling the LLM."""
    title = job_title.strip() or "специалиста"
    org = company.strip() or "вашей компании"

    skills = _extract_skills(resume_content or experience)
    skills_line = ", ".join(skills[:6]) if skills else "современный стек и практический опыт"

    intro = (
        f"Здравствуйте!\n\n"
        f"Меня заинтересовала вакансия «{title}» в {org}. "
        f"Считаю, что мой опыт хорошо соотносится с требованиями позиции."
    )

    if experience:
        intro += f" {experience.strip().rstrip('.')}."

    body_bits: list[str] = []
    if skills:
        body_bits.append(
            f"В работе опираюсь на навыки: {skills_line}. "
            "Умею быстро вникать в продукт, брать ответственность за результат и доводить задачи до продакшена."
        )
    else:
        body_bits.append(
            "Имею релевантный опыт в разработке и готов применить его для решения задач вашей команды."
        )

    if job_description.strip():
        focus = _shorten(job_description, 220)
        body_bits.append(f"Особенно откликается направление вакансии: {focus}")

    if template_content.strip() and len(template_content) > 40:
        snippet = _shorten(template_content.replace("\n", " "), 180)
        body_bits.append(f"Опираюсь на свой рабочий шаблон: {snippet}")

    closing = (
        "\n\nБуду рад(а) обсудить, как смогу быть полезен(на) команде. "
        "Спасибо за внимание к моей кандидатуре!"
    )

    letter = intro + "\n\n" + " ".join(body_bits) + closing
    return letter


def _extract_skills(text: str) -> list[str]:
    known = [
        "Python", "FastAPI", "Django", "PostgreSQL", "Docker", "Kubernetes",
        "React", "TypeScript", "JavaScript", "Go", "Java", "C#", ".NET",
        "AWS", "Azure", "CI/CD", "Redis", "Kafka", "LLM", "OpenAI",
    ]
    lower = text.lower()
    found = [skill for skill in known if skill.lower() in lower]
    if found:
        return found
    tokens = re.findall(r"[A-Za-zА-Яа-я0-9+#.]{3,}", text)
    return list(dict.fromkeys(tokens[:8]))


def _shorten(text: str, limit: int) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"
