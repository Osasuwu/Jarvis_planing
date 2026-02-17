from __future__ import annotations

from prompts.phase_prompts import WATERFALL_PHASES


class PhaseManager:
    def __init__(self) -> None:
        self._phase_role_map = {
            "Requirements Gathering": {
                "product_manager",
                "business_analyst",
                "ux_designer",
                "security_specialist",
                "human_stakeholder",
            },
            "System Design": {
                "architect",
                "backend_engineer",
                "frontend_engineer",
                "devops_engineer",
                "security_specialist",
                "ux_designer",
            },
            "Implementation Planning": {
                "product_manager",
                "architect",
                "backend_engineer",
                "frontend_engineer",
                "devops_engineer",
                "qa_engineer",
            },
            "Testing Strategy": {
                "qa_engineer",
                "backend_engineer",
                "frontend_engineer",
                "security_specialist",
                "devops_engineer",
                "business_analyst",
            },
            "Deployment Planning": {
                "devops_engineer",
                "architect",
                "security_specialist",
                "qa_engineer",
                "backend_engineer",
                "frontend_engineer",
            },
            "Maintenance Strategy": {
                "product_manager",
                "business_analyst",
                "devops_engineer",
                "qa_engineer",
                "security_specialist",
                "human_stakeholder",
            },
        }

    @property
    def phases(self) -> list[str]:
        return WATERFALL_PHASES.copy()

    def is_role_allowed(self, phase: str, role: str) -> bool:
        return role in self._phase_role_map.get(phase, set())

    def fallback_role_for_phase(self, phase: str) -> str:
        allowed = self._phase_role_map.get(phase, set())
        if "business_analyst" in allowed:
            return "business_analyst"
        return sorted(allowed)[0]
