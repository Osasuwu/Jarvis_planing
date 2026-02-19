WATERFALL_PHASES = [
    "Requirements Gathering",
    "System Design",
    "Implementation Planning",
    "Testing Strategy",
    "Deployment Planning",
    "Maintenance Strategy",
]


PHASE_ARTIFACT_REQUIREMENTS = {
    "Requirements Gathering": "Formal requirements specification with functional/non-functional requirements and constraints.",
    "System Design": "Architecture specification, component boundaries, and integration strategy.",
    "Implementation Planning": "Implementation breakdown, timeline, resource plan, and execution dependencies.",
    "Testing Strategy": "Comprehensive test strategy including unit/integration/system/UAT and acceptance criteria.",
    "Deployment Planning": "Release plan, environment strategy, DevOps rollout, rollback, and observability.",
    "Maintenance Strategy": "Operations model, incident handling, post-release governance, and improvement loop.",
}


PHASE_ARTIFACT_REQUIREMENTS_RU = {
    "Requirements Gathering": "Формальная спецификация требований (функциональные/нефункциональные требования и ограничения).",
    "System Design": "Архитектурная спецификация, границы компонентов и стратегия интеграции.",
    "Implementation Planning": "Декомпозиция реализации, график, план ресурсов и зависимости выполнения.",
    "Testing Strategy": "Комплексная стратегия тестирования (unit/integration/system/UAT) и критерии приемки.",
    "Deployment Planning": "План релиза, стратегия окружений, rollout/rollback и наблюдаемость.",
    "Maintenance Strategy": "Операционная модель, обработка инцидентов, пострелизное управление и цикл улучшений.",
}


def phase_context_prompt(phase_name: str, language: str = "en") -> str:
    if language == "ru":
        artifact = PHASE_ARTIFACT_REQUIREMENTS_RU[phase_name]
        return (
            f"Текущая фаза Waterfall: {phase_name}. "
            f"Строго оставайся в рамках этой фазы. "
            f"Обязательный артефакт этой фазы: {artifact}."
        )

    artifact = PHASE_ARTIFACT_REQUIREMENTS[phase_name]
    return (
        f"Current Waterfall phase: {phase_name}. "
        f"Strictly stay within this phase scope. "
        f"Required artifact for this phase: {artifact}."
    )
