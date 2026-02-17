from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


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
    turn_count: int = 0
    converged: bool = False
    artifact: dict[str, Any] = field(default_factory=dict)
    approved_by_human: bool = False


@dataclass
class MeetingState:
    project_name: str
    project_description: str
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
        self.phase_states = {name: PhaseState(name=name) for name in self.phases}

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
        return self.phase_states[self.current_phase].turn_count < self.max_turns_per_phase

    def can_continue_meeting(self) -> bool:
        return self.total_turns < self.global_max_turns and not self.interrupted

    def mark_phase_converged(self, artifact: dict[str, Any]) -> None:
        phase_state = self.phase_states[self.current_phase]
        phase_state.converged = True
        phase_state.artifact = artifact

    def approve_current_phase(self, approved: bool) -> None:
        self.phase_states[self.current_phase].approved_by_human = approved

    def transition_to_next_phase(self) -> bool:
        if self.current_phase_index + 1 >= len(self.phases):
            return False
        self.current_phase_index += 1
        return True

    def to_json(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "project_description": self.project_description,
            "session_started_utc": self.session_started_utc,
            "current_phase": self.current_phase,
            "current_phase_index": self.current_phase_index,
            "max_turns_per_phase": self.max_turns_per_phase,
            "global_max_turns": self.global_max_turns,
            "total_turns": self.total_turns,
            "interrupted": self.interrupted,
            "phase_states": {
                phase: {
                    "turn_count": state.turn_count,
                    "converged": state.converged,
                    "approved_by_human": state.approved_by_human,
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
