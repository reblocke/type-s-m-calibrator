"""Replace-me functional core for a focused scientific applet."""

from .contract import calculate, calculate_json
from .models import DemoRequest, DemoResponse, ValidationError
from .version import __version__

__all__ = [
    "DemoRequest",
    "DemoResponse",
    "ValidationError",
    "__version__",
    "calculate",
    "calculate_json",
]
