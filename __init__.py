"""
AIOS - Self-Learning AI Agent Framework

A memory-driven, self-healing, production-ready AI agent system.
"""

__version__ = "0.5.0"
__author__ = "Shanhuhai"

from .core.engine import log_event, load_events
from .core.config import load as load_config
from .learning.baseline import evolution_score
from .pipeline import run_pipeline

__all__ = [
    "__version__",
    "__author__",
    "log_event",
    "load_events",
    "load_config",
    "evolution_score",
    "run_pipeline",
]


class AIOS:
    """
    Main AIOS interface for external use.

    Example:
        >>> from aios import AIOS
        >>> system = AIOS()
        >>> system.log_event("error", "network", {"code": 502})
        >>> system.run_pipeline()
    """

    def __init__(self, config_path: str = None):
        """
        Initialize AIOS system.

        Args:
            config_path: Optional path to config.yaml (defaults to workspace config)
        """
        self.config_path = config_path
        self._config = None

    @property
    def config(self):
        """Lazy load config"""
        if self._config is None:
            self._config = load_config()
        return self._config

    def log_event(self, layer: str, category: str, data: dict = None, **kwargs):
        """
        Log an event to the event stream.

        Args:
            layer: Event layer (KERNEL/COMMS/TOOL/MEM/SEC)
            category: Event category (e.g., "network", "error")
            data: Event data dictionary
            **kwargs: Additional event fields
        """
        return log_event(layer, category, data, **kwargs)

    def load_events(self, days: int = 1, layer: str = None):
        """
        Load recent events.

        Args:
            days: Number of days to load (default: 1)
            layer: Optional layer filter

        Returns:
            List of event dictionaries
        """
        return load_events(days=days, layer=layer)

    def run_pipeline(self):
        """
        Run the full AIOS pipeline:
        sensors → alerts → reactor → verifier → convergence → feedback → evolution

        Returns:
            Pipeline execution result
        """
        return run_pipeline()

    def evolution_score(self):
        """
        Get current evolution score and grade.

        Returns:
            Dict with score, grade, and metrics
        """
        return evolution_score()

    def handle_task(self, message: str, auto_create: bool = True):
        """
        Handle a complex task using multi-agent system.

        Args:
            message: Task description
            auto_create: Whether to auto-create agents if needed

        Returns:
            Task routing result
        """
        from .agent_system.dispatcher import AgentSystem

        system = AgentSystem()
        return system.handle_task(message, auto_create=auto_create)
