__all__ = ["MainAgent", "SessionStateManager", "SessionStateStorage", "InMemorySessionStateStorage"]


def __getattr__(name):
    if name == "MainAgent":
        from .agent import MainAgent

        return MainAgent
    if name in {"SessionStateManager", "SessionStateStorage", "InMemorySessionStateStorage"}:
        from .session import InMemorySessionStateStorage, SessionStateManager, SessionStateStorage

        exports = {
            "SessionStateManager": SessionStateManager,
            "SessionStateStorage": SessionStateStorage,
            "InMemorySessionStateStorage": InMemorySessionStateStorage,
        }
        return exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
