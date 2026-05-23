# integration package — ORACLE → MAIN adapter layer
from .oracle_adapter import OracleAdapter
from .oracle_schema import NormalizedOracleOutput

__all__ = ["OracleAdapter", "NormalizedOracleOutput"]
