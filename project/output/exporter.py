from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from orchestration.meeting_state import MeetingState
from output.templates import render_markdown_plan


class ProjectPlanExporter:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, state: MeetingState) -> tuple[Path, Path]:
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        md_path = self.output_dir / f"project_development_plan_{stamp}.md"
        json_path = self.output_dir / f"project_development_plan_{stamp}.json"

        md_path.write_text(render_markdown_plan(state), encoding="utf-8")
        json_path.write_text(json.dumps(state.to_json(), indent=2, ensure_ascii=False), encoding="utf-8")
        return md_path, json_path
