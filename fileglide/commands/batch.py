"""Commands for executing explicit batch plans."""

from __future__ import annotations

import click

from fileglide.commands.common import pass_runtime


def create_batch_group() -> click.Group:
    """Create the batch command group."""

    @click.group("batch")
    def batch_group() -> None:
        """Validate and execute explicit JSON batch plans."""

    @batch_group.command("run")
    @click.option(
        "--dry-run/--apply",
        default=True,
        show_default=True,
        help="Preview or execute the plan.",
    )
    @click.argument("plan")
    @pass_runtime
    def run_command(runtime, dry_run, plan) -> None:
        runtime.executor.execute(
            "batch.run",
            [plan],
            lambda: runtime.facade.batch.execute_plan(
                runtime.facade.batch.load_plan(plan),
                operation_runner=runtime.facade.run_batch_step,
                preview_runner=runtime.facade.preview_batch_step,
                dry_run=dry_run,
            ),
            meta={"plan": plan, "dry_run": dry_run},
        )

    return batch_group
