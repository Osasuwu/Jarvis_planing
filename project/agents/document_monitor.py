from agents.base_agent import BaseProjectAgent
from providers.llm_provider import LLMProvider
from prompts.role_prompts import get_role_prompt


class DocumentMonitorAgent(BaseProjectAgent):
    def __init__(self, provider: LLMProvider, language: str = "en") -> None:
        super().__init__("document_monitor", get_role_prompt("document_monitor", language), provider, language)


class DocumentFormatterAgent(DocumentMonitorAgent):
    pass
