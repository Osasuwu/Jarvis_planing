from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.architect import ArchitectAgent
from agents.backend_engineer import BackendEngineerAgent
from agents.base_agent import BaseProjectAgent
from agents.business_analyst import BusinessAnalystAgent
from agents.devops_engineer import DevOpsEngineerAgent
from project.agents.document_monitor import DocumentMonitorAgent
from agents.facilitator import FacilitatorAgent
from agents.frontend_engineer import FrontendEngineerAgent
from agents.human_stakeholder import HumanStakeholderProxy
from agents.product_manager import ProductManagerAgent
from agents.qa_engineer import QAEngineerAgent
from agents.security_specialist import SecuritySpecialistAgent
from agents.ux_designer import UXDesignerAgent
from config.settings import load_settings
from interaction.channel import CLIChannel, InteractionChannel
from orchestration.meeting_state import MeetingState, write_transcript_log
from orchestration.phase_manager import PhaseManager
from output.exporter import ProjectPlanExporter
from prompts.phase_prompts import phase_context_prompt
from providers.llm_provider import provider_factory


class WaterfallController:
    ROLE_ALIASES: dict[str, str] = {
        "requirements_engineer": "business_analyst",
        "requirement_engineer": "business_analyst",
        "solution_architect": "architect",
        "system_designer": "architect",
        "security_engineer": "security_specialist",
        "devops": "devops_engineer",
        "frontend": "frontend_engineer",
        "backend": "backend_engineer",
        "qa": "qa_engineer",
        "ux": "ux_designer",
        "human": "human_stakeholder",
        "stakeholder": "human_stakeholder",
        "document_writer": "document_monitor",
        "doc_writer": "document_monitor",
        "technical_writer": "document_monitor",
        "formatter": "document_monitor",
        "document_formatter": "document_monitor",
        "document_monitor": "document_monitor",
    }

    def __init__(self, channel: InteractionChannel | None = None) -> None:
        self.settings = load_settings()
        self.phase_manager = PhaseManager()
        self.provider = provider_factory(self.settings)
        self.channel = channel or CLIChannel()
        self.language = self.settings.meeting_language

        self.facilitator = FacilitatorAgent(self.provider, language=self.language)
        self.human = HumanStakeholderProxy(channel=self.channel)
        self.agents: dict[str, BaseProjectAgent] = {
            "product_manager": ProductManagerAgent(self.provider, language=self.language),
            "business_analyst": BusinessAnalystAgent(self.provider, language=self.language),
            "document_monitor": DocumentMonitorAgent(self.provider, language=self.language),
            "architect": ArchitectAgent(self.provider, language=self.language),
            "backend_engineer": BackendEngineerAgent(self.provider, language=self.language),
            "frontend_engineer": FrontendEngineerAgent(self.provider, language=self.language),
            "devops_engineer": DevOpsEngineerAgent(self.provider, language=self.language),
            "qa_engineer": QAEngineerAgent(self.provider, language=self.language),
            "ux_designer": UXDesignerAgent(self.provider, language=self.language),
            "security_specialist": SecuritySpecialistAgent(self.provider, language=self.language),
        }

    def run(self) -> None:
        self.channel.display("=== Waterfall Kickoff Multi-Agent Simulator ===")
        state = self._initialize_or_resume_state()
        self._save_phase_checkpoint(state, reason="session_start")

        try:
            self._run_phases(state)
        except KeyboardInterrupt:
            state.interrupted = True
            self.channel.display("\nMeeting interrupted by user.")
            self._save_phase_checkpoint(state, reason="interrupted")

        exporter = ProjectPlanExporter(self.settings.output_dir)
        finalized = state.is_fully_approved()
        markdown_path, json_path = exporter.export(state, finalized=finalized)
        log_path = write_transcript_log(state, self.settings.logs_dir)

        self.channel.display("\n=== Meeting completed ===")
        if not finalized:
            self.channel.display("Meeting did not complete all approved Waterfall phases.")
            self.channel.display("Exported current plan snapshot with all captured phase artifacts.")
        self.channel.display(f"Markdown plan: {markdown_path}")
        self.channel.display(f"Structured JSON: {json_path}")
        self.channel.display(f"Transcript log: {log_path}")

    def _run_phases(self, state: MeetingState) -> None:
        while state.can_continue_meeting():
            phase_name = state.current_phase
            self.channel.display(f"\n--- Phase: {phase_name} ---")
            if self.settings.new_dialog_per_phase and state.phase_states[phase_name].turn_count == 0:
                self._start_phase_dialogs()

            converged = self._run_single_phase(state)
            if not converged:
                if self._handle_phase_limit_recovery(state):
                    continue
                self.channel.display(f"Phase '{phase_name}' did not converge within configured turn limit.")
                self._save_phase_checkpoint(state, reason="phase_not_converged")
                break

            approved = self._request_human_approval(phase_name)
            state.approve_current_phase(approved)
            if not approved:
                state.phase_states[phase_name].converged = False
                self.channel.display(f"Phase '{phase_name}' rejected. Continuing discussion in same phase.")
                self._save_phase_checkpoint(state, reason="phase_rejected")
                continue

            self._print_phase_recap(state, phase_name)
            self._save_phase_checkpoint(state, reason="phase_approved")

            if not state.transition_to_next_phase():
                self._save_phase_checkpoint(state, reason="all_phases_completed")
                break

    def _run_single_phase(self, state: MeetingState) -> bool:
        while state.can_continue_meeting() and state.can_continue_phase():
            facilitator_decision = self._facilitator_decision(state)
            readiness_score = int(facilitator_decision.get("readiness_score", 0))

            missing_required_roles = self._missing_required_roles_for_phase(state)
            if facilitator_decision.get("converged", False) and missing_required_roles:
                facilitator_decision["converged"] = False
                facilitator_decision["selected_speaker"] = missing_required_roles[0]
                facilitator_decision["instruction"] = self._missing_role_instruction(missing_required_roles[0])
                self.channel.display(
                    "[Guardrail] Convergence blocked: required specialist perspectives still missing "
                    f"for phase '{state.current_phase}': {', '.join(missing_required_roles)}"
                )

            selected_speaker = facilitator_decision.get("selected_speaker", "business_analyst")
            selected_speaker = self._resolve_selected_speaker(state, selected_speaker)
            instruction = facilitator_decision.get("instruction", "Provide concise phase contribution.")

            if self._needs_document_monitor(state.current_phase, selected_speaker, instruction):
                selected_speaker = "document_monitor"
                self.channel.display(
                    "[Guardrail] Documentation monitoring/structuring task detected; rerouting to document_monitor."
                )

            if missing_required_roles and selected_speaker not in missing_required_roles and selected_speaker != "human_stakeholder":
                selected_speaker = missing_required_roles[0]
                instruction = self._missing_role_instruction(selected_speaker)
                self.channel.display(
                    "[Guardrail] Prioritizing missing required role before further iteration: "
                    f"{selected_speaker}"
                )

            if self._should_auto_extend_phase(state, readiness_score):
                extended = state.extend_current_phase_turn_limit(5)
                if extended:
                    self.channel.display(
                        f"[Guardrail] Low convergence readiness ({readiness_score}) near cap; "
                        f"auto-extended phase '{state.current_phase}' by 5 turns "
                        f"to {state.phase_states[state.current_phase].max_turns}."
                    )

            if self._should_force_human_checkpoint(state, selected_speaker, readiness_score):
                selected_speaker = "human_stakeholder"
                instruction = (
                    "Please review the current phase draft artifact, confirm what is acceptable, "
                    "and list any final must-have corrections before convergence."
                )
                self.channel.display(
                    "[Guardrail] Near phase turn limit; routing next turn to human for checkpoint review."
                )

            if selected_speaker == "human_stakeholder":
                self._print_phase_draft_for_human(state)
                response = self.human.respond(instruction)
                state.add_transcript("human_stakeholder", response)
            else:
                if not self.phase_manager.is_role_allowed(state.current_phase, selected_speaker):
                    selected_speaker = self.phase_manager.fallback_role_for_phase(state.current_phase)

                agent = self.agents[selected_speaker]
                context_messages = self._build_context_messages(state)
                agent_turn = agent.respond(
                    phase=state.current_phase,
                    facilitator_instruction=instruction,
                    context_messages=context_messages,
                )
                self._print_role_turn(agent_turn.role, agent_turn.content)
                state.add_transcript(agent_turn.role, agent_turn.content)
                parsed_agent_payload = self._safe_parse_json(agent_turn.content)
                if parsed_agent_payload:
                    state.update_phase_draft(parsed_agent_payload)

            if facilitator_decision.get("converged", False):
                phase_state = state.phase_states[state.current_phase]
                artifact = {
                    "phase": state.current_phase,
                    "summary": facilitator_decision.get("phase_summary", ""),
                    "artifact_check": facilitator_decision.get("artifact_check", {}),
                    "document": phase_state.draft_artifact,
                }
                state.mark_phase_converged(artifact)
                self.channel.display(f"Convergence detected for phase '{state.current_phase}'.")
                self.channel.display(f"Phase summary: {artifact['summary']}")
                return True

        return False

    @staticmethod
    def _needs_document_monitor(phase: str, selected_speaker: str, instruction: str) -> bool:
        if phase != "Requirements Gathering":
            return False
        if selected_speaker == "document_monitor":
            return False

        text = (instruction or "").lower()
        formatting_markers = (
            "format",
            "formatted",
            "reformat",
            "structure",
            "structured",
            "consolidat",
            "specification",
            "coverage",
            "completeness",
            "undercovered",
            "finalize document",
            "оформ",
            "структур",
            "консолид",
            "спецификац",
            "документ",
            "полнот",
            "покрыти",
            "упущен",
        )
        return any(marker in text for marker in formatting_markers)

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower())
        return slug.strip("_") or "project"

    def _checkpoint_dir(self) -> Path:
        path = self.settings.output_dir / "checkpoints"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _save_phase_checkpoint(self, state: MeetingState, reason: str) -> Path:
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        phase_no = state.current_phase_index + 1
        filename = (
            f"meeting_checkpoint_{self._slugify(state.project_name)}_"
            f"p{phase_no:02d}_{reason}_{stamp}.json"
        )
        path = self._checkpoint_dir() / filename
        payload = state.to_json()
        payload["checkpoint_reason"] = reason
        payload["checkpoint_created_utc"] = datetime.utcnow().isoformat()
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        self.channel.display(f"[Checkpoint] Saved: {path}")
        return path

    def _list_checkpoint_files(self) -> list[Path]:
        checkpoint_paths = sorted(
            self._checkpoint_dir().glob("meeting_checkpoint_*.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        if checkpoint_paths:
            return checkpoint_paths

        legacy = sorted(
            self.settings.output_dir.glob("project_development_*.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        return legacy

    def _pick_checkpoint_file(self) -> Path | None:
        checkpoints = self._list_checkpoint_files()
        if not checkpoints:
            self.channel.display("No checkpoints found; starting a new meeting.")
            return None

        self.channel.display("Available checkpoints:")
        preview = checkpoints[:12]
        for index, path in enumerate(preview, start=1):
            self.channel.display(f"  {index}. {path.name}")

        raw_choice = self.channel.prompt_text(
            f"Select checkpoint number (1-{len(preview)}) or press Enter for latest: "
        ).strip()
        if not raw_choice:
            return preview[0]
        try:
            chosen = int(raw_choice)
        except ValueError:
            self.channel.display("Invalid selection; using latest checkpoint.")
            return preview[0]
        if chosen < 1 or chosen > len(preview):
            self.channel.display("Selection out of range; using latest checkpoint.")
            return preview[0]
        return preview[chosen - 1]

    def _prompt_resume_phase(self, state: MeetingState) -> int:
        self.channel.display("Phases available for resume:")
        for index, phase_name in enumerate(state.phases, start=1):
            phase_state = state.phase_states[phase_name]
            marker = "[current]" if index - 1 == state.current_phase_index else ""
            self.channel.display(
                f"  {index}. {phase_name} {marker} | turns={phase_state.turn_count} "
                f"| converged={phase_state.converged} | approved={phase_state.approved_by_human}"
            )

        raw_choice = self.channel.prompt_text(
            f"Choose phase to continue from (1-{len(state.phases)}) or Enter for current phase: "
        ).strip()
        if not raw_choice:
            return state.current_phase_index
        try:
            value = int(raw_choice)
        except ValueError:
            self.channel.display("Invalid phase number; using current phase.")
            return state.current_phase_index
        if value < 1 or value > len(state.phases):
            self.channel.display("Phase out of range; using current phase.")
            return state.current_phase_index
        return value - 1

    def _initialize_or_resume_state(self) -> MeetingState:
        resume = self.channel.prompt_yes_no("Resume from saved checkpoint? [y/n]: ")
        if resume:
            selected = self._pick_checkpoint_file()
            if selected is not None:
                try:
                    with selected.open("r", encoding="utf-8") as handle:
                        payload = json.load(handle)
                    state = MeetingState.from_json(payload)
                    state.interrupted = False
                    self.channel.display(f"Loaded checkpoint: {selected}")
                    phase_index = self._prompt_resume_phase(state)
                    if phase_index != state.current_phase_index:
                        state.resume_from_phase(phase_index)
                        self.channel.display(f"Resumed from phase: {state.current_phase}")
                    return state
                except Exception as exc:
                    self.channel.display(f"Failed to load checkpoint ({exc}). Starting a new meeting.")

        project_name = self.channel.prompt_text("Project name: ").strip() or "Untitled Project"
        project_description = self.channel.prompt_text("Initial project description: ").strip()
        state = MeetingState(
            project_name=project_name,
            project_description=project_description,
            meeting_language=self.language,
            phases=self.phase_manager.phases,
            max_turns_per_phase=self.settings.max_turns_per_phase,
            global_max_turns=self.settings.global_max_turns,
        )
        state.add_transcript("human_stakeholder", project_description)
        return state

    def _missing_required_roles_for_phase(self, state: MeetingState) -> list[str]:
        required_roles = self.phase_manager.required_roles_for_phase(state.current_phase)
        if not required_roles:
            return []

        phase_entries = [entry for entry in state.transcript if entry.phase == state.current_phase]
        spoken_roles = {entry.speaker for entry in phase_entries if entry.speaker not in {"facilitator", "human_stakeholder"}}
        return [role for role in required_roles if role not in spoken_roles]

    @staticmethod
    def _missing_role_instruction(role: str) -> str:
        return (
            f"Provide your role-specific perspective for this phase and include key decisions, "
            f"risks, and compromises from the viewpoint of {role}."
        )

    def _handle_phase_limit_recovery(self, state: MeetingState) -> bool:
        if state.phase_states[state.current_phase].converged:
            return True

        prompt = (
            f"Phase '{state.current_phase}' reached its turn limit "
            f"({state.phase_states[state.current_phase].max_turns}). "
            "Extend this phase by 10 turns and continue?"
        )
        extend = self.channel.prompt_yes_no(prompt)
        if not extend:
            return False

        extended = state.extend_current_phase_turn_limit(10)
        if not extended:
            self.channel.display(
                f"Phase '{state.current_phase}' reached max extension limit."
            )
            return False
        self.channel.display(
            f"Turn limit for phase '{state.current_phase}' extended to "
            f"{state.phase_states[state.current_phase].max_turns}."
        )
        return True

    def _facilitator_decision(self, state: MeetingState) -> dict[str, Any]:
        phase = state.current_phase
        phase_prompt = phase_context_prompt(phase, language=self.language)
        allowed_roles = self.phase_manager.allowed_roles_for_phase(phase)
        if self.settings.smart_forgetting:
            phase_transcript = [entry for entry in state.transcript if entry.phase == phase]
            last_turns = phase_transcript[-8:]
        else:
            last_turns = state.transcript[-8:]
        transcript_window = "\n".join(
            f"{entry.speaker}: {entry.content}" for entry in last_turns
        )

        instruction = (
            f"{phase_prompt}\n"
            f"Current phase turn count: {state.phase_states[phase].turn_count}/{state.max_turns_per_phase}\n"
            f"Global turn count: {state.total_turns}/{state.global_max_turns}\n"
            f"Allowed speakers for this phase: {', '.join(allowed_roles)}\n"
            "Select selected_speaker ONLY from allowed speakers above (or human_stakeholder).\n"
            "Use your reasoning to decide next speaker and whether the phase is converged.\n"
            "Provide readiness_score (0-100) indicating how close this phase is to converged and review-ready.\n"
            "Recent transcript:\n"
            f"{transcript_window}"
        )
        context_messages = self._build_context_messages(state)
        result = self.facilitator.respond(
            phase=phase,
            facilitator_instruction=instruction,
            context_messages=context_messages,
        )
        state.add_transcript("facilitator", result.content)

        parsed = self._safe_parse_json(result.content)
        if "readiness_score" not in parsed:
            parsed["readiness_score"] = self._estimate_readiness(parsed, state)
        self._print_facilitator_turn(parsed, result.content)
        if "selected_speaker" not in parsed:
            parsed["selected_speaker"] = self.phase_manager.fallback_role_for_phase(phase)
        if "instruction" not in parsed:
            parsed["instruction"] = "Provide concise phase contribution for convergence."
        return parsed

    @staticmethod
    def _safe_parse_json(raw_text: str) -> dict[str, Any]:
        raw_text = raw_text.strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(raw_text[start : end + 1])
                except json.JSONDecodeError:
                    return {}
            return {}

    def _compact_phase_memory(self, state: MeetingState) -> str:
        if self.settings.phase_memory_limit <= 0:
            return ""

        current_index = state.current_phase_index
        phase_names = state.phases[max(0, current_index - self.settings.phase_memory_limit):current_index]
        memory_lines: list[str] = []
        for phase_name in phase_names:
            phase_state = state.phase_states[phase_name]
            artifact = phase_state.artifact
            if not isinstance(artifact, dict) or not artifact:
                continue
            summary = str(artifact.get("summary", "")).strip()
            document = artifact.get("document", {})
            doc_keys = []
            if isinstance(document, dict):
                doc_keys = list(document.keys())[:6]
            sections_text = ", ".join(doc_keys) if doc_keys else "(none)"
            memory_lines.append(
                f"- {phase_name}: summary='{summary[:240]}', sections={sections_text}"
            )

        if not memory_lines:
            return ""

        return (
            "Compressed memory from earlier approved phases (for continuity only, do not restate verbatim):\n"
            + "\n".join(memory_lines)
        )

    def _build_context_messages(self, state: MeetingState) -> list[dict[str, str]]:
        if self.settings.smart_forgetting:
            phase_entries = [entry for entry in state.transcript if entry.phase == state.current_phase]
            window = phase_entries[-self.settings.context_window_turns :]
        else:
            window = state.transcript[-max(10, self.settings.context_window_turns) :]

        messages: list[dict[str, str]] = []
        memory = self._compact_phase_memory(state)
        if memory:
            messages.append({"role": "user", "content": memory})
        messages.extend(
            {"role": "user", "content": f"{entry.speaker}: {entry.content}"}
            for entry in window
        )
        return messages

    def _start_phase_dialogs(self) -> None:
        self.facilitator.start_new_dialog()
        for agent in self.agents.values():
            agent.start_new_dialog()

    def _print_phase_draft_for_human(self, state: MeetingState) -> None:
        draft = state.phase_states[state.current_phase].draft_artifact
        if not draft:
            self.channel.display("\n[Info] No consolidated phase artifact is currently available for review yet.")
            return

        self.channel.display("\n[Phase Artifact Snapshot For Review]")
        self.channel.display(WaterfallController._render_human_readable_payload(draft))

    def _print_facilitator_turn(self, parsed: dict[str, Any], raw_content: str) -> None:
        if not parsed:
            self.channel.display(f"[facilitator] {raw_content}\n")
            return

        self.channel.display("[facilitator]")
        selected = parsed.get("selected_speaker", "(not specified)")
        instruction = parsed.get("instruction", "(no instruction)")
        converged = bool(parsed.get("converged", False))
        reason = parsed.get("convergence_reason", "")
        readiness_score = int(parsed.get("readiness_score", 0))
        self.channel.display(f"- Next speaker: {selected}")
        self.channel.display(f"- Instruction: {instruction}")
        self.channel.display(f"- Convergence readiness: {readiness_score}/100")

        artifact_check = parsed.get("artifact_check", {})
        if isinstance(artifact_check, dict):
            complete = artifact_check.get("complete")
            if complete is not None:
                self.channel.display(f"- Artifact completeness: {complete}")
            missing_items = artifact_check.get("missing_items", [])
            if isinstance(missing_items, list) and missing_items:
                self.channel.display("- Missing items before convergence:")
                for item in missing_items:
                    self.channel.display(f"  - {item}")

        self.channel.display(f"- Converged: {converged}")
        if reason:
            self.channel.display(f"- Convergence reason: {reason}")
        self.channel.display("")

    def _print_role_turn(self, role: str, raw_content: str) -> None:
        parsed = WaterfallController._safe_parse_json(raw_content)
        self.channel.display(f"[{role}]")
        if not parsed:
            self.channel.display(raw_content)
            self.channel.display("")
            return

        self.channel.display(WaterfallController._render_human_readable_payload(parsed))
        self.channel.display("")

    @staticmethod
    def _render_human_readable_payload(payload: Any, level: int = 0) -> str:
        indent = "  " * level
        if isinstance(payload, dict):
            lines: list[str] = []
            for key, value in payload.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{indent}- {key}:")
                    lines.append(WaterfallController._render_human_readable_payload(value, level + 1))
                else:
                    lines.append(f"{indent}- {key}: {value}")
            return "\n".join(lines)

        if isinstance(payload, list):
            lines = []
            for item in payload:
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent}-")
                    lines.append(WaterfallController._render_human_readable_payload(item, level + 1))
                else:
                    lines.append(f"{indent}- {item}")
            return "\n".join(lines) if lines else f"{indent}- (none)"

        return f"{indent}{payload}"

    def _print_phase_recap(self, state: MeetingState, phase_name: str) -> None:
        phase_state = state.phase_states[phase_name]
        artifact = phase_state.artifact
        summary = artifact.get("summary", "") if isinstance(artifact, dict) else ""
        self.channel.display(f"\n=== Phase Recap: {phase_name} ===")
        self.channel.display(f"Approved by human: {phase_state.approved_by_human}")
        self.channel.display(f"Converged: {phase_state.converged}")
        if summary:
            self.channel.display(f"Summary: {summary}")

        artifact_doc = artifact.get("document", {}) if isinstance(artifact, dict) else {}
        if isinstance(artifact_doc, dict) and artifact_doc:
            self.channel.display("Key artifact sections:")
            for key, value in artifact_doc.items():
                if isinstance(value, list):
                    self.channel.display(f"- {key}: {len(value)} items")
                elif isinstance(value, dict):
                    self.channel.display(f"- {key}: {len(value.keys())} fields")
                else:
                    self.channel.display(f"- {key}: included")
        self.channel.display("===============================\n")

    def _request_human_approval(self, phase: str) -> bool:
        return self.channel.prompt_yes_no(f"Approve phase '{phase}'")

    def _resolve_selected_speaker(self, state: MeetingState, selected_speaker: str) -> str:
        normalized = (selected_speaker or "").strip().lower()
        normalized = normalized.replace(" ", "_")
        normalized = self.ROLE_ALIASES.get(normalized, normalized)

        if normalized == "human_stakeholder":
            return normalized

        if self.phase_manager.is_role_allowed(state.current_phase, normalized):
            return normalized

        fallback = self.phase_manager.fallback_role_for_phase(state.current_phase)
        self.channel.display(
            f"[Guardrail] Facilitator selected invalid role '{selected_speaker}'. "
            f"Using '{fallback}' for phase '{state.current_phase}'."
        )
        return fallback

    @staticmethod
    def _should_force_human_checkpoint(state: MeetingState, selected_speaker: str, readiness_score: int) -> bool:
        if selected_speaker == "human_stakeholder":
            return False

        phase_state = state.phase_states[state.current_phase]
        remaining_turns = phase_state.max_turns - phase_state.turn_count
        if remaining_turns > 2:
            return False

        if readiness_score < 65:
            return False

        recent_in_phase = [
            entry for entry in reversed(state.transcript)
            if entry.phase == state.current_phase and entry.speaker != "facilitator"
        ][:2]
        if len(recent_in_phase) < 2:
            return False

        return all(entry.speaker != "human_stakeholder" for entry in recent_in_phase)

    @staticmethod
    def _should_auto_extend_phase(state: MeetingState, readiness_score: int) -> bool:
        phase_state = state.phase_states[state.current_phase]
        remaining_turns = phase_state.max_turns - phase_state.turn_count
        if remaining_turns > 1:
            return False
        return readiness_score < 55 and phase_state.extension_count < 3

    @staticmethod
    def _estimate_readiness(parsed: dict[str, Any], state: MeetingState) -> int:
        artifact_check = parsed.get("artifact_check", {})
        if not isinstance(artifact_check, dict):
            artifact_check = {}
        missing_items = artifact_check.get("missing_items", [])
        if not isinstance(missing_items, list):
            missing_items = []

        completeness_bonus = 35 if artifact_check.get("complete") else 0
        missing_penalty = min(len(missing_items) * 12, 60)

        phase_state = state.phase_states[state.current_phase]
        progress_ratio = phase_state.turn_count / max(phase_state.max_turns, 1)
        progress_bonus = int(min(progress_ratio, 1.0) * 30)

        base = 25 + completeness_bonus + progress_bonus - missing_penalty
        return max(0, min(100, base))
