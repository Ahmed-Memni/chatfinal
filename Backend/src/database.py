from sqlalchemy import create_engine, text, inspect
from langchain_community.utilities import SQLDatabase
import src.config as config
from functools import lru_cache

# -----------------------
# Engine management
# -----------------------
_engine = None

def get_engine():
    """Return a SQLAlchemy engine for current DB_URI."""
    global _engine
    if _engine is None:
        _engine = create_engine(config.DB_URI)
    return _engine

def reset_engine():
    """Clear cached engine so next call creates new one."""
    global _engine
    _engine = None

# -----------------------
# Database access
# -----------------------
def get_db():
    """Return a SQLDatabase instance using current engine."""
    return SQLDatabase(get_engine())

@lru_cache(maxsize=1)
def get_schema(_=None):
    """Return full DB schema with caching."""
    return get_full_table_info()

def clear_schema_cache():
    """Clear cached schema."""
    get_schema.cache_clear()

# -----------------------
# Fetch full table info
# -----------------------
def get_full_table_info():
    try:
        engine = get_engine()
        info_str = ""
        inspector = inspect(engine)

        with engine.connect() as conn:
            tables = inspector.get_table_names(schema='public')

            for table in tables:
                columns_info = inspector.get_columns(table, schema='public')
                columns = [col['name'] for col in columns_info]
                types = [col['type'] for col in columns_info]

                info_str += f"\nCREATE TABLE {table} (\n"
                for col_name, col_type in zip(columns, types):
                    info_str += f"    {col_name} {col_type},\n"
                info_str = info_str.rstrip(",\n") + "\n)\n\n"

                rows = conn.execute(text(f"SELECT * FROM {table};")).mappings().all()
                if not rows:
                    info_str += "/* 0 rows */\n"
                    continue

                info_str += f"/* {len(rows)} rows from {table} table: */\n"
                info_str += "\t".join([f"{c} ({t})" for c, t in zip(columns, types)]) + "\n"
                for row in rows:
                    info_str += "\t".join(str(row[c]) for c in columns) + "\n"
                info_str += "\n"

        return info_str

    except Exception as e:
        return f"Error getting full table info: {e}"

# -----------------------
# Execute query
# -----------------------
def execute_query(query: str, schema: str = "insurance") -> str:
    db = get_db()
    try:
        results = db.run(query)
        if isinstance(results, list):
            return "\n".join(
                " - ".join(str(v) for v in row.values()) if isinstance(row, dict) else str(row)
                for row in results
            )
        return str(results)
    except Exception as e:
        return f"Error executing query: {e}"
