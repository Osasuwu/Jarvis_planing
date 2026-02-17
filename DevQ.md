# Development Questions (Critical Ambiguities)

Format:

`Q<number> | Area | Question | Working Assumption | Impact | Answer`

Q1 | Model Selection | Which exact low-cost/free-tier cloud models should be considered production default as of Feb 2026 for facilitator/architect/security vs lighter roles? | Use configurable defaults in `model_config.yaml` (`gpt-4.1-mini` for core reasoning, `gpt-4.1-nano` for lighter roles) and allow runtime override via config. | Affects cost/performance and quality consistency | Use tiered model allocation (mini for facilitator/architect/security/PM, nano for execution roles), configurable in model_config.yaml. | STATUS: IMPLEMENTED

Q2 | AutoGen Compatibility | Which AutoGen package variant/version is target-standard in deployment (`pyautogen` API behavior for `AssistantAgent.generate_reply`)? | Implement against `pyautogen` and isolate invocation in `agents/base_agent.py` for easy adapter changes if API differs. | Affects runtime compatibility and orchestration reliability | Target latest stable pyautogen; isolate all AutoGen-specific logic inside llm_adapter.py and prevent direct API usage outside adapter. | STATUS: IMPLEMENTED

