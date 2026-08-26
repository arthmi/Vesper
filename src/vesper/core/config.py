# src/tonshell/core/config.py
from __future__ import annotations

import os
import tempfile
import tomllib, tomli_w
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class PanelSide(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


class NotificationMode(str, Enum):
    CLASSIC = "classic"
    MINIMAL = "minimal"
    DND = "dnd"


class GlowGeometry(str, Enum):
    TOTAL = "total"
    PANEL_EDGE = "panel_edge"


class GlowScreenTarget(str, Enum):
    ALL = "all"
    FOCUSED = "focused"
    FIXED = "fixed"


@dataclass
class NotificationConfig:
    mode: NotificationMode = NotificationMode.CLASSIC
    glow_geometry: GlowGeometry = GlowGeometry.PANEL_EDGE
    glow_screen_target: GlowScreenTarget = GlowScreenTarget.FOCUSED_MONITOR
    glow_fixed_monitor_name: str | None = None


@dataclass
class ShellConfig:
    panel_side: PanelSide = PanelSide.RIGHT
    notifications: NotificationConfig = field(default_factory=NotificationConfig)

    @staticmethod
    def default_config_path() -> Path:
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg_config_home) if xdg_config_home else Path.home() / ".config"
        return base / "vesper" / "config.toml"

    @classmethod
    def load(cls, path: Path | None = None) -> "ShellConfig":
        if path is None:
            path = cls.default_config_path()
        path = Path(path)
        if not path.exists():
            # error message
            ...
        try:
            with open(path, "rb") as f:
                raw = tomllib.load(f)
        except FileNotFoundError, tomllib.TOMLDecodeError:
            raw ={}
            # error message

        panel_side = PanelSide(raw.get("panel_side", "top"))
        notifications = raw.get("notifications", {})

        mode = NotificationMode(notifications.get("mode", "minimal"))
        glow_geometry = GlowGeometry(notifications.get("glow_geometry", "total"))
        glow_screen_target = GlowScreenTarget(notifications.get("glow_screen_target", "focused"))
        glow_fixed_monitor_name = notifications.get("glow_fixed_monitor_name", None)

        notification_config = NotificationConfig(
            mode = mode,
            glow_geometry = glow_geometry,
            glow_screen_target = glow_screen_target,
            glow_fixed_monitor_name = glow_fixed_monitor_name
            )
        return cls(
                panel_side=panel_side,
                notifications=notification_config,
                )

    def save(self, path: Path | None = None) -> None:
        if path is None:
            path = self.default_config_path()
        path = Path(path)
        config = asdict(self)
        config["panel_side"] = config["panel_side"].value
        config["notifications"]["mode"] = config["notifications"]["mode"].value
        config["notifications"]["glow_geometry"] = config["notifications"]["glow_geometry"].value
        config["notifications"]["glow_screen_target"] = config["notifications"]["glow_screen_target"].value
        
        config = {k: v for k, v in config.items() if v is not None}   # remove all key of value None
        path.parent.mkdir(parents=True, exist_ok=True)
        output = tomli_w.dumps(config)
        print(f"saving config.toml:\n{output}")

        fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            f.write(output)

        os.replace(temp_path, path)
