# Waterfall Kickoff Multi-Agent Simulator (AutoGen)

Python CLI system that simulates a real-world IT project kickoff meeting in strict Waterfall order and generates a complete Project Development Plan in Markdown + JSON.

## Features

- Python 3.11+ CLI app (no GUI)
- AutoGen-based role agents with strict role boundaries
- Facilitator-controlled turn-taking and convergence detection
- Strict phase enforcement:
	1. Requirements Gathering
	2. System Design
	3. Implementation Planning
	4. Testing Strategy
	5. Deployment Planning
	6. Maintenance Strategy
- Human stakeholder participation (interactive CLI proxy)
- Human approval gate before phase transition
- Phase checkpoints saved during meeting flow, with resume-from-phase support
- Deterministic mode support (temperature override)
- Global/phase turn limits and loop prevention
- Multi-provider fallback chain (provider1 -> provider2 -> ... -> ollama)
- Human-readable CLI rendering of structured agent outputs
- Bilingual meeting instructions for agents (`en`/`ru`) via environment switch
- Phase-specific artifact schemas per Waterfall phase (instead of generic role payloads)
- Convergence readiness score (0-100) with pre-cap guardrails
- Full transcript logging
- Dedicated document monitor role for requirements/spec structuring and phase coverage completeness checks
- Structured outputs:
	- Markdown project plan
	- JSON machine-readable plan/session data

## Project Structure

```text
project/
├── main.py
├── main_ui.py
├── config/
│   ├── model_config.yaml
│   └── settings.py
├── interaction/
│   └── channel.py
├── providers/
│   ├── llm_provider.py
│   └── llm_adapter.py
├── agents/
│   ├── base_agent.py
│   ├── facilitator.py
│   ├── product_manager.py
│   ├── business_analyst.py
│   ├── architect.py
│   ├── backend_engineer.py
│   ├── frontend_engineer.py
│   ├── devops_engineer.py
│   ├── qa_engineer.py
│   ├── ux_designer.py
│   ├── security_specialist.py
│   └── human_stakeholder.py
├── orchestration/
│   ├── waterfall_controller.py
│   ├── meeting_state.py
│   └── phase_manager.py
├── prompts/
│   ├── role_prompts.py
│   └── phase_prompts.py
├── output/
│   ├── exporter.py
│   ├── templates.py
│   ├── sample_project_development_plan.md
│   └── sample_project_development_plan.json
└── logs/
```

## Setup

1. Create virtual environment and install dependencies:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:

```bash
copy .env.example .env
```

Set at least one provider key:

- Chain mode (recommended): set `MODEL_PROVIDER=openrouter`, configure `BACKUP_MODEL_PROVIDERS`, and provide keys for providers you want to use
- Local-only mode: set `MODEL_PROVIDER=ollama` and run Ollama server

Choose meeting language for all agent instructions/output style:

- `MEETING_LANGUAGE=en` (default)
- `MEETING_LANGUAGE=ru`

3. Optional: adjust model/role mapping in `project/config/model_config.yaml`.

## Run

From repository root:

```bash
cd project
python main.py
```

Minimal UI mode (separate from CLI; includes multiline response box, quick yes/no buttons, interrupt button, status bar, and timestamped transcript view):

```bash
cd project
python main_ui.py
```

## CLI Flow

1. Enter project name and initial description.
2. (Optional) Resume from checkpoint and choose the phase to continue from.
3. Facilitator orchestrates role turns per phase.
4. Human can answer clarifications.
5. Human approves/rejects phase transition.
6. CLI displays structured JSON contributions as readable bullet-style output (raw JSON remains in logs).
7. At completion/interruption, system writes:
	 - `project/output/project_development_plan_<timestamp>.md`
	 - `project/output/project_development_plan_<timestamp>.json`
	 - `project/logs/meeting_transcript_<timestamp>.log`
	 - `project/output/checkpoints/meeting_checkpoint_<project>_...json`

Use `/interrupt` when prompted as human participant to stop safely.

## Configuration

### `.env`

- `MODEL_PROVIDER`: starting provider name from `project/config/model_config.yaml` (for example: `openrouter`, `groq`, `openai`)
- `MEETING_LANGUAGE`: `en` or `ru`
- `BACKUP_MODEL_PROVIDERS`: ordered comma-separated fallback providers (example: `groq,together,mistral,fireworks,deepinfra,openai,ollama`)
- `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `TOGETHER_API_KEY`, `MISTRAL_API_KEY`, `FIREWORKS_API_KEY`, `DEEPINFRA_API_KEY`, `OPENAI_API_KEY`, `OLLAMA_API_KEY`
- `DETERMINISTIC_MODE`: `true/false`
- `TEMPERATURE`: ignored when deterministic mode is true
- `TIMEOUT_SECONDS`: per-request timeout
- `RETRY_ATTEMPTS`: retries per provider before fallback switch
- `RETRY_BACKOFF_SECONDS`: retry delay multiplier (seconds)
- `NEW_DIALOG_PER_PHASE`: reset agent dialogs on phase transition (`false` keeps one continuous conversation)
- `SMART_FORGETTING`: use phase-scoped context windows instead of long global transcript (`true/false`)
- `CONTEXT_WINDOW_TURNS`: number of recent turns kept in context window
- `PHASE_MEMORY_LIMIT`: number of prior phases to include as compressed memory
- `MAX_TURNS_PER_PHASE`: hard cap per phase
- `GLOBAL_MAX_TURNS`: hard cap for full meeting
- `OUTPUT_DIR`, `LOGS_DIR`: relative to `project/`

Recommended starting values to avoid premature cutoffs in requirements/design phases:

- `MAX_TURNS_PER_PHASE=16`
- `GLOBAL_MAX_TURNS=140`

### `project/config/model_config.yaml`

- Provider definitions (`openrouter`, `groq`, `together`, `mistral`, `fireworks`, `deepinfra`, `openai`, `ollama`)
- Base URLs and API key env names
- Role-to-model mapping
- Default runtime controls

## Provider Chain Behavior

- The runtime starts with `MODEL_PROVIDER`.
- If a request fails after configured retries, the system moves to the next provider in `BACKUP_MODEL_PROVIDERS`.
- Chain order is respected exactly as configured.
- Providers missing API keys are skipped automatically (except `ollama`, which can run locally).
- Keep `ollama` as the last fallback for offline/local resilience.

## Working with Russian reference docs

- Source references are in [project/references](project/references) (`Проект №1.docx`, `Проект №2.docx`, `Проект №3.docx`).
- Use [project/references/reference_structure_template.md](project/references/reference_structure_template.md) as AI-readable normalized structure.
- Paste converted text from your reference docs under those headings to feed context consistently.
- Final markdown output now follows a structure aligned with these reference-style sections while remaining suitable for this project.

## Notes on Model Strategy

- API-provider chain first, Ollama last-resort for local/offline fallback.
- Heavier reasoning slots are assigned to:
	- Facilitator
	- Architect
	- Security Specialist
	- Product Manager
- Lighter slots are assigned to:
	- Business Analyst
	- Dev roles
	- QA
	- UX

Model names are configurable because market offerings can change over time.

## Multilingual model options (if needed for stronger Russian quality)

If default `gpt-4.1-*` quality in Russian is insufficient for your domain text, consider these alternatives:

- Cloud candidates:
	- `gpt-4o` / `gpt-4o-mini` (strong multilingual robustness, generally good RU handling)
	- `Claude 3.5 Sonnet` / `Claude 3.7 Sonnet` (good long-form Russian reasoning/writing)
	- `Gemini 1.5 Pro` / `Gemini 2.x` (good multilingual comprehension with large context)
- Ollama/self-hosted candidates:
	- `qwen2.5:14b` or newer Qwen multilingual variants
	- `llama-3.1:8b/70b` (acceptable RU with prompt tuning)
	- `mistral-nemo` / newer Mistral multilingual models

Keep facilitator/architect/security/product on stronger models; execution roles can stay on lighter models.

## Suggested free-tier starting models by provider

- OpenRouter: `google/gemma-3-27b-it:free`, `qwen/qwen3-14b:free`, `qwen/qwen3-8b:free`, `deepseek/deepseek-r1-distill-qwen-14b:free`
- Groq: `llama-3.1-8b-instant` (usually easiest free/low-cost start), `llama-3.3-70b-versatile`
- Together: `deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free`, `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo`
- Mistral: trial credits often map best to `mistral-small-latest`
- Fireworks: trial credits with `accounts/fireworks/models/llama-v3p1-8b-instruct`
- DeepInfra: trial credits with `meta-llama/Llama-3.1-8B-Instruct`
- OpenAI: no permanent free tier; if credits exist, use `gpt-4.1-mini` / `gpt-4o-mini`
- Ollama (local fallback): `qwen3:8b`, `llama3.1:8b`

## Example Run (short)

```text
=== Waterfall Kickoff Multi-Agent Simulator ===
Project name: Retail Inventory Modernization
Initial project description: Build inventory planning and replenishment platform.

--- Phase: Requirements Gathering ---
[facilitator] { ... JSON decision ... }
[business_analyst] { ... JSON role contribution ... }
...
Approve phase 'Requirements Gathering'? [y/n]: y
...
=== Meeting completed ===
Markdown plan: ...
Structured JSON: ...
Transcript log: ...
```
