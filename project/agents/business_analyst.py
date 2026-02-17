from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import ROLE_PROMPTS


class BusinessAnalystAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider) -> None:
        super().__init__("business_analyst", ROLE_PROMPTS["business_analyst"], provider)
