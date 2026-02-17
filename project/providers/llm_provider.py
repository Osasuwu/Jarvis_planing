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


class LLMProvider(ABC):
    def __init__(self, settings: RuntimeSettings) -> None:
        self.settings = settings

    @abstractmethod
    def build_agent_model_config(self, role: str) -> AgentModelConfig:
        raise NotImplementedError


class CloudProvider(LLMProvider):
    def build_agent_model_config(self, role: str) -> AgentModelConfig:
        model_name = self.settings.model_map.get(role)
        if not model_name:
            raise ValueError(f"No cloud model configured for role '{role}'.")

        # TODO(Q1): Verify final low-cost cloud models for February 2026 in production.
        # ASSUMPTION(Q1): gpt-4.1-mini/nano tier remains available and suitable for this workflow.
        return AgentModelConfig(
            role=role,
            model=model_name,
            config_list=[
                {
                    "model": model_name,
                    "api_key": self.settings.api_key,
                    "base_url": self.settings.base_url,
                }
            ],
            temperature=self.settings.temperature,
            timeout=self.settings.timeout_seconds,
        )


class OllamaProvider(LLMProvider):
    def build_agent_model_config(self, role: str) -> AgentModelConfig:
        model_name = self.settings.model_map.get(role)
        if not model_name:
            raise ValueError(f"No ollama model configured for role '{role}'.")

        return AgentModelConfig(
            role=role,
            model=model_name,
            config_list=[
                {
                    "model": model_name,
                    "api_key": self.settings.api_key or "ollama",
                    "base_url": self.settings.base_url,
                }
            ],
            temperature=self.settings.temperature,
            timeout=self.settings.timeout_seconds,
        )


def provider_factory(settings: RuntimeSettings) -> LLMProvider:
    if settings.provider_name == "cloud":
        return CloudProvider(settings)
    if settings.provider_name == "ollama":
        return OllamaProvider(settings)
    raise ValueError(f"Unsupported provider: {settings.provider_name}")
