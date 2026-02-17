from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from providers.llm_provider import LLMProvider
from prompts.phase_prompts import phase_context_prompt

try:
    from autogen import AssistantAgent
except ImportError as exc:
    raise ImportError(
        "AutoGen is required. Install dependencies from requirements.txt before running."
    ) from exc


@dataclass
class AgentTurn:
    role: str
    phase: str
    content: str


class BaseProjectAgent:
    def __init__(self, role: str, system_prompt: str, provider: LLMProvider) -> None:
        self.role = role
        model_cfg = provider.build_agent_model_config(role)
        self._agent = AssistantAgent(
            name=role,
            system_message=system_prompt,
            llm_config={
                "config_list": model_cfg.config_list,
                "temperature": model_cfg.temperature,
                "timeout": model_cfg.timeout,
            },
        )

    def respond(self, phase: str, facilitator_instruction: str, context_messages: list[dict[str, str]]) -> AgentTurn:
        # TODO(Q2): Confirm target AutoGen package/API compatibility in deployment environment.
        # ASSUMPTION(Q2): AssistantAgent.generate_reply(messages=[...]) is available in installed AutoGen version.
        phase_instruction = phase_context_prompt(phase)
        prompt = (
            f"{phase_instruction}\n"
            f"Facilitator instruction: {facilitator_instruction}\n"
            "Return role-scoped response only."
        )
        response = self._agent.generate_reply(
            messages=context_messages + [{"role": "user", "content": prompt}]
        )
        text = response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)
        return AgentTurn(role=self.role, phase=phase, content=text)
