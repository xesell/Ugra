"""Build prompt context string from candidate profile."""

from ugra.domain.candidate_profile import CandidateProfile


def build_prompt_context(profile: CandidateProfile) -> str:
    """Human-readable context injected into all LLM system prompts."""
    idn = profile.identity
    exp = profile.experience
    lines = [
        f"Пользователь: {idn.full_name or 'кандидат'}.",
        f"Основная специализация — {idn.primary_specialization}.",
    ]
    if idn.secondary_specializations:
        lines.append(f"Дополнительные специализации: {', '.join(idn.secondary_specializations)}.")
    lines.append(f"Уровень: {idn.level.value} ({idn.level_rationale}).")
    lines.append(f"Коммерческий опыт: {exp.commercial_years:.0f} лет, общий: {exp.total_years:.0f} лет.")

    if exp.leadership_years > 0:
        lines.append(f"Опыт руководства: {exp.leadership_years:.0f} лет.")
    if exp.architecture_years > 0:
        lines.append("Имеет опыт проектирования архитектуры.")
    if exp.ai_years > 0:
        lines.append("Имеет опыт AI Automation.")

    top = profile.top_skills(12)
    if top:
        lines.append(f"Ключевые технологии: {', '.join(top)}.")

    if profile.domains:
        lines.append(f"Отрасли: {', '.join(profile.domains)}.")
    if profile.strengths:
        lines.append(f"Сильные стороны: {', '.join(profile.strengths[:6])}.")
    if profile.weaknesses:
        lines.append(f"Слабые стороны (не предлагать): {', '.join(profile.weaknesses[:5])}.")

    high_roles = [r.title for r in profile.preferred_roles if r.priority == "high"]
    if high_roles:
        lines.append(f"Приоритетные роли: {', '.join(high_roles)}.")

    low_roles = [r.title for r in profile.preferred_roles if r.priority == "low"]
    if low_roles:
        lines.append(f"Низкий приоритет ролей: {', '.join(low_roles)}.")

    if profile.search_strategy.exclude_keywords:
        lines.append(f"Не предлагать вакансии с: {', '.join(profile.search_strategy.exclude_keywords[:8])}.")

    lines.append("Все решения принимай на основе этого профиля, не анализируй PDF повторно.")
    return "\n".join(lines)
