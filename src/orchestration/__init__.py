"""Orchestration layer for pipeline and session management."""

from .session_store import SQLiteSessionStore
from .session import SessionManager
from .pipeline import PipelineEngine
from .pipeline_config import (
    PipelineConfig,
    PipelineInput,
    PipelineSettings,
    PipelineStep,
    parse_pipeline_config,
    config_to_yaml,
)
from .plugin_manager import (
    PluginManager,
    PLUGIN_ENTRY_POINT_GROUP,
    discover,
    get_processor,
    list_processors,
)

__all__ = [
    "SQLiteSessionStore",
    "SessionManager",
    "PipelineEngine",
    "PipelineConfig",
    "PipelineInput",
    "PipelineSettings",
    "PipelineStep",
    "parse_pipeline_config",
    "config_to_yaml",
    "PluginManager",
    "PLUGIN_ENTRY_POINT_GROUP",
    "discover",
    "get_processor",
    "list_processors",
]
