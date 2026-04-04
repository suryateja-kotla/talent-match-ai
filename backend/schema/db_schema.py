"""
schema/db_schema.py
-------------------
PostgreSQL DDL — creates all tables and triggers for ResumeIQ.

Called once at application startup (main.py → on_startup).
All statements are idempotent (IF NOT EXISTS / OR REPLACE).

Tables:
  candidates      — parsed resume data for each applicant
  job_descriptions — job requisitions created by HR
  applications    — many-to-many: candidate applied to job, with match_score
"""

import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config.db_config import DB_CONFIG

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Connection helper
# ─────────────────────────────────────────────────────────────────────────────

def get_connection():
    """Return a live psycopg2 connection using DB_CONFIG from .env."""
    return psycopg2.connect(**DB_CONFIG)


# ─────────────────────────────────────────────────────────────────────────────
# Database bootstrap
# ─────────────────────────────────────────────────────────────────────────────

def create_database_if_not_exists():
    """
    Connect to the default 'postgres' database and create
    the target DB (POSTGRES_DB) if it does not already exist.
    Must run before init_db().
    """
    db_name = DB_CONFIG["dbname"]
    config = {k: v for k, v in DB_CONFIG.items() if k != "dbname"}

    conn = psycopg2.connect(**config)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cur.fetchone():
                logger.info("Database '%s' already exists.", db_name)
            else:
                cur.execute(f'CREATE DATABASE "{db_name}"')
                logger.info("Database '%s' created.", db_name)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# DDL statements
# ─────────────────────────────────────────────────────────────────────────────

_TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

# skills          → JSONB array  : ["Python", "Docker", ...]
# skill_experience→ JSONB object : {"Python": 5.0, "Docker": 2.0}
# education       → JSONB array  : [{"degree": "...", "institution": "...", "year": "..."}]
_CANDIDATES_TABLE = """
CREATE TABLE IF NOT EXISTS candidates (
    id                      SERIAL          PRIMARY KEY,
    first_name              VARCHAR(100)    NOT NULL,
    last_name               VARCHAR(100)    NOT NULL,
    email                   VARCHAR(255)    UNIQUE NOT NULL,
    phone                   VARCHAR(20),
    linkedin_url            VARCHAR(500),
    current_company         VARCHAR(255),
    current_job_title       VARCHAR(255),
    total_experience_years  NUMERIC(5, 2)   DEFAULT 0,
    skills                  JSONB,
    skill_experience        JSONB,
    education               JSONB,
    raw_text                TEXT,
    source_file             VARCHAR(500),
    is_active               BOOLEAN         DEFAULT TRUE,
    created_at              TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);
"""

_CANDIDATES_TRIGGER = """
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_candidates_updated_at'
    ) THEN
        CREATE TRIGGER trg_candidates_updated_at
        BEFORE UPDATE ON candidates
        FOR EACH ROW EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
"""

_JOB_DESCRIPTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS job_descriptions (
    id                   SERIAL       PRIMARY KEY,
    job_title            VARCHAR(255) NOT NULL,
    job_type             VARCHAR(20)  DEFAULT 'full-time'
                             CHECK (job_type IN ('full-time','part-time','contract','internship')),
    required_skills      JSONB,
    min_experience_years INT,
    max_experience_years INT,
    job_description      TEXT,
    qualifications       TEXT,
    number_of_positions  INT          DEFAULT 1,
    is_active            BOOLEAN      DEFAULT TRUE,
    created_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
"""

_JOB_DESCRIPTIONS_TRIGGER = """
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_jobs_updated_at'
    ) THEN
        CREATE TRIGGER trg_jobs_updated_at
        BEFORE UPDATE ON job_descriptions
        FOR EACH ROW EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
"""

_APPLICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS applications (
    id                SERIAL       PRIMARY KEY,
    candidate_id      INT          NOT NULL REFERENCES candidates(id)      ON DELETE CASCADE,
    job_id            INT          NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    match_score       DECIMAL(5,2),
    applied_at        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    status_updated_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    created_at        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (candidate_id, job_id)
);
"""

_APPLICATIONS_TRIGGER = """
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_applications_updated_at'
    ) THEN
        CREATE TRIGGER trg_applications_updated_at
        BEFORE UPDATE ON applications
        FOR EACH ROW EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
"""


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    """
    Idempotently create all tables and triggers.
    Safe to call on every startup.
    """
    logger.info(
        "Initialising DB schema at %s:%s/%s",
        DB_CONFIG["host"], DB_CONFIG["port"], DB_CONFIG["dbname"],
    )
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(_TRIGGER_FUNCTION)
            cur.execute(_CANDIDATES_TABLE)
            cur.execute(_CANDIDATES_TRIGGER)
            cur.execute(_JOB_DESCRIPTIONS_TABLE)
            cur.execute(_JOB_DESCRIPTIONS_TRIGGER)
            cur.execute(_APPLICATIONS_TABLE)
            cur.execute(_APPLICATIONS_TRIGGER)
        conn.commit()
        logger.info("DB schema ready — candidates, job_descriptions, applications tables OK.")
    except Exception:
        conn.rollback()
        logger.exception("DB schema initialisation failed.")
        raise
    finally:
        conn.close()