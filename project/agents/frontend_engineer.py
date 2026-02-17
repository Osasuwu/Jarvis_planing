from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import ROLE_PROMPTS


class FrontendEngineerAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider) -> None:
        super().__init__("frontend_engineer", ROLE_PROMPTS["frontend_engineer"], provider)
