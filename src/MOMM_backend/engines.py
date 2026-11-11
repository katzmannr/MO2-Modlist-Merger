"""Configured game-engine definitions and their ordered registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .enums import EngineStatus
from .errors import ModelValidationError


@dataclass(frozen=True, slots=True)
class GameEngine:
    id: str
    name: str
    version: str
    status: EngineStatus = EngineStatus.ACTIVE

    def __post_init__(self) -> None:
        for field_name in ("id", "name", "version"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ModelValidationError(f"Engine {field_name} must be a non-empty string.")
            if value != value.strip():
                raise ModelValidationError(f"Engine {field_name} cannot have surrounding whitespace.")
        try:
            object.__setattr__(self, "status", EngineStatus(self.status))
        except (TypeError, ValueError) as exc:
            raise ModelValidationError(f"Invalid engine status: {self.status!r}.") from exc

    @property
    def selectable(self) -> bool:
        return self.status is EngineStatus.ACTIVE


class EngineRegistry:
    """Ordered registry; retired definitions remain available for stored data."""

    def __init__(self, engines: Iterable[GameEngine] | None = None) -> None:
        self._engines: dict[str, GameEngine] = {}
        for engine in engines or ():
            self.add(engine)

    def add(self, engine: GameEngine) -> None:
        if not isinstance(engine, GameEngine):
            raise ModelValidationError("EngineRegistry accepts GameEngine objects only.")
        if engine.id in self._engines:
            raise ModelValidationError(f"Duplicate engine id: {engine.id!r}.")
        self._engines[engine.id] = engine

    def get(self, engine_id: str) -> GameEngine:
        try:
            return self._engines[engine_id]
        except KeyError as exc:
            raise KeyError(f"Unknown engine id: {engine_id!r}.") from exc

    def confirm(self, engine_id: str) -> GameEngine:
        current = self.get(engine_id)
        updated = GameEngine(current.id, current.name, current.version, EngineStatus.COMPATIBLE)
        self._engines[engine_id] = updated
        return updated

    def activate(self, engine_id: str) -> GameEngine:
        current = self.get(engine_id)
        updated = GameEngine(current.id, current.name, current.version, EngineStatus.ACTIVE)
        self._engines[engine_id] = updated
        return updated

    def active(self) -> tuple[GameEngine, ...]:
        return tuple(engine for engine in self._engines.values() if engine.selectable)

    def all(self) -> tuple[GameEngine, ...]:
        return tuple(self._engines.values())

    def ids(self, *, active_only: bool = False) -> tuple[str, ...]:
        selected = self.active() if active_only else self.all()
        return tuple(engine.id for engine in selected)

    def __contains__(self, engine_id: object) -> bool:
        return engine_id in self._engines

    def __iter__(self):
        return iter(self._engines.values())

    def __len__(self) -> int:
        return len(self._engines)
