"""Telegram bot — primary user interface."""

import asyncio
from uuid import uuid4

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from ugra.application.use_cases import (
    GenerateCoverLetterUseCase,
    RouteMessageUseCase,
    SearchJobsUseCase,
)
from ugra.config.settings import get_settings
from ugra.core.di.container import Container
from ugra.core.logging.setup import get_logger, setup_logging
from ugra.domain.value_objects import JobFilter

logger = get_logger(__name__)
router = Router()

_user_sessions: dict[int, dict] = {}


def _get_session(telegram_id: int) -> dict:
    if telegram_id not in _user_sessions:
        _user_sessions[telegram_id] = {
            "user_id": uuid4(),
            "skills": [],
            "experience_years": 0,
            "filters": {},
            "last_jobs": [],
        }
    return _user_sessions[telegram_id]


def _telegram_metadata() -> dict:
    return {"channel": "telegram_owner", "is_owner": True}


def _find_job(session: dict, job_id: str) -> dict | None:
    return next((j for j in session.get("last_jobs", []) if j.get("id") == job_id), None)


def _job_card_keyboard(job: dict) -> InlineKeyboardMarkup:
    job_id = job["id"]
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="AI Resume", callback_data=f"resume:{job_id}"),
            InlineKeyboardButton(text="Сгенерировать письмо", callback_data=f"letter:{job_id}"),
        ],
    ]
    if job.get("url"):
        rows.append([InlineKeyboardButton(text="Открыть", url=job["url"])])
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 *Ugra Career Agent*\n\n"
        "Ваш персональный AI-помощник в поиске работы.\n\n"
        "Команды:\n"
        "/jobs — поиск вакансий\n"
        "/top — топ совпадений\n"
        "/resume — ваши резюме\n"
        "/interview — подготовка к интервью\n"
        "/settings — настройки\n"
        "/stats — статистика",
        parse_mode="Markdown",
    )


@router.message(Command("jobs"))
async def cmd_jobs(message: Message):
    session = _get_session(message.from_user.id)
    container = Container()
    use_case = SearchJobsUseCase(container.job_source_registry(), container.career_agent())

    filters = JobFilter(**{k: v for k, v in session.get("filters", {}).items() if k in JobFilter.__dataclass_fields__})
    jobs = await use_case.execute(session["user_id"], filters, session["skills"], session["experience_years"])
    session["last_jobs"] = jobs

    if not jobs:
        await message.answer("Вакансии не найдены.")
        return

    for job in jobs[:5]:
        pros = "\n".join(f"✔ {p}" for p in job.get("pros", [])[:3])
        cons = "\n".join(f"✖ {c}" for c in job.get("cons", [])[:3])
        gaps = "\n".join(f"• {g}" for g in job.get("skill_gaps", [])[:3])

        text = (
            f"*{job['title']}*\n"
            f"_{job['company']}_\n\n"
            f"Match Score: *{job['match_percentage']}*\n\n"
            f"{pros}\n{cons}\n"
        )
        if gaps:
            text += f"\n*Недостаёт:*\n{gaps}"

        await message.answer(text, parse_mode="Markdown", reply_markup=_job_card_keyboard(job))


@router.message(Command("top"))
async def cmd_top(message: Message):
    session = _get_session(message.from_user.id)
    jobs = sorted(session.get("last_jobs", []), key=lambda j: j.get("match_score", 0), reverse=True)[:3]

    if not jobs:
        await message.answer("Сначала выполните /jobs для поиска вакансий.")
        return

    lines = ["🏆 *Топ совпадений:*\n"]
    for i, job in enumerate(jobs, 1):
        lines.append(f"{i}. *{job['title']}* — {job['match_percentage']} ({job['company']})")
    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(Command("resume"))
async def cmd_resume(message: Message):
    container = Container()
    session = _get_session(message.from_user.id)
    orchestrator = container.orchestrator()
    use_case = RouteMessageUseCase(orchestrator)

    response = await use_case.execute(
        session["user_id"],
        "/resume",
        {"resumes": session.get("resumes", []), **_telegram_metadata()},
    )
    await message.answer(response.content, parse_mode="Markdown")


@router.message(Command("interview"))
async def cmd_interview(message: Message):
    session = _get_session(message.from_user.id)
    jobs = session.get("last_jobs", [])
    if not jobs:
        await message.answer("Сначала найдите вакансии через /jobs.")
        return

    container = Container()
    use_case = RouteMessageUseCase(container.orchestrator())
    response = await use_case.execute(
        session["user_id"],
        "/interview",
        {"job": jobs[0], "skills": session["skills"], **_telegram_metadata()},
    )
    await message.answer(response.content, parse_mode="Markdown")


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    session = _get_session(message.from_user.id)
    await message.answer(
        f"⚙️ *Настройки*\n\n"
        f"Skills: {', '.join(session['skills']) or 'не заданы'}\n"
        f"Experience: {session['experience_years']} лет\n"
        f"Remote: {session['filters'].get('remote_only', False)}",
        parse_mode="Markdown",
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    session = _get_session(message.from_user.id)
    jobs = session.get("last_jobs", [])
    avg_score = sum(j.get("match_score", 0) for j in jobs) / max(len(jobs), 1)
    await message.answer(
        f"📊 *Статистика*\n\n"
        f"Просмотрено вакансий: {len(jobs)}\n"
        f"Средний Match Score: {avg_score:.0f}%",
        parse_mode="Markdown",
    )


@router.message(F.text)
async def handle_text(message: Message):
    session = _get_session(message.from_user.id)
    container = Container()
    use_case = RouteMessageUseCase(container.orchestrator())
    response = await use_case.execute(
        session["user_id"],
        message.text,
        {
            "skills": session["skills"],
            "experience_years": session["experience_years"],
            **_telegram_metadata(),
        },
    )
    await message.answer(response.content, parse_mode="Markdown")


@router.callback_query(F.data.startswith("resume:"))
async def on_resume_callback(callback: CallbackQuery):
    job_id = callback.data.split(":", 1)[1]
    session = _get_session(callback.from_user.id)
    job = _find_job(session, job_id)
    if not job:
        await callback.answer("Вакансия не найдена. Сначала выполните /jobs.", show_alert=True)
        return

    await callback.answer()
    container = Container()
    use_case = RouteMessageUseCase(container.orchestrator())
    response = await use_case.execute(
        session["user_id"],
        f"Подготовь резюме под вакансию {job['title']}",
        {"job": job, "resumes": session.get("resumes", []), **_telegram_metadata()},
    )
    await callback.message.answer(response.content, parse_mode="Markdown")


@router.callback_query(F.data.startswith("letter:"))
async def on_letter_callback(callback: CallbackQuery):
    job_id = callback.data.split(":", 1)[1]
    session = _get_session(callback.from_user.id)
    job = _find_job(session, job_id)
    if not job:
        await callback.answer("Вакансия не найдена. Сначала выполните /jobs.", show_alert=True)
        return

    await callback.answer("Генерирую письмо...")
    container = Container()
    use_case = GenerateCoverLetterUseCase(container.cover_letter_agent(), container.resume_agent())
    letter = await use_case.execute(job, session.get("resumes", []))
    await callback.message.answer(f"📝 *Сопроводительное письмо:*\n\n{letter}", parse_mode="Markdown")


async def run_bot() -> None:
    settings = get_settings()
    setup_logging(settings)

    if not settings.telegram_bot_token:
        logger.error("telegram_bot_token_not_set")
        return

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    logger.info("telegram_bot_starting")
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
