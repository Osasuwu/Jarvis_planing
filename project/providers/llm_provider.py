from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from config.settings import RuntimeSettings


@dataclass(frozen=True)
class AgentModelConfig:
    role: str
    model: str
    config_list: list[dict[str, str]]
    temperature: float
    timeout: int
    retry_attempts: int
    retry_backoff_seconds: float


class LLMProvider(ABC):
    def __init__(self, settings: RuntimeSettings) -> None:
        self.settings = settings

    @abstractmethod
    def build_agent_model_config(self, role: str) -> AgentModelConfig:
        raise NotImplementedError


class CloudProvider(LLMProvider):
    def build_agent_model_config(self, role: str) -> AgentModelConfig:
        config_list: list[dict[str, str]] = []
        first_model = ""
        for provider_name in self.settings.provider_chain:
            provider_settings = self.settings.providers[provider_name]
            model_name = provider_settings.model_map.get(role)
            if not model_name:
                continue

            api_key = provider_settings.api_key
            if provider_settings.vendor == "ollama" and not api_key:
                api_key = "ollama"
            if provider_settings.vendor != "ollama" and not api_key:
                continue

            if not first_model:
                first_model = model_name

            config_list.append(
                {
                    "model": model_name,
                    "api_key": api_key,
                    "base_url": provider_settings.base_url,
                    "provider_name": provider_name,
                }
            )

        if not config_list:
            providers = ", ".join(self.settings.provider_chain)
            raise ValueError(f"No model configured for role '{role}' across providers: {providers}.")

        return AgentModelConfig(
            role=role,
            model=first_model,
            config_list=config_list,
            temperature=self.settings.temperature,
            timeout=self.settings.timeout_seconds,
            retry_attempts=self.settings.retry_attempts,
            retry_backoff_seconds=self.settings.retry_backoff_seconds,
        )


class OllamaProvider(LLMProvider):
    def build_agent_model_config(self, role: str) -> AgentModelConfig:
        return CloudProvider(self.settings).build_agent_model_config(role)


def provider_factory(settings: RuntimeSettings) -> LLMProvider:
    configured = settings.providers.get(settings.provider_name)
    if not configured:
        raise ValueError(f"Unsupported provider: {settings.provider_name}")

    if configured.vendor == "ollama":
        return OllamaProvider(settings)
    return CloudProvider(settings)
