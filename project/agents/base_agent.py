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
    def __init__(self, role: str, system_prompt: str, provider: LLMProvider, language: str = "en") -> None:
        self.role = role
        self.language = language
        model_cfg = provider.build_agent_model_config(role)
        self._adapter = AutoGenAdapter(name=role, system_prompt=system_prompt, model_cfg=model_cfg)

    def start_new_dialog(self) -> None:
        self._adapter.start_new_dialog()

    def respond(self, phase: str, facilitator_instruction: str, context_messages: list[dict[str, str]]) -> AgentTurn:
        phase_instruction = phase_context_prompt(phase, language=self.language)
        language_instruction = (
            "All natural-language values in your JSON response MUST be in English."
            if self.language == "en"
            else "Все текстовые значения в JSON-ответе ДОЛЖНЫ быть на русском языке, даже если входной контекст на английском."
        )
        prompt = (
            f"{phase_instruction}\n"
            f"{language_instruction}\n"
            f"Facilitator instruction: {facilitator_instruction}\n"
            "Return role-scoped response only."
        )
        text = self._adapter.reply(messages=context_messages + [{"role": "user", "content": prompt}])
        return AgentTurn(role=self.role, phase=phase, content=text)
