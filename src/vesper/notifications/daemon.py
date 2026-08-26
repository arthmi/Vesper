# src/tonshell/notifications/daemon.py
from __future__ import annotations

from datetime import datetime

from gi.repository import GLib
from pydbus import SessionBus
from pydbus.generic import signal

from vesper.core.config import NotificationMode, ShellConfig


class NotificationDaemon:
    """Implementation du service DBus org.freedesktop.Notifications."""
    dbus = """
    <node>
      <interface name='org.freedesktop.Notifications'>
        <method name='Notify'>
          <arg type='s' name='app_name' direction='in'/>
          <arg type='u' name='replaces_id' direction='in'/>
          <arg type='s' name='app_icon' direction='in'/>
          <arg type='s' name='summary' direction='in'/>
          <arg type='s' name='body' direction='in'/>
          <arg type='as' name='actions' direction='in'/>
          <arg type='a{sv}' name='hints' direction='in'/>
          <arg type='i' name='expire_timeout' direction='in'/>
          <arg type='u' name='id' direction='out'/>
        </method>
        <method name='CloseNotification'>
          <arg type='u' name='id' direction='in'/>
        </method>
        <method name='GetCapabilities'>
          <arg type='as' name='capabilities' direction='out'/>
        </method>
        <method name='GetServerInformation'>
          <arg type='s' name='name' direction='out'/>
          <arg type='s' name='vendor' direction='out'/>
          <arg type='s' name='version' direction='out'/>
          <arg type='s' name='spec_version' direction='out'/>
        </method>
        <signal name='NotificationClosed'>
          <arg type='u' name='id'/>
          <arg type='u' name='reason'/>
        </signal>
        <signal name='ActionInvoked'>
          <arg type='u' name='id'/>
          <arg type='s' name='action_key'/>
        </signal>
      </interface>
    </node>
    """

    NotificationClosed = signal()
    ActionInvoked = signal()

    def __init__(self, config: ShellConfig) -> None:
        self.config = config
        self._next_id: int = 1
        self._active_notifications: dict[int, dict] = {}

    def Notify(
        self,
        app_name: str,
        replaces_id: int,
        app_icon: str,
        summary: str,
        body: str,
        actions: list[str],
        hints: dict,
        expire_timeout: int,
    ) -> int:
        if replaces_id != 0:
            notif_id = replaces_id
        else:
            notif_id = self._next_id
            self._next_id += 1
        urgency = hints.get("urgency", "normal")
        self._active_notifications[notif_id] = {
                "app_name": app_name,
                "summary": summary,
                "body": body,
                "urgency": urgency,
                "timestamp": datetime.now()
                }
        urgency_mode = self.config.notifications.mode
        match urgency_mode:
            case "classic":
                print(f"[classic] {{{urgency}}} {app_name}:\n{summary}")
            case "minimal":
                print(f"[minimal] {{{urgency}}}{app_name}:\n{summary}")
            case "dnd":
                print(f"[dnd] {{{urgency}}} {app_name}:\n{summary}")
        return notif_id

    def CloseNotification(self, id: int) -> None:
        if id not in self._active_notifications:
            #log
            return
        self._active_notifications.pop(id)
        self.NotificationClosed(id, 3)  # reason: 3 = CloseNotification

    def GetCapabilities(self) -> list[str]:
        return ["body", "actions", "persistence"]

    def GetServerInformation(self) -> tuple[str, str, str, str]:
        return ("tonshell-notifications", "tonshell", "0.1.0", "1.2")

    def run(self) -> None:
        SessionBus().publish("org.freedesktop.Notifications", self)
        GLib.MainLoop().run()

if __name__ == "__main__":
    config = ShellConfig.load()
    daemon = NotificationDaemon(config)
    daemon.run()
