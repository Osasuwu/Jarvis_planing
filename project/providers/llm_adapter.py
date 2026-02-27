from __future__ import annotations

import json
import time

from providers.llm_provider import AgentModelConfig

try:
    from autogen import AssistantAgent
except ImportError as exc:
    raise ImportError(
        "AutoGen is required. Install dependencies from requirements.txt before running."
    ) from exc


class AutoGenAdapter:
    def __init__(self, name: str, system_prompt: str, model_cfg: AgentModelConfig) -> None:
        self._name = name
        self._system_prompt = system_prompt
        self._temperature = model_cfg.temperature
        self._timeout = model_cfg.timeout
        self._provider_configs = model_cfg.config_list
        self._retry_attempts = model_cfg.retry_attempts
        self._retry_backoff_seconds = model_cfg.retry_backoff_seconds
        self._active_provider_index = 0
        self._agent = self._build_agent(self._active_provider_index)

    def _build_agent(self, provider_index: int) -> AssistantAgent:
        config = self._provider_configs[provider_index]
        return AssistantAgent(
            name=self._name,
            system_message=self._system_prompt,
            llm_config={
                "config_list": [config],
                "temperature": self._temperature,
                "timeout": self._timeout,
            },
        )

    def start_new_dialog(self) -> None:
        self._agent = self._build_agent(self._active_provider_index)

    @staticmethod
    def _is_retryable_error(exc: Exception) -> bool:
        text = str(exc).lower()
        markers = (
            "timed out",
            "timeout",
            "readtimeout",
            "read timeout",
            "rate limit",
            "429",
            "temporarily unavailable",
            "service unavailable",
            "connection",
            "network",
            "overloaded",
        )
        return any(marker in text for marker in markers)

    @staticmethod
    def _is_quota_error(exc: Exception) -> bool:
        text = str(exc).lower()
        markers = (
            "insufficient_quota",
            "insufficient quota",
            "quota",
            "credit",
            "billing",
            "payment required",
        )
        return any(marker in text for marker in markers)

    def reply(self, messages: list[dict[str, str]]) -> str:
        failures: list[str] = []
        provider_count = len(self._provider_configs)

        for provider_offset in range(provider_count):
            provider_index = (self._active_provider_index + provider_offset) % provider_count
            provider_name = self._provider_configs[provider_index].get("provider_name", f"provider_{provider_index}")
            self._agent = self._build_agent(provider_index)

            for attempt in range(1, self._retry_attempts + 1):
                try:
                    response = self._agent.generate_reply(messages=messages)
                    self._active_provider_index = provider_index
                    return response if isinstance(response, str) else json.dumps(response, ensure_ascii=False)
                except Exception as exc:
                    failures.append(f"{provider_name} attempt {attempt}: {exc}")
                    if self._is_quota_error(exc):
                        break

                    retryable = self._is_retryable_error(exc)
                    if retryable and attempt < self._retry_attempts:
                        delay = self._retry_backoff_seconds * attempt
                        time.sleep(delay)
                        continue
                    break

        error_summary = " | ".join(failures[-6:]) if failures else "No provider attempts recorded"
        raise TimeoutError(f"All providers failed to generate a reply. {error_summary}")
