from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import get_role_prompt


class QAEngineerAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider, language: str = "en") -> None:
        super().__init__("qa_engineer", get_role_prompt("qa_engineer", language), provider, language)
