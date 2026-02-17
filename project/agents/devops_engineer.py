from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import ROLE_PROMPTS


class DevOpsEngineerAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider) -> None:
        super().__init__("devops_engineer", ROLE_PROMPTS["devops_engineer"], provider)
