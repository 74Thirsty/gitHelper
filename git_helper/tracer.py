"""Runtime tracing utilities leveraged by the gitHelper GUI."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class TraceEvent:
    """Immutable description of a traced function call."""

    function: str
    arg_types: List[str]
    kwarg_types: Dict[str, str]
    metadata: Dict[str, Any]


class FunctionTracer:
    """Collects lightweight runtime traces for GUI presentation."""

    def __init__(self) -> None:
        self._call_stack: List[TraceEvent] = []
        self._type_history: Dict[str, List[str]] = defaultdict(list)

    def trace_function(self, func_name: str, *args: Any, metadata: Dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Record a function invocation with basic argument type information."""

        event = TraceEvent(
            function=func_name,
            arg_types=[type(arg).__name__ for arg in args],
            kwarg_types={key: type(value).__name__ for key, value in kwargs.items()},
            metadata=dict(metadata or {}),
        )
        self._call_stack.append(event)

        for arg in args:
            self._track_nested_types(arg)
        for value in kwargs.values():
            self._track_nested_types(value)

    def _track_nested_types(self, obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                self._type_history[type(key).__name__].append(str(key))
                self._track_nested_types(value)
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                self._track_nested_types(item)
        else:
            self._type_history[type(obj).__name__].append(str(obj))

    def call_stack(self) -> Iterable[TraceEvent]:
        """Return the chronological call stack."""

        return list(self._call_stack)

    def type_usage(self) -> Dict[str, List[str]]:
        """Return collected nested type information."""

        return {key: list(values) for key, values in self._type_history.items()}

    def reset(self) -> None:
        """Clear all tracked data."""

        self._call_stack.clear()
        self._type_history.clear()


__all__ = ["FunctionTracer", "TraceEvent"]
