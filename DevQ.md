# Development Questions (Critical Ambiguities)

Format:

`Q<number> | Area | Question | Working Assumption | Impact`

Q1 | Model Selection | Which exact low-cost/free-tier cloud models should be considered production default as of Feb 2026 for facilitator/architect/security vs lighter roles? | Use configurable defaults in `model_config.yaml` (`gpt-4.1-mini` for core reasoning, `gpt-4.1-nano` for lighter roles) and allow runtime override via config. | Affects cost/performance and quality consistency.

Q2 | AutoGen Compatibility | Which AutoGen package variant/version is target-standard in deployment (`pyautogen` API behavior for `AssistantAgent.generate_reply`)? | Implement against `pyautogen` and isolate invocation in `agents/base_agent.py` for easy adapter changes if API differs. | Affects runtime compatibility and orchestration reliability.

