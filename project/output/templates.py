from __future__ import annotations

import json

from orchestration.meeting_state import MeetingState


def render_markdown_plan(state: MeetingState) -> str:
    phase = state.phase_states
    language = state.meeting_language

    def artifact_text(phase_name: str) -> str:
        value = phase[phase_name].artifact
        if not value:
            return "_No finalized artifact captured._" if language == "en" else "_Итоговый артефакт пока не зафиксирован._"
        return value.get("summary", str(value))

    def artifact_doc_text(phase_name: str, fallback: str) -> str:
        value = phase[phase_name].artifact
        if not value:
            return fallback
        document = value.get("document", {})
        if not document:
            return value.get("summary", fallback)
        schema_fields = document.get("schema_fields", [])
        if isinstance(schema_fields, list) and schema_fields:
            lines = []
            for field in schema_fields:
                field_value = document.get(field, [])
                if isinstance(field_value, list) and field_value:
                    lines.append(f"### {field}")
                    lines.extend(f"- {item}" for item in field_value)
                    lines.append("")
            if lines:
                return "\n".join(lines).strip()
        return f"```json\n{json.dumps(document, ensure_ascii=False, indent=2)}\n```"

    def requirements_field(field_name: str, fallback: str) -> str:
        req_artifact = phase["Requirements Gathering"].artifact
        document = req_artifact.get("document", {}) if req_artifact else {}
        field_value = document.get(field_name)
        if not field_value:
            return fallback
        if isinstance(field_value, list):
            return "\n".join(f"- {item}" for item in field_value)
        return str(field_value)

    if language == "ru":
        lines = [
            f"# План разработки проекта: {state.project_name}",
            "",
            "## 1. Введение",
            state.project_description,
            "",
            "## 2. Предназначение и ключевые цели",
            artifact_text("Requirements Gathering"),
            "",
            "## 3. Стейкхолдеры и критерии успеха",
            requirements_field("clarifications", "_Заполните список стейкхолдеров и критерии успеха._"),
            "",
            "## 4. Контекст проекта, факторы и зависимости",
            requirements_field("clarifications", "_Добавьте контекст проекта, внутренние/внешние факторы и зависимости._"),
            "",
            "## 5. Спецификация требований и рамок проекта",
            requirements_field("requirements", "_Добавьте функциональные/нефункциональные требования, ограничения и out-of-scope._")
            + "\n\n"
            + requirements_field("constraints", ""),
            "",
            "## 6. Архитектура и технологический стек",
            artifact_text("System Design"),
            "",
            "## 7. План реализации (Waterfall timeline)",
            artifact_text("Implementation Planning"),
            "",
            "## 8. Организационная структура и RACI",
            artifact_doc_text("Implementation Planning", "_Добавьте роли, зоны ответственности и матрицу RACI._"),
            "",
            "## 9. План управления ресурсами",
            artifact_doc_text("Implementation Planning", "_Добавьте ресурсный план (команда, инструменты, ограничения)._"),
            "",
            "## 10. Контроль, коммуникации и управление изменениями",
            artifact_doc_text("Implementation Planning", "_Добавьте правила контроля, коммуникации и изменения требований._"),
            "",
            "## 11. Стратегия тестирования и контроль качества",
            artifact_text("Testing Strategy"),
            "",
            "## 12. План развертывания и эксплуатации",
            artifact_text("Deployment Planning"),
            "",
            "## 13. Управление рисками и мониторинг",
            artifact_text("Maintenance Strategy"),
            "",
            "## 14. Итог и дальнейшее развитие",
            artifact_doc_text("Maintenance Strategy", "_Добавьте итоговые выводы и план улучшений._"),
            "",
        ]
        return "\n".join(lines)

    lines = [
        f"# Project Development Plan: {state.project_name}",
        "",
        "## 1. Introduction",
        state.project_description,
        "",
        "## 2. Purpose and Objectives",
        artifact_text("Requirements Gathering"),
        "",
        "## 3. Stakeholders and Success Criteria",
        requirements_field("clarifications", "_Add stakeholders and success criteria._"),
        "",
        "## 4. Project Context, Factors, and Dependencies",
        requirements_field("clarifications", "_Add project context, internal/external factors, and dependencies._"),
        "",
        "## 5. Requirements and Scope Specification",
        requirements_field("requirements", "_Add functional/non-functional requirements, constraints, and out-of-scope items._")
        + "\n\n"
        + requirements_field("constraints", ""),
        "",
        "## 6. Architecture Overview and Tech Stack",
        artifact_text("System Design"),
        "",
        "## 7. Implementation Plan (Waterfall Timeline)",
        artifact_text("Implementation Planning"),
        "",
        "## 8. Organization Structure and RACI",
        artifact_doc_text("Implementation Planning", "_Add responsibilities and RACI matrix._"),
        "",
        "## 9. Resource Management Plan",
        artifact_doc_text("Implementation Planning", "_Add team, tools, and budget/resource constraints._"),
        "",
        "## 10. Control, Communication, and Change Management",
        artifact_doc_text("Implementation Planning", "_Add control cadence, communication plan, and change process._"),
        "",
        "## 11. Testing Strategy and Quality Control",
        artifact_text("Testing Strategy"),
        "",
        "## 12. Deployment and Operations Plan",
        artifact_text("Deployment Planning"),
        "",
        "## 13. Risk Management and Monitoring",
        artifact_text("Maintenance Strategy"),
        "",
        "## 14. Final Summary and Next Steps",
        artifact_doc_text("Maintenance Strategy", "_Add conclusions and continuous-improvement roadmap._"),
        "",
    ]

    return "\n".join(lines)
