from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import get_role_prompt


class UXDesignerAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider, language: str = "en") -> None:
        super().__init__("ux_designer", get_role_prompt("ux_designer", language), provider, language)
