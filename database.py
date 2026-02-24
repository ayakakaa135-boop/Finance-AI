"""
Database connection and schema for Finance AI
Compatible with Streamlit Cloud secrets
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def _build_database_url() -> str:
    """
    Build database URL with support for:
    1. Streamlit Cloud secrets (st.secrets)
    2. Environment variables (DATABASE_URL or DB_*)
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            # Option 1: Direct DATABASE_URL in secrets
            if 'DATABASE_URL' in st.secrets:
                return st.secrets['DATABASE_URL']
            
            # Option 2: Individual DB components in secrets
            if all(key in st.secrets for key in ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_NAME']):
                db_port = st.secrets.get('DB_PORT', '5432')
                return (
                    f"postgresql+psycopg2://{st.secrets['DB_USER']}:{st.secrets['DB_PASSWORD']}"
                    f"@{st.secrets['DB_HOST']}:{db_port}/{st.secrets['DB_NAME']}"
                )
    except (ImportError, AttributeError, KeyError):
        pass
    
    # Fall back to environment variables
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Build from individual environment variables
    required_vars = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"]
    missing_vars = [name for name in required_vars if not os.getenv(name)]
    
    if missing_vars:
        missing_str = ", ".join(missing_vars)
        raise ValueError(
            f"❌ Database configuration is incomplete!\n\n"
            f"In Streamlit Cloud, go to Settings → Secrets and add:\n\n"
            f"DATABASE_URL = \"postgresql://user:pass@host:5432/dbname\"\n\n"
            f"OR add these separately:\n"
            f"DB_USER = \"your_username\"\n"
            f"DB_PASSWORD = \"your_password\"\n"
            f"DB_HOST = \"your_host\"\n"
            f"DB_NAME = \"your_database\"\n"
            f"DB_PORT = \"5432\"\n\n"
            f"Missing: {missing_str}"
        )

    db_port = os.getenv("DB_PORT", "5432")
    return (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{db_port}/{os.getenv('DB_NAME')}"
    )


def get_engine():
    """Create and return a SQLAlchemy engine."""
    url = _build_database_url()
    return create_engine(url, connect_args={"sslmode": "require"})


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id              SERIAL PRIMARY KEY,
    filename        VARCHAR(255),
    doc_type        VARCHAR(50),   -- 'invoice', 'bank_statement', 'receipt'
    upload_date     TIMESTAMP DEFAULT NOW(),
    raw_text        TEXT,
    summary         TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
    id              SERIAL PRIMARY KEY,
    document_id     INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    transaction_date DATE,
    description     VARCHAR(500),
    amount          NUMERIC(12, 2),
    currency        VARCHAR(10) DEFAULT 'SEK',
    category        VARCHAR(100),
    transaction_type VARCHAR(20),  -- 'income' or 'expense'
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budgets (
    id          SERIAL PRIMARY KEY,
    category    VARCHAR(100) UNIQUE,
    monthly_limit NUMERIC(12, 2),
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE OR REPLACE VIEW monthly_summary AS
SELECT
    DATE_TRUNC('month', transaction_date) AS month,
    category,
    transaction_type,
    SUM(amount) AS total,
    COUNT(*) AS transaction_count
FROM transactions
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 4 DESC;
"""


def init_db():
    """Initialize database with schema."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(SCHEMA_SQL))
        conn.commit()
    print("✅ Database ready!")


if __name__ == "__main__":
    init_db()
