from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .engines import EngineRegistry, GameEngine
from .enums import EngineStatus
from .errors import ConfigurationError, ModelValidationError


@dataclass(slots=True)
class AppSettings:
    version: str
    engines: EngineRegistry
    instances: list[dict[str, Any]] = field(default_factory=list)
    storage: dict[str, str] = field(default_factory=dict)
    backup: dict[str, Any] = field(default_factory=dict)
    merge: dict[str, Any] = field(default_factory=dict)
    ui: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "AppSettings":
        if not isinstance(raw, dict):
            raise ConfigurationError("The settings root must be a JSON object.")
        version = raw.get("version")
        if version != "1.0":
            raise ConfigurationError(f"Unsupported settings version: {version!r}.")
        raw_engines = raw.get("game_engines", [])
        if not isinstance(raw_engines, list):
            raise ConfigurationError("'game_engines' must be an array.")

        engines: list[GameEngine] = []
        for index, item in enumerate(raw_engines):
            if not isinstance(item, dict):
                raise ConfigurationError(f"game_engines[{index}] must be a JSON object.")
            try:
                engines.append(GameEngine(
                    id=item["id"],
                    name=item["name"],
                    version=item["version"],
                    status=EngineStatus(item.get("status", "active")),
                ))
            except (KeyError, TypeError, ValueError, ModelValidationError) as exc:
                raise ConfigurationError(f"Invalid game_engines[{index}]: {exc}") from exc
        try:
            registry = EngineRegistry(engines)
        except ModelValidationError as exc:
            raise ConfigurationError(f"Invalid game engine registry: {exc}") from exc

        known = {"version", "game_engines", "instances", "storage", "backup", "merge", "ui"}
        return cls(
            version=version,
            engines=registry,
            instances=_expect_type(raw, "instances", list, []),
            storage=_expect_type(raw, "storage", dict, {}),
            backup=_expect_type(raw, "backup", dict, {}),
            merge=_expect_type(raw, "merge", dict, {}),
            ui=_expect_type(raw, "ui", dict, {}),
            extra={key: value for key, value in raw.items() if key not in known},
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "version": self.version,
            "game_engines": [
                {"id": engine.id, "name": engine.name, "version": engine.version, "status": engine.status.value}
                for engine in self.engines.all()
            ],
            "instances": self.instances,
            "storage": self.storage,
            "backup": self.backup,
            "merge": self.merge,
            "ui": self.ui,
        }
        result.update(self.extra)
        return result


def _expect_type(raw: dict[str, Any], key: str, expected: type, default: Any) -> Any:
    value = raw.get(key, default)
    if not isinstance(value, expected):
        raise ConfigurationError(f"{key!r} must be a {expected.__name__}.")
    return value


def load_settings(path: str | Path) -> AppSettings:
    settings_path = Path(path)
    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Settings file {settings_path} not found.") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Invalid JSON in {settings_path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise ConfigurationError(f"Cannot read settings file {settings_path}: {exc}") from exc
    return AppSettings.from_dict(raw)


def save_settings(settings: AppSettings, path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(settings.to_dict(), indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(destination)
    except OSError as exc:
        raise ConfigurationError(f"Cannot save settings to {destination}: {exc}") from exc
