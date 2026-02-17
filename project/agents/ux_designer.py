from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import ROLE_PROMPTS


class UXDesignerAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider) -> None:
        super().__init__("ux_designer", ROLE_PROMPTS["ux_designer"], provider)
