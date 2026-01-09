"""Combined outside-view + inside-view runner."""

from importlib import import_module
from typing import Any

__all__ = ["run"]


def __getattr__(name: str) -> Any:
    if name == "run":
        return import_module("combined_harness.runner").run
    raise AttributeError(name)
