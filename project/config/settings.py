from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class RuntimeSettings:
    provider_name: str
    deterministic_mode: bool
    temperature: float
    timeout_seconds: int
    max_turns_per_phase: int
    global_max_turns: int
    output_dir: Path
    logs_dir: Path
    model_map: dict[str, str]
    base_url: str
    api_key: str


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_settings() -> RuntimeSettings:
    root = _project_root()
    load_dotenv(root.parent / ".env")
    config = _read_yaml(root / "config" / "model_config.yaml")

    defaults = config.get("defaults", {})
    configured_provider = os.getenv("MODEL_PROVIDER", defaults.get("provider", "cloud"))
    providers = config.get("providers", {})
    provider_cfg = providers.get(configured_provider)
    if not provider_cfg:
        available = ", ".join(sorted(providers.keys()))
        raise ValueError(f"Unknown provider '{configured_provider}'. Available: {available}")

    api_key_env = provider_cfg.get("api_key_env", "OPENAI_API_KEY")
    api_key = os.getenv(api_key_env, "")

    deterministic_env = os.getenv("DETERMINISTIC_MODE")
    deterministic_mode = (
        deterministic_env.lower() in {"1", "true", "yes", "on"}
        if deterministic_env is not None
        else bool(defaults.get("deterministic_mode", False))
    )

    temperature = 0.0 if deterministic_mode else float(os.getenv("TEMPERATURE", defaults.get("temperature", 0.35)))
    timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", defaults.get("timeout_seconds", 45)))
    max_turns_per_phase = int(os.getenv("MAX_TURNS_PER_PHASE", defaults.get("max_turns_per_phase", 8)))
    global_max_turns = int(os.getenv("GLOBAL_MAX_TURNS", defaults.get("global_max_turns", 48)))

    output_dir = root / os.getenv("OUTPUT_DIR", defaults.get("output_dir", "output"))
    logs_dir = root / os.getenv("LOGS_DIR", defaults.get("logs_dir", "logs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    model_map = provider_cfg.get("models", {})
    base_url = provider_cfg.get("base_url", "")

    return RuntimeSettings(
        provider_name=configured_provider,
        deterministic_mode=deterministic_mode,
        temperature=temperature,
        timeout_seconds=timeout_seconds,
        max_turns_per_phase=max_turns_per_phase,
        global_max_turns=global_max_turns,
        output_dir=output_dir,
        logs_dir=logs_dir,
        model_map=model_map,
        base_url=base_url,
        api_key=api_key,
    )
