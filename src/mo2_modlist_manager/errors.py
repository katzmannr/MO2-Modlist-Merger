class ModlistManagerError(Exception):
    """Base exception for expected application errors."""

class ConfigurationError(ModlistManagerError):
    """Settings are missing, malformed, or semantically invalid."""

class ModelValidationError(ModlistManagerError):
    """An in-memory model violates application invariants."""
