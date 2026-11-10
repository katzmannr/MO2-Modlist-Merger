from __future__ import annotations

from dataclasses import dataclass
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
            if not getattr(self, field_name).strip():
                raise ModelValidationError(f"Engine {field_name} entry is missing.")

    @property
    def selectable(self) -> bool:
        return self.status is EngineStatus.ACTIVE


class EngineRegistry:
    """Registry of configured engines; retired entries remain addressable."""

    def __init__(self, engines: list[GameEngine] | None = None) -> None:
        self._engines: dict[str, GameEngine] = {}
        for engine in engines or []:
            self.add(engine)

    def add(self, engine: GameEngine) -> None:
        if engine.id in self._engines:
            raise ModelValidationError(f"Duplicate engine id: {engine.id!r}")
        self._engines[engine.id] = engine

    def get(self, engine_id: str) -> GameEngine:
        try:
            return self._engines[engine_id]
        except KeyError as exc:
            raise KeyError(f"Unknown engine id: {engine_id!r}") from exc

    def active(self) -> tuple[GameEngine, ...]:
        return tuple(e for e in self._engines.values() if e.selectable)

    def all(self) -> tuple[GameEngine, ...]:
        return tuple(self._engines.values())

    def ids(self, *, active_only: bool = False) -> tuple[str, ...]:
        engines = self.active() if active_only else self.all()
        return tuple(e.id for e in engines)

    def __contains__(self, engine_id: str) -> bool:
        return engine_id in self._engines

    def __len__(self) -> int:
        return len(self._engines)
