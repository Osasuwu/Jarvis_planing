from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import ROLE_PROMPTS


class QAEngineerAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider) -> None:
        super().__init__("qa_engineer", ROLE_PROMPTS["qa_engineer"], provider)
