from __future__ import annotations

import json
from typing import Any

from agents.architect import ArchitectAgent
from agents.backend_engineer import BackendEngineerAgent
from agents.base_agent import BaseProjectAgent
from agents.business_analyst import BusinessAnalystAgent
from agents.devops_engineer import DevOpsEngineerAgent
from agents.facilitator import FacilitatorAgent
from agents.frontend_engineer import FrontendEngineerAgent
from agents.human_stakeholder import HumanStakeholderProxy
from agents.product_manager import ProductManagerAgent
from agents.qa_engineer import QAEngineerAgent
from agents.security_specialist import SecuritySpecialistAgent
from agents.ux_designer import UXDesignerAgent
from config.settings import load_settings
from orchestration.meeting_state import MeetingState, write_transcript_log
from orchestration.phase_manager import PhaseManager
from output.exporter import ProjectPlanExporter
from prompts.phase_prompts import phase_context_prompt
from providers.llm_provider import provider_factory


class WaterfallController:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.phase_manager = PhaseManager()
        self.provider = provider_factory(self.settings)

        self.facilitator = FacilitatorAgent(self.provider)
        self.human = HumanStakeholderProxy()
        self.agents: dict[str, BaseProjectAgent] = {
            "product_manager": ProductManagerAgent(self.provider),
            "business_analyst": BusinessAnalystAgent(self.provider),
            "architect": ArchitectAgent(self.provider),
            "backend_engineer": BackendEngineerAgent(self.provider),
            "frontend_engineer": FrontendEngineerAgent(self.provider),
            "devops_engineer": DevOpsEngineerAgent(self.provider),
            "qa_engineer": QAEngineerAgent(self.provider),
            "ux_designer": UXDesignerAgent(self.provider),
            "security_specialist": SecuritySpecialistAgent(self.provider),
        }

    def run(self) -> None:
        print("=== Waterfall Kickoff Multi-Agent Simulator ===")
        project_name = input("Project name: ").strip() or "Untitled Project"
        project_description = input("Initial project description: ").strip()

        state = MeetingState(
            project_name=project_name,
            project_description=project_description,
            phases=self.phase_manager.phases,
            max_turns_per_phase=self.settings.max_turns_per_phase,
            global_max_turns=self.settings.global_max_turns,
        )

        state.add_transcript("human_stakeholder", project_description)

        try:
            self._run_phases(state)
        except KeyboardInterrupt:
            state.interrupted = True
            print("\nMeeting interrupted by user.")

        exporter = ProjectPlanExporter(self.settings.output_dir)
        markdown_path, json_path = exporter.export(state)
        log_path = write_transcript_log(state, self.settings.logs_dir)

        print("\n=== Meeting completed ===")
        print(f"Markdown plan: {markdown_path}")
        print(f"Structured JSON: {json_path}")
        print(f"Transcript log: {log_path}")

    def _run_phases(self, state: MeetingState) -> None:
        while state.can_continue_meeting():
            phase_name = state.current_phase
            print(f"\n--- Phase: {phase_name} ---")

            converged = self._run_single_phase(state)
            if not converged:
                print(f"Phase '{phase_name}' did not converge within configured turn limit.")
                break

            approved = self._request_human_approval(phase_name)
            state.approve_current_phase(approved)
            if not approved:
                state.phase_states[phase_name].converged = False
                print(f"Phase '{phase_name}' rejected. Continuing discussion in same phase.")
                continue

            if not state.transition_to_next_phase():
                break

    def _run_single_phase(self, state: MeetingState) -> bool:
        while state.can_continue_meeting() and state.can_continue_phase():
            facilitator_decision = self._facilitator_decision(state)
            selected_speaker = facilitator_decision.get("selected_speaker", "business_analyst")
            instruction = facilitator_decision.get("instruction", "Provide concise phase contribution.")

            if selected_speaker == "human_stakeholder":
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
                print(f"[{agent_turn.role}] {agent_turn.content}\n")
                state.add_transcript(agent_turn.role, agent_turn.content)

            if facilitator_decision.get("converged", False):
                artifact = {
                    "phase": state.current_phase,
                    "summary": facilitator_decision.get("phase_summary", ""),
                    "artifact_check": facilitator_decision.get("artifact_check", {}),
                }
                state.mark_phase_converged(artifact)
                print(f"Convergence detected for phase '{state.current_phase}'.")
                print(f"Phase summary: {artifact['summary']}")
                return True

        return False

    def _facilitator_decision(self, state: MeetingState) -> dict[str, Any]:
        phase = state.current_phase
        phase_prompt = phase_context_prompt(phase)
        last_turns = state.transcript[-8:]
        transcript_window = "\n".join(
            f"{entry.speaker}: {entry.content}" for entry in last_turns
        )

        instruction = (
            f"{phase_prompt}\n"
            f"Current phase turn count: {state.phase_states[phase].turn_count}/{state.max_turns_per_phase}\n"
            f"Global turn count: {state.total_turns}/{state.global_max_turns}\n"
            "Use your reasoning to decide next speaker and whether the phase is converged.\n"
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
        print(f"[facilitator] {result.content}\n")

        parsed = self._safe_parse_json(result.content)
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

    @staticmethod
    def _build_context_messages(state: MeetingState) -> list[dict[str, str]]:
        window = state.transcript[-10:]
        return [{"role": "user", "content": f"{entry.speaker}: {entry.content}"} for entry in window]

    @staticmethod
    def _request_human_approval(phase: str) -> bool:
        while True:
            response = input(f"Approve phase '{phase}'? [y/n]: ").strip().lower()
            if response in {"y", "yes"}:
                return True
            if response in {"n", "no"}:
                return False
            print("Please answer 'y' or 'n'.")
