from __future__ import annotations

from orchestration.meeting_state import MeetingState


def render_markdown_plan(state: MeetingState) -> str:
    phase = state.phase_states

    def artifact_text(phase_name: str) -> str:
        value = phase[phase_name].artifact
        if not value:
            return "_No finalized artifact captured._"
        return value.get("summary", str(value))

    lines = [
        f"# Project Development Plan: {state.project_name}",
        "",
        "## Executive Summary",
        artifact_text("Requirements Gathering"),
        "",
        "## Stakeholder Analysis",
        artifact_text("Requirements Gathering"),
        "",
        "## Requirements Specification",
        artifact_text("Requirements Gathering"),
        "",
        "## Architecture Overview",
        artifact_text("System Design"),
        "",
        "## Tech Stack",
        artifact_text("System Design"),
        "",
        "## Timeline (Waterfall Aligned)",
        artifact_text("Implementation Planning"),
        "",
        "## Risk Analysis",
        artifact_text("Implementation Planning"),
        "",
        "## Testing Plan",
        artifact_text("Testing Strategy"),
        "",
        "## Deployment Plan",
        artifact_text("Deployment Planning"),
        "",
        "## Maintenance Plan",
        artifact_text("Maintenance Strategy"),
        "",
    ]

    return "\n".join(lines)
