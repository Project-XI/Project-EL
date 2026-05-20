"""
SessionPersistence — storage-interface for viva session state.

This is a thin adapter layer so that the session state manager never
couples directly to a file system or database.  Callers supply a concrete
``loader`` and ``saver`` callable when constructing a
:class:`SessionPersistence` instance, or they can use one of the ready-made
factory methods.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

Loader = Callable[[str], Dict[str, Any]]
Saver  = Callable[[str, Dict[str, Any]], Any]


# ---------------------------------------------------------------------------
# In-process defaults (not for production — no durability guarantees)
# ---------------------------------------------------------------------------

class _InMemoryStore:
    """Simple dict-of-dicts for unit tests and ephemeral sessions."""

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get(session_id)

    def set(self, session_id: str, data: Dict[str, Any]) -> None:
        self._data[session_id] = data

    def delete(self, session_id: str) -> None:
        self._data.pop(session_id, None)


_IN_MEMORY: _InMemoryStore = _InMemoryStore()


# ---------------------------------------------------------------------------
# Concrete convenience factories
# ---------------------------------------------------------------------------

def _fs_saver(base_dir: Path, session_id: str, data: Dict[str, Any]) -> Path:
    path = base_dir / f"{session_id}.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True))
    return path


def _fs_loader(base_dir: Path, session_id: str) -> Optional[Dict[str, Any]]:
    path = base_dir / f"{session_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def in_memory_persistence() -> "SessionPersistence":
    """Return a persistence backed by an in-process dictionary."""
    return SessionPersistence(loader=_IN_MEMORY.get, saver=_IN_MEMORY.set)


def file_system_persistence(base_dir: str | Path) -> "SessionPersistence":
    """
    Return a persistence backend that reads/writes ``<session_id>.json``
    files inside *base_dir*.
    """
    base = Path(base_dir).expanduser().resolve()
    base.mkdir(parents=True, exist_ok=True)
    return SessionPersistence(
        loader=lambda sid: _fs_loader(base, sid),
        saver=lambda sid, data: _fs_saver(base, sid, data),
    )


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class SessionPersistence:
    """
    Generic storage adapter.  Supply a *loader* and a *saver* at
    construction time, or use one of the factory methods above.

    Parameters
    ----------
    loader:
        Called as ``loader(session_id) -> dict | None``.  Must return the
        raw persisted data dict (or ``None`` if not found).
    saver:
        Called as ``saver(session_id, dict) -> Any``.
    """

    def __init__(self, loader: Loader, saver: Saver) -> None:
        self._loader = loader
        self._saver = saver

    # ---- Core interface -----------------------------------------------------

    def save(self, session_id: str, data: Dict[str, Any]) -> Any:
        """Persist *data* for *session_id* and return the saver's result."""
        return self._saver(session_id, data)

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load persisted data for *session_id*.  Returns ``None`` on miss."""
        return self._loader(session_id)

    def exists(self, session_id: str) -> bool:
        return self._loader(session_id) is not None

    def delete(self, session_id: str) -> bool:
        """Remove stored data for *session_id* if the backend supports it."""
        if hasattr(self._loader, "__self__") and hasattr(
            self._loader.__self__, "delete"
        ):
            self._loader.__self__.delete(session_id)
            return True
        return False

    # ---- Health check -------------------------------------------------------

    def health_check(self) -> Dict[str, Any]:
        """Return basic backend health status."""
        return {
            "type": type(self).__name__,
            "loader": repr(self._loader),
            "saver": repr(self._saver),
        }
