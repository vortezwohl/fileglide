"""Batch plan loading and execution workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from fileglide.exceptions import NotFoundError, ValidationError


class BatchService:
    """Validate and execute explicit batch plans."""

    def load_plan(self, plan_path: str | Path) -> dict[str, Any]:
        """Load and validate a JSON batch plan file."""

        path = Path(plan_path)
        if not path.exists():
            raise NotFoundError(
                code="plan_missing",
                message="Batch plan does not exist.",
                details={"path": str(path)},
                path=str(path),
            )
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(raw, dict):
            raise ValidationError(
                code="invalid_plan",
                message="Batch plan root must be a JSON object.",
                details={"path": str(path)},
                path=str(path),
            )
        steps = raw.get("steps")
        if not isinstance(steps, list) or not steps:
            raise ValidationError(
                code="invalid_plan_steps",
                message="Batch plan must define a non-empty steps array.",
                details={"path": str(path)},
                path=str(path),
            )
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict) or not step.get("action"):
                raise ValidationError(
                    code="invalid_plan_step",
                    message="Each batch step must be an object with an action.",
                    details={"index": index},
                    path=str(path),
                )
        return raw

    def execute_plan(
        self,
        plan: dict[str, Any],
        *,
        operation_runner: Callable[[str, dict[str, Any]], dict[str, Any]],
        preview_runner: Callable[[str, dict[str, Any]], dict[str, Any]],
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Execute or preview a validated batch plan step by step."""

        steps = plan["steps"]
        results = []
        ok = True
        for index, step in enumerate(steps, start=1):
            action = step["action"]
            arguments = dict(step.get("arguments") or {})
            try:
                result = (
                    preview_runner(action, arguments)
                    if dry_run
                    else operation_runner(action, arguments)
                )
                step_ok = bool(result.get("ok", True))
                ok = ok and step_ok
                results.append(
                    {
                        "index": index,
                        "action": action,
                        "ok": step_ok,
                        "dry_run": dry_run,
                        "result": result,
                    }
                )
            except Exception as exc:
                ok = False
                results.append(
                    {
                        "index": index,
                        "action": action,
                        "ok": False,
                        "dry_run": dry_run,
                        "error": {
                            "code": "batch_step_failed",
                            "message": str(exc),
                            "details": {"exception_type": exc.__class__.__name__},
                        },
                    }
                )
        return {
            "ok": ok,
            "dry_run": dry_run,
            "step_count": len(steps),
            "results": results,
        }
