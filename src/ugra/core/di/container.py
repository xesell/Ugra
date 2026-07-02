"""Dependency injection container."""

from uuid import UUID

from dependency_injector import containers, providers

from ugra.agents.career.agent import CareerAgent
from ugra.agents.cover_letter.agent import CoverLetterAgent
from ugra.agents.interview.agent import InterviewAgent
from ugra.agents.learning.agent import LearningAgent
from ugra.agents.orchestrator.intelligence_orchestrator import IntelligenceOrchestrator
from ugra.agents.resume.agent import ResumeAgent
from ugra.agents.runtime.context_builder import ContextBuilder
from ugra.agents.runtime.memory import AgentMemory
from ugra.agents.runtime.tools import AgentTools
from ugra.application.autonomous.first_task import FirstAutonomousTask
from ugra.application.autonomous.scheduler import AutonomousScheduler
from ugra.application.events.handlers import register_event_handlers
from ugra.application.intelligence.cognition_engine import CognitionEngine
from ugra.application.intelligence.goal_manager import GoalManager
from ugra.application.intelligence.personality_service import PersonalityService
from ugra.application.intelligence.ugra_mood import UgraMoodService
from ugra.config.settings import Settings, get_settings
from ugra.core.events.bus import EventBus
from ugra.core.tools.implementations import create_default_tool_registry
from ugra.domain.entities import JobSource
from ugra.infrastructure.adapters.job_sources.geekjob import GeekJobAdapter
from ugra.infrastructure.adapters.job_sources.habr import HabrCareerAdapter
from ugra.infrastructure.adapters.job_sources.hh import HeadHunterAdapter
from ugra.infrastructure.adapters.job_sources.registry import JobSourceRegistry
from ugra.infrastructure.llm.completion_gateway import CompletionGateway
from ugra.infrastructure.llm.factory import create_completion_port
from ugra.infrastructure.llm.service import create_llm_service
from ugra.infrastructure.mcp.registry import MCPRegistry
from ugra.infrastructure.persistence.database import create_engine, create_session_factory
from ugra.infrastructure.persistence.repositories.goal_repository import InMemoryGoalRepository
from ugra.infrastructure.persistence.repositories.memory_factory import create_memory_repository
from ugra.infrastructure.prompts.manager import PromptManager
from ugra.infrastructure.rag.knowledge_base import EmbeddingService


def _create_agent_registry(
    career: CareerAgent,
    resume: ResumeAgent,
    cover_letter: CoverLetterAgent,
    interview: InterviewAgent,
    learning: LearningAgent,
):
    from ugra.agents.base.registry import AgentRegistry

    registry = AgentRegistry()
    for agent in [career, resume, cover_letter, interview, learning]:
        registry.register(agent)
    return registry


def _create_job_source_registry(settings: Settings) -> JobSourceRegistry:
    registry = JobSourceRegistry()
    registry.register(HeadHunterAdapter(settings.hh_api_token, country="113", source=JobSource.HH_RU))
    registry.register(HeadHunterAdapter(settings.hh_api_token, country="40", source=JobSource.HH_KZ))
    registry.register(HabrCareerAdapter())
    registry.register(GeekJobAdapter(settings.geekjob_api_token))
    return registry


def _resolve_default_user_id(settings: Settings) -> UUID | None:
    if settings.default_user_id:
        return UUID(settings.default_user_id)
    return None


def _bootstrap_events(event_bus: EventBus, personality: PersonalityService, mood: UgraMoodService) -> None:
    register_event_handlers(event_bus, personality, mood)


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "ugra.presentation.api.routes",
            "ugra.presentation.telegram.bot",
        ]
    )

    config = providers.Singleton(get_settings)

    event_bus = providers.Singleton(EventBus)

    db_engine = providers.Singleton(create_engine, settings=config)
    session_factory = providers.Singleton(create_session_factory, engine=db_engine)

    # AI Core
    prompt_manager = providers.Singleton(PromptManager)
    completion_gateway = providers.Singleton(
        lambda settings: CompletionGateway(create_completion_port(settings)),
        settings=config,
    )
    llm_service = providers.Singleton(create_llm_service, settings=config)
    personality_service = providers.Singleton(PersonalityService)
    ugra_mood = providers.Singleton(UgraMoodService)
    cognition_engine = providers.Singleton(
        CognitionEngine,
        gateway=completion_gateway,
        prompt_manager=prompt_manager,
    )

    memory_repository = providers.Singleton(
        create_memory_repository,
        settings=config,
        session_factory=session_factory,
    )
    agent_memory = providers.Singleton(AgentMemory, repository=memory_repository)

    goal_repository = providers.Singleton(InMemoryGoalRepository)
    goal_manager = providers.Singleton(
        GoalManager,
        repository=goal_repository,
        event_bus=event_bus,
    )

    context_builder = providers.Singleton(
        ContextBuilder,
        memory=agent_memory,
        goals=goal_manager,
        personality=personality_service,
    )

    embedding_service = providers.Singleton(EmbeddingService, model_name=config.provided.embedding_model)

    job_source_registry = providers.Singleton(_create_job_source_registry, settings=config)
    mcp_registry = providers.Singleton(MCPRegistry)

    tool_registry = providers.Singleton(
        create_default_tool_registry,
        job_sources=job_source_registry,
        llm_service=llm_service,
    )
    agent_tools = providers.Singleton(AgentTools, registry=tool_registry)

    career_agent = providers.Singleton(
        CareerAgent,
        personality=personality_service,
        cognition=cognition_engine,
        goal_manager=goal_manager,
        memory_repo=memory_repository,
        agent_memory=agent_memory,
        tool_registry=tool_registry,
        prompt_manager=prompt_manager,
        event_bus=event_bus,
        llm=llm_service,
        job_sources=job_source_registry,
        knowledge_base=providers.Object(None),
    )
    resume_agent = providers.Singleton(ResumeAgent, llm=llm_service)
    cover_letter_agent = providers.Singleton(CoverLetterAgent, llm=llm_service)
    interview_agent = providers.Singleton(InterviewAgent, llm=llm_service)
    learning_agent = providers.Singleton(LearningAgent, llm=llm_service)

    agent_registry = providers.Singleton(
        _create_agent_registry,
        career=career_agent,
        resume=resume_agent,
        cover_letter=cover_letter_agent,
        interview=interview_agent,
        learning=learning_agent,
    )

    orchestrator = providers.Singleton(
        IntelligenceOrchestrator,
        registry=agent_registry,
        cognition=cognition_engine,
        goal_manager=goal_manager,
        memory_repo=memory_repository,
        tool_registry=tool_registry,
        personality=personality_service,
        event_bus=event_bus,
    )

    first_autonomous_task = providers.Singleton(
        FirstAutonomousTask,
        orchestrator=orchestrator,
        memory=agent_memory,
        mood=ugra_mood,
        event_bus=event_bus,
    )

    autonomous_scheduler = providers.Singleton(
        AutonomousScheduler,
        orchestrator=orchestrator,
        event_bus=event_bus,
        default_user_id=providers.Callable(_resolve_default_user_id, settings=config),
        interval_seconds=config.provided.autonomous_interval_seconds,
    )

    event_handlers = providers.Singleton(
        _bootstrap_events,
        event_bus=event_bus,
        personality=personality_service,
        mood=ugra_mood,
    )


def bootstrap_mcp(container: Container) -> None:
    settings = container.config()
    mcp = container.mcp_registry()
    mcp.load_from_json(settings.mcp_servers)
