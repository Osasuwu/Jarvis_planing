from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import get_role_prompt


class BusinessAnalystAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider, language: str = "en") -> None:
        super().__init__("business_analyst", get_role_prompt("business_analyst", language), provider, language)
