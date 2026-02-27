from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class ProviderSettings:
    name: str
    vendor: str
    base_url: str
    api_key: str
    model_map: dict[str, str]


@dataclass(frozen=True)
class RuntimeSettings:
    provider_name: str
    backup_provider_names: tuple[str, ...]
    meeting_language: str
    deterministic_mode: bool
    temperature: float
    timeout_seconds: int
    retry_attempts: int
    retry_backoff_seconds: float
    new_dialog_per_phase: bool
    smart_forgetting: bool
    context_window_turns: int
    phase_memory_limit: int
    max_turns_per_phase: int
    global_max_turns: int
    output_dir: Path
    logs_dir: Path
    model_map: dict[str, str]
    base_url: str
    api_key: str
    providers: dict[str, ProviderSettings]
    provider_chain: tuple[str, ...]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _to_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_backup_providers(raw: str | None, defaults: dict[str, Any]) -> list[str]:
    if raw:
        return [item.strip() for item in raw.split(",") if item.strip()]
    configured = defaults.get("backup_providers", [])
    if not isinstance(configured, list):
        return []
    return [str(item).strip() for item in configured if str(item).strip()]


def load_settings() -> RuntimeSettings:
    root = _project_root()
    load_dotenv(root.parent / ".env")
    config = _read_yaml(root / "config" / "model_config.yaml")

    defaults = config.get("defaults", {})
    configured_provider = os.getenv("MODEL_PROVIDER", defaults.get("provider", "cloud"))
    meeting_language = os.getenv("MEETING_LANGUAGE", "en").strip().lower()
    if meeting_language not in {"en", "ru"}:
        raise ValueError("MEETING_LANGUAGE must be 'en' or 'ru'.")
    providers = config.get("providers", {})
    provider_cfg = providers.get(configured_provider)
    if not provider_cfg:
        available = ", ".join(sorted(providers.keys()))
        raise ValueError(f"Unknown provider '{configured_provider}'. Available: {available}")

    backup_provider_names = _parse_backup_providers(os.getenv("BACKUP_MODEL_PROVIDERS"), defaults)
    backup_provider_names = [name for name in backup_provider_names if name != configured_provider]
    unknown_backups = [name for name in backup_provider_names if name not in providers]
    if unknown_backups:
        available = ", ".join(sorted(providers.keys()))
        unknown = ", ".join(sorted(unknown_backups))
        raise ValueError(f"Unknown backup provider(s): {unknown}. Available: {available}")

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
    retry_attempts = int(os.getenv("RETRY_ATTEMPTS", defaults.get("retry_attempts", 2)))
    retry_backoff_seconds = float(os.getenv("RETRY_BACKOFF_SECONDS", defaults.get("retry_backoff_seconds", 1.4)))
    new_dialog_per_phase = _to_bool(os.getenv("NEW_DIALOG_PER_PHASE"), _to_bool(defaults.get("new_dialog_per_phase"), True))
    smart_forgetting = _to_bool(os.getenv("SMART_FORGETTING"), _to_bool(defaults.get("smart_forgetting"), True))
    context_window_turns = int(os.getenv("CONTEXT_WINDOW_TURNS", defaults.get("context_window_turns", 6)))
    phase_memory_limit = int(os.getenv("PHASE_MEMORY_LIMIT", defaults.get("phase_memory_limit", 2)))
    max_turns_per_phase = int(os.getenv("MAX_TURNS_PER_PHASE", defaults.get("max_turns_per_phase", 16)))
    global_max_turns = int(os.getenv("GLOBAL_MAX_TURNS", defaults.get("global_max_turns", 140)))

    output_dir = root / os.getenv("OUTPUT_DIR", defaults.get("output_dir", "output"))
    logs_dir = root / os.getenv("LOGS_DIR", defaults.get("logs_dir", "logs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    model_map = provider_cfg.get("models", {})
    base_url = provider_cfg.get("base_url", "")

    provider_chain = tuple([configured_provider, *backup_provider_names])
    provider_settings: dict[str, ProviderSettings] = {}
    for name in provider_chain:
        cfg = providers[name]
        key_env = cfg.get("api_key_env", "OPENAI_API_KEY")
        provider_settings[name] = ProviderSettings(
            name=name,
            vendor=cfg.get("vendor", "unknown"),
            base_url=cfg.get("base_url", ""),
            api_key=os.getenv(key_env, ""),
            model_map=cfg.get("models", {}),
        )

    return RuntimeSettings(
        provider_name=configured_provider,
        backup_provider_names=tuple(backup_provider_names),
        meeting_language=meeting_language,
        deterministic_mode=deterministic_mode,
        temperature=temperature,
        timeout_seconds=timeout_seconds,
        retry_attempts=max(1, retry_attempts),
        retry_backoff_seconds=max(0.1, retry_backoff_seconds),
        new_dialog_per_phase=new_dialog_per_phase,
        smart_forgetting=smart_forgetting,
        context_window_turns=max(2, context_window_turns),
        phase_memory_limit=max(0, phase_memory_limit),
        max_turns_per_phase=max_turns_per_phase,
        global_max_turns=global_max_turns,
        output_dir=output_dir,
        logs_dir=logs_dir,
        model_map=model_map,
        base_url=base_url,
        api_key=api_key,
        providers=provider_settings,
        provider_chain=provider_chain,
    )
