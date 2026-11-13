import json
from typing import List, Optional
from sqlalchemy.types import TypeDecorator, Text
try:
    from pgvector.sqlalchemy import Vector as PGVector
except ImportError:
    PGVector = None


class VectorType(TypeDecorator):
    """
    Adaptive Vector Type that uses native pgvector.sqlalchemy.Vector on PostgreSQL
    and serializes to JSON string on SQLite / other engines.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim: int = 1536):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and PGVector is not None:
            return dialect.type_descriptor(PGVector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Optional[List[float]], dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and PGVector is not None:
            return value
        return json.dumps(value)

    def process_result_value(self, value, dialect) -> Optional[List[float]]:
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return None
        return list(value)
