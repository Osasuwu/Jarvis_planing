from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from orchestration.phase_artifacts import build_phase_artifact


@dataclass
class TranscriptEntry:
    turn: int
    phase: str
    speaker: str
    content: str
    timestamp_utc: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class PhaseState:
    name: str
    max_turns: int = 0
    extension_count: int = 0
    turn_count: int = 0
    converged: bool = False
    raw_contributions: list[dict[str, Any]] = field(default_factory=list)
    draft_artifact: dict[str, Any] = field(default_factory=dict)
    artifact: dict[str, Any] = field(default_factory=dict)
    approved_by_human: bool = False


@dataclass
class MeetingState:
    project_name: str
    project_description: str
    meeting_language: str
    phases: list[str]
    max_turns_per_phase: int
    global_max_turns: int
    current_phase_index: int = 0
    total_turns: int = 0
    interrupted: bool = False
    transcript: list[TranscriptEntry] = field(default_factory=list)
    phase_states: dict[str, PhaseState] = field(default_factory=dict)
    session_started_utc: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self) -> None:
        self.phase_states = {
            name: PhaseState(name=name, max_turns=self.max_turns_per_phase) for name in self.phases
        }

    @property
    def current_phase(self) -> str:
        return self.phases[self.current_phase_index]

    def add_transcript(self, speaker: str, content: str) -> None:
        self.total_turns += 1
        phase = self.current_phase
        self.phase_states[phase].turn_count += 1
        self.transcript.append(
            TranscriptEntry(turn=self.total_turns, phase=phase, speaker=speaker, content=content)
        )

    def can_continue_phase(self) -> bool:
        phase_state = self.phase_states[self.current_phase]
        return phase_state.turn_count < phase_state.max_turns

    def extend_current_phase_turn_limit(self, extra_turns: int, max_extensions: int = 3) -> bool:
        phase_state = self.phase_states[self.current_phase]
        if extra_turns <= 0:
            return False
        if phase_state.extension_count >= max_extensions:
            return False
        phase_state.max_turns += extra_turns
        phase_state.extension_count += 1
        return True

    def can_continue_meeting(self) -> bool:
        return self.total_turns < self.global_max_turns and not self.interrupted

    def mark_phase_converged(self, artifact: dict[str, Any]) -> None:
        phase_state = self.phase_states[self.current_phase]
        phase_state.converged = True
        phase_state.artifact = artifact

    def update_phase_draft(self, contribution: dict[str, Any]) -> None:
        if not contribution:
            return
        phase_state = self.phase_states[self.current_phase]
        phase_state.raw_contributions.append(contribution)
        phase_state.draft_artifact = build_phase_artifact(
            self.current_phase,
            phase_state.raw_contributions,
        )

    def approve_current_phase(self, approved: bool) -> None:
        self.phase_states[self.current_phase].approved_by_human = approved

    def transition_to_next_phase(self) -> bool:
        if self.current_phase_index + 1 >= len(self.phases):
            return False
        self.current_phase_index += 1
        return True

    def is_fully_approved(self) -> bool:
        return all(
            phase_state.converged and phase_state.approved_by_human
            for phase_state in self.phase_states.values()
        )

    def resume_from_phase(self, phase_index: int) -> None:
        if phase_index < 0 or phase_index >= len(self.phases):
            raise ValueError(f"Invalid phase index: {phase_index}")

        keep_phases = set(self.phases[:phase_index])
        self.transcript = [entry for entry in self.transcript if entry.phase in keep_phases]

        self.total_turns = 0
        for entry in self.transcript:
            self.total_turns += 1
            entry.turn = self.total_turns

        for phase_name in self.phases[phase_index:]:
            self.phase_states[phase_name] = PhaseState(name=phase_name, max_turns=self.max_turns_per_phase)

        self.current_phase_index = phase_index
        self.interrupted = False

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> "MeetingState":
        phases = payload.get("phases")
        if not isinstance(phases, list) or not phases:
            phase_states_payload = payload.get("phase_states", {})
            if isinstance(phase_states_payload, dict) and phase_states_payload:
                phases = list(phase_states_payload.keys())
            else:
                raise ValueError("Checkpoint payload does not contain phases information.")

        state = cls(
            project_name=str(payload.get("project_name", "Untitled Project")),
            project_description=str(payload.get("project_description", "")),
            meeting_language=str(payload.get("meeting_language", "en")),
            phases=[str(phase) for phase in phases],
            max_turns_per_phase=int(payload.get("max_turns_per_phase", 16)),
            global_max_turns=int(payload.get("global_max_turns", 140)),
            current_phase_index=int(payload.get("current_phase_index", 0)),
            total_turns=int(payload.get("total_turns", 0)),
            interrupted=bool(payload.get("interrupted", False)),
            session_started_utc=str(payload.get("session_started_utc", datetime.utcnow().isoformat())),
        )

        phase_states_payload = payload.get("phase_states", {})
        if isinstance(phase_states_payload, dict):
            restored_phase_states: dict[str, PhaseState] = {}
            for phase_name in state.phases:
                raw = phase_states_payload.get(phase_name, {})
                restored_phase_states[phase_name] = PhaseState(
                    name=phase_name,
                    max_turns=int(raw.get("max_turns", state.max_turns_per_phase)),
                    extension_count=int(raw.get("extension_count", 0)),
                    turn_count=int(raw.get("turn_count", 0)),
                    converged=bool(raw.get("converged", False)),
                    raw_contributions=list(raw.get("raw_contributions", [])),
                    draft_artifact=dict(raw.get("draft_artifact", {})),
                    artifact=dict(raw.get("artifact", {})),
                    approved_by_human=bool(raw.get("approved_by_human", False)),
                )
            state.phase_states = restored_phase_states

        transcript_payload = payload.get("transcript", [])
        restored_transcript: list[TranscriptEntry] = []
        if isinstance(transcript_payload, list):
            for index, row in enumerate(transcript_payload, start=1):
                if not isinstance(row, dict):
                    continue
                restored_transcript.append(
                    TranscriptEntry(
                        turn=int(row.get("turn", index)),
                        phase=str(row.get("phase", state.current_phase)),
                        speaker=str(row.get("speaker", "unknown")),
                        content=str(row.get("content", "")),
                        timestamp_utc=str(row.get("timestamp_utc", datetime.utcnow().isoformat())),
                    )
                )
        state.transcript = restored_transcript

        if state.current_phase_index < 0 or state.current_phase_index >= len(state.phases):
            state.current_phase_index = 0

        if state.total_turns <= 0:
            state.total_turns = len(state.transcript)

        return state

    def to_json(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_description": self.project_description,
            "meeting_language": self.meeting_language,
            "session_started_utc": self.session_started_utc,
            "phases": self.phases,
            "current_phase": self.current_phase,
            "current_phase_index": self.current_phase_index,
            "max_turns_per_phase": self.max_turns_per_phase,
            "global_max_turns": self.global_max_turns,
            "total_turns": self.total_turns,
            "interrupted": self.interrupted,
            "phase_states": {
                phase: {
                    "turn_count": state.turn_count,
                    "max_turns": state.max_turns,
                    "extension_count": state.extension_count,
                    "converged": state.converged,
                    "approved_by_human": state.approved_by_human,
                    "raw_contributions": state.raw_contributions,
                    "draft_artifact": state.draft_artifact,
                    "artifact": state.artifact,
                }
                for phase, state in self.phase_states.items()
            },
            "transcript": [entry.__dict__ for entry in self.transcript],
        }


def write_transcript_log(meeting_state: MeetingState, logs_dir: Path) -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = logs_dir / f"meeting_transcript_{stamp}.log"
    with path.open("w", encoding="utf-8") as handle:
        for entry in meeting_state.transcript:
            handle.write(
                f"[{entry.timestamp_utc}] TURN {entry.turn} | {entry.phase} | {entry.speaker}\n"
            )
            handle.write(f"{entry.content}\n\n")
    return path
