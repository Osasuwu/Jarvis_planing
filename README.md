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
- Deterministic mode support (temperature override)
- Global/phase turn limits and loop prevention
- Cloud-first model strategy with Ollama fallback via config
- Full transcript logging
- Structured outputs:
	- Markdown project plan
	- JSON machine-readable plan/session data

## Project Structure

```text
project/
├── main.py
├── config/
│   ├── model_config.yaml
│   └── settings.py
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

- Cloud mode: set `OPENAI_API_KEY` and keep `MODEL_PROVIDER=cloud`
- Ollama mode: set `MODEL_PROVIDER=ollama` and run Ollama server

3. Optional: adjust model/role mapping in `project/config/model_config.yaml`.

## Run

From repository root:

```bash
cd project
python main.py
```

## CLI Flow

1. Enter project name and initial description.
2. Facilitator orchestrates role turns per phase.
3. Human can answer clarifications.
4. Human approves/rejects phase transition.
5. At completion/interruption, system writes:
	 - `project/output/project_development_plan_<timestamp>.md`
	 - `project/output/project_development_plan_<timestamp>.json`
	 - `project/logs/meeting_transcript_<timestamp>.log`

Use `/interrupt` when prompted as human participant to stop safely.

## Configuration

### `.env`

- `MODEL_PROVIDER`: `cloud` or `ollama`
- `OPENAI_API_KEY`: Cloud provider key
- `DETERMINISTIC_MODE`: `true/false`
- `TEMPERATURE`: ignored when deterministic mode is true
- `TIMEOUT_SECONDS`: per-request timeout
- `MAX_TURNS_PER_PHASE`: hard cap per phase
- `GLOBAL_MAX_TURNS`: hard cap for full meeting
- `OUTPUT_DIR`, `LOGS_DIR`: relative to `project/`

### `project/config/model_config.yaml`

- Provider definitions (`cloud`, `ollama`)
- Base URLs and API key env names
- Role-to-model mapping
- Default runtime controls

## Notes on Model Strategy

- Cloud-first for low local resource usage.
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
