from __future__ import annotations

from dataclasses import dataclass

from providers.llm_adapter import AutoGenAdapter
from providers.llm_provider import LLMProvider
from prompts.phase_prompts import phase_context_prompt


@dataclass
class AgentTurn:
    role: str
    phase: str
    content: str


class BaseProjectAgent:
    def __init__(self, role: str, system_prompt: str, provider: LLMProvider) -> None:
        self.role = role
        model_cfg = provider.build_agent_model_config(role)
        self._adapter = AutoGenAdapter(name=role, system_prompt=system_prompt, model_cfg=model_cfg)

    def respond(self, phase: str, facilitator_instruction: str, context_messages: list[dict[str, str]]) -> AgentTurn:
        phase_instruction = phase_context_prompt(phase)
        prompt = (
            f"{phase_instruction}\n"
            f"Facilitator instruction: {facilitator_instruction}\n"
            "Return role-scoped response only."
        )
        text = self._adapter.reply(messages=context_messages + [{"role": "user", "content": prompt}])
        return AgentTurn(role=self.role, phase=phase, content=text)
