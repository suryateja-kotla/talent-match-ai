"""
schema/db_schema.py
Creates and initialises all PostgreSQL tables required by ResumeIQ.
Run this once (or at startup) to ensure tables exist.
"""

import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config.db_config import DB_CONFIG

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_connection():
    """Return a live psycopg2 connection using DB_CONFIG."""
    return psycopg2.connect(**DB_CONFIG)


def create_database_if_not_exists():
    """Create the Postgres database if it does not already exist."""
    db_name = DB_CONFIG["dbname"]
    config_without_db = {k: v for k, v in DB_CONFIG.items() if k != "dbname"}

    conn = psycopg2.connect(**config_without_db)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{db_name}"')
                logger.info("Database '%s' created.", db_name)
            else:
                logger.info("Database '%s' already exists.", db_name)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# DDL
# ─────────────────────────────────────────────────────────────────────────────

_DDL_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_DDL_CANDIDATES = """
CREATE TABLE IF NOT EXISTS candidates (
    id                      SERIAL PRIMARY KEY,
    first_name              VARCHAR(100) NOT NULL,
    last_name               VARCHAR(100) NOT NULL,
    email                   VARCHAR(255) UNIQUE NOT NULL,
    phone                   VARCHAR(20),
    linkedin_url            VARCHAR(500),
    skills                  JSONB,
    skill_experience        JSONB,
    education               JSONB,
    total_experience_years  NUMERIC(5,2) DEFAULT 0,
    current_company         VARCHAR(255),
    current_job_title       VARCHAR(255),
    raw_text                TEXT,
    source_file             VARCHAR(500),
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active               BOOLEAN DEFAULT TRUE
);
"""

_DDL_CANDIDATES_TRIGGER = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_candidates_ts'
    ) THEN
        CREATE TRIGGER trg_candidates_ts
        BEFORE UPDATE ON candidates
        FOR EACH ROW EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
"""

_DDL_JOB_DESCRIPTIONS = """
CREATE TABLE IF NOT EXISTS job_descriptions (
    id                      SERIAL PRIMARY KEY,
    job_title               VARCHAR(255) NOT NULL,
    job_type                VARCHAR(20) DEFAULT 'full-time'
                                CHECK (job_type IN ('full-time', 'part-time', 'contract', 'internship')),
    required_skills         JSONB,
    min_experience_years    INT,
    max_experience_years    INT,
    job_description         TEXT,
    qualifications          TEXT,
    number_of_positions     INT DEFAULT 1,
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active               BOOLEAN DEFAULT TRUE
);
"""

_DDL_JOB_DESCRIPTIONS_TRIGGER = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_job_descriptions_ts'
    ) THEN
        CREATE TRIGGER trg_job_descriptions_ts
        BEFORE UPDATE ON job_descriptions
        FOR EACH ROW EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
"""

_DDL_APPLICATIONS = """
CREATE TABLE IF NOT EXISTS applications (
    id                  SERIAL PRIMARY KEY,
    candidate_id        INT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id              INT NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    match_score         DECIMAL(5, 2),
    applied_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (candidate_id, job_id)
);
"""

_DDL_APPLICATIONS_TRIGGER = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_applications_ts'
    ) THEN
        CREATE TRIGGER trg_applications_ts
        BEFORE UPDATE ON applications
        FOR EACH ROW EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
"""


# ─────────────────────────────────────────────────────────────────────────────
# Public entry-point
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    """Idempotently create all tables and triggers."""
    logger.info(
        "Connecting to PostgreSQL at %s:%s, db=%s",
        DB_CONFIG["host"], DB_CONFIG["port"], DB_CONFIG["dbname"],
    )
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(_DDL_TRIGGER_FN)
            cur.execute(_DDL_CANDIDATES)
            cur.execute(_DDL_CANDIDATES_TRIGGER)
            cur.execute(_DDL_JOB_DESCRIPTIONS)
            cur.execute(_DDL_JOB_DESCRIPTIONS_TRIGGER)
            cur.execute(_DDL_APPLICATIONS)
            cur.execute(_DDL_APPLICATIONS_TRIGGER)
        conn.commit()
        logger.info("All tables and triggers are ready.")
    except Exception:
        conn.rollback()
        logger.exception("Database initialisation failed.")
        raise
    finally:
        conn.close()