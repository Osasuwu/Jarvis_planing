from __future__ import annotations

from typing import Any


PHASE_ARTIFACT_SCHEMAS: dict[str, list[str]] = {
    "Requirements Gathering": [
        "functional_requirements",
        "non_functional_requirements",
        "constraints",
        "formatted_specification",
        "coverage_good",
        "coverage_gaps",
        "open_questions",
        "stakeholders",
        "success_criteria",
    ],
    "System Design": [
        "architecture_overview",
        "component_boundaries",
        "integration_strategy",
        "data_flows",
        "security_architecture",
        "design_risks",
    ],
    "Implementation Planning": [
        "work_breakdown",
        "timeline_milestones",
        "resource_plan",
        "dependency_plan",
        "raci_outline",
        "change_control",
    ],
    "Testing Strategy": [
        "test_levels",
        "acceptance_criteria",
        "quality_gates",
        "test_data_strategy",
        "defect_management",
    ],
    "Deployment Planning": [
        "environment_strategy",
        "release_strategy",
        "rollback_plan",
        "observability_plan",
        "operational_readiness",
    ],
    "Maintenance Strategy": [
        "support_model",
        "incident_response",
        "sla_slo",
        "continuous_improvement",
        "monitoring_governance",
    ],
}


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]


def _latest_by_role(contributions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for payload in contributions:
        role = str(payload.get("role", "unknown"))
        result[role] = payload
    return result


def _merge_values(*values: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _as_list(value):
            if item not in seen:
                seen.add(item)
                merged.append(item)
    return merged


def build_phase_artifact(phase_name: str, contributions: list[dict[str, Any]]) -> dict[str, Any]:
    schema_fields = PHASE_ARTIFACT_SCHEMAS.get(phase_name, [])
    latest = _latest_by_role(contributions)

    artifact: dict[str, Any] = {
        "phase": phase_name,
        "schema_fields": schema_fields,
        "contribution_count": len(contributions),
    }

    if phase_name == "Requirements Gathering":
        ba = latest.get("business_analyst", {})
        monitor = latest.get("document_monitor", latest.get("document_formatter", {}))
        pm = latest.get("product_manager", {})
        sec = latest.get("security_specialist", {})
        artifact.update(
            {
                "functional_requirements": _merge_values(ba.get("requirements")),
                "non_functional_requirements": _merge_values(
                    ba.get("non_functional_requirements"), sec.get("security_controls")
                ),
                "constraints": _merge_values(ba.get("constraints")),
                "formatted_specification": _merge_values(
                    monitor.get("formatted_specification"), monitor.get("document_sections")
                ),
                "coverage_good": _merge_values(monitor.get("coverage_good")),
                "coverage_gaps": _merge_values(monitor.get("coverage_gaps")),
                "open_questions": _merge_values(ba.get("clarifications"), pm.get("open_risks"), monitor.get("coverage_gaps")),
                "stakeholders": _merge_values(pm.get("insights")),
                "success_criteria": _merge_values(pm.get("decisions")),
            }
        )

    elif phase_name == "System Design":
        architect = latest.get("architect", {})
        backend = latest.get("backend_engineer", {})
        frontend = latest.get("frontend_engineer", {})
        devops = latest.get("devops_engineer", {})
        sec = latest.get("security_specialist", {})
        artifact.update(
            {
                "architecture_overview": _merge_values(architect.get("architecture_points")),
                "component_boundaries": _merge_values(
                    architect.get("architecture_points"), frontend.get("frontend_plan")
                ),
                "integration_strategy": _merge_values(
                    architect.get("architecture_points"), backend.get("dependencies"), devops.get("controls")
                ),
                "data_flows": _merge_values(architect.get("architecture_points"), backend.get("backend_plan")),
                "security_architecture": _merge_values(sec.get("security_controls"), sec.get("threats")),
                "design_risks": _merge_values(
                    architect.get("risks"), backend.get("risks"), frontend.get("risks"), devops.get("risks")
                ),
            }
        )

    elif phase_name == "Implementation Planning":
        backend = latest.get("backend_engineer", {})
        frontend = latest.get("frontend_engineer", {})
        devops = latest.get("devops_engineer", {})
        pm = latest.get("product_manager", {})
        artifact.update(
            {
                "work_breakdown": _merge_values(backend.get("backend_plan"), frontend.get("frontend_plan")),
                "timeline_milestones": _merge_values(pm.get("decisions")),
                "resource_plan": _merge_values(devops.get("controls"), pm.get("insights")),
                "dependency_plan": _merge_values(backend.get("dependencies"), frontend.get("dependencies")),
                "raci_outline": _merge_values(pm.get("decisions")),
                "change_control": _merge_values(devops.get("controls")),
            }
        )

    elif phase_name == "Testing Strategy":
        qa = latest.get("qa_engineer", {})
        sec = latest.get("security_specialist", {})
        artifact.update(
            {
                "test_levels": _merge_values(qa.get("test_strategy")),
                "acceptance_criteria": _merge_values(qa.get("quality_gates")),
                "quality_gates": _merge_values(qa.get("quality_gates")),
                "test_data_strategy": _merge_values(qa.get("test_strategy")),
                "defect_management": _merge_values(qa.get("risks"), sec.get("risks")),
            }
        )

    elif phase_name == "Deployment Planning":
        devops = latest.get("devops_engineer", {})
        sec = latest.get("security_specialist", {})
        artifact.update(
            {
                "environment_strategy": _merge_values(devops.get("devops_plan")),
                "release_strategy": _merge_values(devops.get("controls")),
                "rollback_plan": _merge_values(devops.get("controls"), devops.get("risks")),
                "observability_plan": _merge_values(devops.get("controls")),
                "operational_readiness": _merge_values(sec.get("security_controls"), devops.get("devops_plan")),
            }
        )

    elif phase_name == "Maintenance Strategy":
        pm = latest.get("product_manager", {})
        qa = latest.get("qa_engineer", {})
        devops = latest.get("devops_engineer", {})
        artifact.update(
            {
                "support_model": _merge_values(devops.get("devops_plan"), pm.get("insights")),
                "incident_response": _merge_values(devops.get("controls"), qa.get("quality_gates")),
                "sla_slo": _merge_values(pm.get("decisions"), qa.get("quality_gates")),
                "continuous_improvement": _merge_values(pm.get("open_risks"), qa.get("risks")),
                "monitoring_governance": _merge_values(devops.get("controls")),
            }
        )

    else:
        artifact["raw"] = contributions[-1] if contributions else {}

    for field in schema_fields:
        artifact.setdefault(field, [])
    return artifact
