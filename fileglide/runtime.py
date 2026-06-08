"""Runtime state shared by click commands."""

from __future__ import annotations

from dataclasses import dataclass

from fileglide.executor import CommandExecutor
from fileglide.facade import FileGlideFacade


@dataclass(slots=True)
class RuntimeContext:
    """Store CLI-wide services and rendering preferences."""

    output_format: str = "json"
    pretty: bool = True


@dataclass(slots=True)
class RuntimeState:
    """Bundle the context, facade, and executor for click commands."""

    context: RuntimeContext
    facade: FileGlideFacade
    executor: CommandExecutor


def build_runtime(output_format: str = "json", pretty: bool = True) -> RuntimeState:
    """Create the runtime objects needed by the CLI."""

    context = RuntimeContext(output_format=output_format, pretty=pretty)
    facade = FileGlideFacade()
    executor = CommandExecutor(context)
    return RuntimeState(context=context, facade=facade, executor=executor)
