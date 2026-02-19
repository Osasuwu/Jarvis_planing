from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import get_role_prompt


class RiskManagerAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider, language: str = "en") -> None:
        super().__init__("risk_manager", get_role_prompt("risk_manager", language), provider, language)
