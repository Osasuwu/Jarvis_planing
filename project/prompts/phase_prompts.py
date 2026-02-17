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


def phase_context_prompt(phase_name: str) -> str:
    artifact = PHASE_ARTIFACT_REQUIREMENTS[phase_name]
    return (
        f"Current Waterfall phase: {phase_name}. "
        f"Strictly stay within this phase scope. "
        f"Required artifact for this phase: {artifact}."
    )
