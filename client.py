from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any

SOCKET_PATH = "/tmp/maquake.sock"


class MacuakeError(Exception):
    """Raised when the Macuake API returns an error."""


@dataclass
class TabInfo:
    session_id: str
    index: int
    title: str
    active: bool
    cwd: str


@dataclass
class WindowState:
    visible: bool
    pinned: bool
    tab_count: int
    active_tab_index: int
    active_session_id: str
    width_percent: int
    height_percent: int


@dataclass
class ReadResult:
    session_id: str
    lines: list[str]
    rows: int
    cols: int


class MacuakeClient:
    """Client for the Macuake Unix domain socket API."""

    def __init__(self, socket_path: str = SOCKET_PATH) -> None:
        self.socket_path = socket_path

    def _send(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send a JSON message and return the parsed response."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(self.socket_path)
            sock.sendall(json.dumps(payload).encode())
            sock.shutdown(socket.SHUT_WR)
            chunks: list[bytes] = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
        data = json.loads(b"".join(chunks))
        if not data.get("ok"):
            raise MacuakeError(data.get("error", "unknown error"))
        return data

    # ── Window Control ───────────────────────────────────────────────

    def toggle(self) -> None:
        self._send({"action": "toggle"})

    def show(self) -> None:
        self._send({"action": "show"})

    def hide(self) -> None:
        self._send({"action": "hide"})

    def pin(self) -> None:
        self._send({"action": "pin"})

    def unpin(self) -> None:
        self._send({"action": "unpin"})

    # ── State ────────────────────────────────────────────────────────

    def state(self) -> WindowState:
        data = self._send({"action": "state"})
        return WindowState(
            visible=data["visible"],
            pinned=data["pinned"],
            tab_count=data["tab_count"],
            active_tab_index=data["active_tab_index"],
            active_session_id=data["active_session_id"],
            width_percent=data["width_percent"],
            height_percent=data["height_percent"],
        )

    def list_tabs(self) -> list[TabInfo]:
        data = self._send({"action": "list"})
        return [
            TabInfo(
                session_id=t["session_id"],
                index=t["index"],
                title=t["title"],
                active=t["active"],
                cwd=t["cwd"],
            )
            for t in data["tabs"]
        ]

    # ── Tab Management ───────────────────────────────────────────────

    def new_tab(self, directory: str | None = None) -> str:
        """Create a new tab. Returns the session_id."""
        payload: dict[str, Any] = {"action": "new-tab"}
        if directory is not None:
            payload["directory"] = directory
        data = self._send(payload)
        return data["session_id"]

    def focus(
        self,
        *,
        session_id: str | None = None,
        index: int | None = None,
    ) -> None:
        """Switch to a tab by session_id or index."""
        payload: dict[str, Any] = {"action": "focus"}
        if session_id is not None:
            payload["session_id"] = session_id
        elif index is not None:
            payload["index"] = index
        self._send(payload)

    def close_session(self, session_id: str | None = None) -> None:
        """Close a tab. Closes the active tab if no session_id given."""
        payload: dict[str, Any] = {"action": "close-session"}
        if session_id is not None:
            payload["session_id"] = session_id
        self._send(payload)

    # ── Terminal I/O ─────────────────────────────────────────────────

    def execute(self, command: str, session_id: str | None = None) -> None:
        """Send a command (appends newline)."""
        payload: dict[str, Any] = {"action": "execute", "command": command}
        if session_id is not None:
            payload["session_id"] = session_id
        self._send(payload)

    def paste(self, text: str, session_id: str | None = None) -> None:
        """Send raw text (no newline appended)."""
        payload: dict[str, Any] = {"action": "paste", "text": text}
        if session_id is not None:
            payload["session_id"] = session_id
        self._send(payload)

    def read(
        self,
        lines: int | None = None,
        session_id: str | None = None,
    ) -> ReadResult:
        """Read terminal screen content."""
        payload: dict[str, Any] = {"action": "read"}
        if lines is not None:
            payload["lines"] = lines
        if session_id is not None:
            payload["session_id"] = session_id
        data = self._send(payload)
        return ReadResult(
            session_id=data["session_id"],
            lines=data["lines"],
            rows=data["rows"],
            cols=data["cols"],
        )

    def control_char(self, key: str, session_id: str | None = None) -> None:
        """Send a control character or special key.

        Supported keys: c, d, z, a, e, k, l, u, w, enter, esc, tab.
        """
        payload: dict[str, Any] = {"action": "control-char", "key": key}
        if session_id is not None:
            payload["session_id"] = session_id
        self._send(payload)
