"""Event handlers — agents subscribe to domain events."""

from ugra.application.intelligence.personality_service import PersonalityService
from ugra.application.intelligence.ugra_mood import UgraMoodService
from ugra.core.events.bus import EventBus
from ugra.core.logging.setup import get_logger
from ugra.domain.events import (
    AgentStateChanged,
    InterviewReceived,
    NotificationSent,
    OfferReceived,
    ResumeUpdated,
    SkillGapDetected,
    VacancyFound,
)

logger = get_logger(__name__)


def register_event_handlers(
    event_bus: EventBus,
    personality: PersonalityService,
    mood: UgraMoodService,
) -> None:
    """Wire all event subscriptions at application bootstrap."""

    async def on_vacancy_found(event: VacancyFound) -> None:
        emotion = personality.react_to_event("VacancyFound")
        logger.info(
            "event_vacancy_found",
            job_id=str(event.job_id),
            company=event.company,
            match_score=event.match_score,
            emotion=emotion.value,
        )

    async def on_interview_received(event: InterviewReceived) -> None:
        emotion = personality.react_to_event("InterviewReceived")
        logger.info(
            "event_interview_received",
            job_id=str(event.job_id),
            user_id=str(event.user_id),
            emotion=emotion.value,
        )

    async def on_offer_received(event: OfferReceived) -> None:
        emotion = personality.react_to_event("OfferReceived")
        logger.info(
            "event_offer_received",
            job_id=str(event.job_id),
            salary=event.salary,
            emotion=emotion.value,
        )

    async def on_resume_updated(event: ResumeUpdated) -> None:
        logger.info("event_resume_updated", resume_id=str(event.resume_id), version=event.version)

    async def on_skill_gap(event: SkillGapDetected) -> None:
        emotion = personality.react_to_event("SkillGapDetected")
        logger.info(
            "event_skill_gap",
            skills=list(event.missing_skills),
            emotion=emotion.value,
        )

    async def on_notification_sent(event: NotificationSent) -> None:
        logger.info("event_notification_sent", channel=event.channel)

    async def on_state_changed(event: AgentStateChanged) -> None:
        label = mood.format_status(event.new_state)
        logger.info(
            "event_agent_state_changed",
            agent=event.agent_name,
            state=event.new_state,
            ui_label=label,
        )

    event_bus.subscribe(VacancyFound, on_vacancy_found)
    event_bus.subscribe(InterviewReceived, on_interview_received)
    event_bus.subscribe(OfferReceived, on_offer_received)
    event_bus.subscribe(ResumeUpdated, on_resume_updated)
    event_bus.subscribe(SkillGapDetected, on_skill_gap)
    event_bus.subscribe(NotificationSent, on_notification_sent)
    event_bus.subscribe(AgentStateChanged, on_state_changed)
