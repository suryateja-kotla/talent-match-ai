import logging
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config.db_config import DB_CONFIG
from schema.pydantic_models import CandidateSchema

logger = logging.getLogger(__name__)

# ── Connection helper ────────────────────────────────────────────────────────
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# ── Database bootstrap ───────────────────────────────────────────────────────
def create_database_if_not_exists():
    db_name = DB_CONFIG["dbname"]
    config = {k: v for k, v in DB_CONFIG.items() if k != "dbname"}
    conn = psycopg2.connect(**config)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{db_name}"')
                logger.info("Database '%s' created.", db_name)
    finally:
        conn.close()

# ── DDL statements ───────────────────────────────────────────────────────────
_TRIGGER_FUNCTION = """
CREATE OR REPLACE FUNCTION update_timestamp() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END; $$ LANGUAGE plpgsql;
"""

_CANDIDATES_TABLE = """
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    linkedin_url VARCHAR(500),
    current_company VARCHAR(255),
    current_job_title VARCHAR(255),
    total_experience_years NUMERIC(5, 2) DEFAULT 0,
    skills JSONB,
    skill_experience JSONB,
    education JSONB,
    raw_text TEXT,
    source_file VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_CANDIDATES_TRIGGER = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_candidates_updated_at') THEN
        CREATE TRIGGER trg_candidates_updated_at BEFORE UPDATE ON candidates FOR EACH ROW EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
"""

_JOB_DESCRIPTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS job_descriptions (
    id SERIAL PRIMARY KEY,
    job_title VARCHAR(255) NOT NULL,
    required_skills JSONB,
    experience_years INTEGER,
    job_description TEXT,
    location VARCHAR(255),
    number_of_positions INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
 


_JOB_DESCRIPTIONS_TRIGGER = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_jobs_updated_at') THEN
        CREATE TRIGGER trg_jobs_updated_at BEFORE UPDATE ON job_descriptions FOR EACH ROW EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
"""

_APPLICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    candidate_id INT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INT NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    match_score DECIMAL(5,2),
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (candidate_id, job_id)
);
"""

_APPLICATIONS_TRIGGER = """
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_applications_updated_at') THEN
        CREATE TRIGGER trg_applications_updated_at BEFORE UPDATE ON applications FOR EACH ROW EXECUTE FUNCTION update_timestamp();
    END IF;
END $$;
"""

# ── Public entry point ───────────────────────────────────────────────────────
def init_db():
    create_database_if_not_exists()
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
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ── DB Operations (DML) ──────────────────────────────────────────────────────
from decimal import Decimal

def serialize(record: dict) -> dict:

    for key, value in record.items():
        if isinstance(value, Decimal):
            record[key] = float(value)

    for key in ("created_at", "updated_at", "applied_at", "status_updated_at"):
        if record.get(key):
            record[key] = str(record[key])

    return record

def upsert_candidate(data: CandidateSchema) -> int:
    sql = """
        INSERT INTO candidates (
            first_name, last_name, email, phone, linkedin_url,
            current_company, current_job_title, total_experience_years,
            skills, skill_experience, education, raw_text, source_file
        ) VALUES (
            %(first_name)s, %(last_name)s, %(email)s, %(phone)s, %(linkedin_url)s,
            %(current_company)s, %(current_job_title)s, %(total_experience_years)s,
            %(skills)s::jsonb, %(skill_experience)s::jsonb, %(education)s::jsonb,
            %(raw_text)s, %(source_file)s
        ) ON CONFLICT (email) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            total_experience_years = EXCLUDED.total_experience_years,
            skills = EXCLUDED.skills,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id;
    """
    if isinstance(data, dict):
       params = data
    else:
        params = data.model_dump()
    params["skills"] = json.dumps(params.get("skills",[]))
    params["skill_experience"] = json.dumps(params.get("skill_experience",{}))
    education_list=params.get("education",[])
    formatted_education = []
    for e in education_list:
        if isinstance(e, dict):
            formatted_education.append(e)
        else:
            formatted_education.append(e.model_dump())
    params["education"] = json.dumps(formatted_education)
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            c_id = cur.fetchone()[0]
        conn.commit()
        return c_id
    finally:
        conn.close()

def get_candidate_by_email(email: str) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM candidates WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            return serialize(dict(zip(cols, row)))
    finally:
        conn.close()

def list_candidates() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, first_name, last_name, email, skills, created_at FROM candidates ORDER BY created_at DESC")
            cols = [d[0] for d in cur.description]
            return [serialize(dict(zip(cols, row))) for row in cur.fetchall()]
    finally:
        conn.close()

def list_jobs() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, job_title, required_skills, experience_years,
                       location, number_of_positions, is_active, created_at,job_description
                FROM job_descriptions
                WHERE is_active = TRUE
                ORDER BY created_at DESC
            """)
            cols = [d[0] for d in cur.description]
            return [serialize(dict(zip(cols, row))) for row in cur.fetchall()]
    finally:
        conn.close()


def insert_job(job_data: dict) -> int:
    sql = """
        INSERT INTO job_descriptions (
            job_title,
            required_skills,
            experience_years,
            job_description,
            location,
            number_of_positions
        ) VALUES (
            %(job_title)s,
            %(required_skills)s,
            %(experience_years)s,
            %(job_description)s,
            %(location)s,
            %(number_of_positions)s
        ) RETURNING id;
    """
    job_data["required_skills"] = json.dumps(job_data.get("required_skills", []))

    job_data.setdefault("number_of_positions", 1)
    job_data.setdefault("job_description", "")
    job_data.setdefault("location", "")

    raw_exp = job_data.get("experience_years", 0)
    if isinstance(raw_exp, str):
        digits = ''.join(filter(str.isdigit, raw_exp))
        job_data["experience_years"] = int(digits) if digits else 0
    else:
        job_data["experience_years"] = int(raw_exp or 0)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, job_data)
            job_id = cur.fetchone()[0]
        conn.commit()
        return job_id
    finally:
        conn.close()
        
def list_jobs_by_location(location: str) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, job_title,
                       experience_years,
                       required_skills,
                       job_description,
                       location
                FROM job_descriptions
                WHERE is_active = TRUE
                AND LOWER(location) LIKE LOWER(%s)
                ORDER BY created_at DESC
            """, (f"%{location}%",))

            cols = [d[0] for d in cur.description]
            return [serialize(dict(zip(cols, row))) for row in cur.fetchall()]
    finally:
        conn.close()
    

def get_candidate_by_id(candidate_id: int) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM candidates WHERE id = %s", (candidate_id,))
            row = cur.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cur.description]
            return serialize(dict(zip(cols, row)))
    finally:
        conn.close()
        
           
def create_application(candidate_id: int, job_id: int, match_score: float):
    sql = """
        INSERT INTO applications (candidate_id, job_id, match_score)
        VALUES (%s, %s, %s)
        ON CONFLICT (candidate_id, job_id)
        DO UPDATE SET match_score = EXCLUDED.match_score
    """

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (candidate_id, job_id, match_score))
        conn.commit()
    finally:
        conn.close()
        

def list_applications_by_candidate(candidate_id: int) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    a.id,
                    a.match_score,
                    a.applied_at,
                    j.job_title,
                    j.location
                FROM applications a
                JOIN job_descriptions j ON a.job_id = j.id
                WHERE a.candidate_id = %s
                ORDER BY a.applied_at DESC
            """, (candidate_id,))

            cols = [d[0] for d in cur.description]
            return [serialize(dict(zip(cols, row))) for row in cur.fetchall()]
    finally:
        conn.close()
        

def list_all_applications() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    a.id,
                    a.match_score,
                    a.applied_at,
                    j.job_title,
                    j.location,
                    c.first_name,
                    c.last_name
                FROM applications a
                JOIN job_descriptions j ON a.job_id = j.id
                JOIN candidates c ON a.candidate_id = c.id
                ORDER BY a.applied_at DESC
            """)

            cols = [d[0] for d in cur.description]
            return [serialize(dict(zip(cols, row))) for row in cur.fetchall()]
    finally:
        conn.close()