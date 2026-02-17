from __future__ import annotations

import json

from providers.llm_provider import AgentModelConfig

try:
    from autogen import AssistantAgent
except ImportError as exc:
    raise ImportError(
        "AutoGen is required. Install dependencies from requirements.txt before running."
    ) from exc


class AutoGenAdapter:
    def __init__(self, name: str, system_prompt: str, model_cfg: AgentModelConfig) -> None:
        self._agent = AssistantAgent(
            name=name,
            system_message=system_prompt,
            llm_config={
                "config_list": model_cfg.config_list,
                "temperature": model_cfg.temperature,
                "timeout": model_cfg.timeout,
            },
        )

    def reply(self, messages: list[dict[str, str]]) -> str:
        response = self._agent.generate_reply(messages=messages)
        return response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)
