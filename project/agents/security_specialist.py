from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import get_role_prompt


class SecuritySpecialistAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider, language: str = "en") -> None:
        super().__init__("security_specialist", get_role_prompt("security_specialist", language), provider, language)
