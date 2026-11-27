-- Initial SQLite Schema for Global Data Science Salaries (2020-2022)
-- Enforces domain integrity constraints and query indexes for analytical workloads.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ds_salaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_year INTEGER NOT NULL CHECK (work_year >= 2000 AND work_year <= 2100),
    experience_level TEXT NOT NULL CHECK (experience_level IN ('EN', 'MI', 'SE', 'EX')),
    employment_type TEXT NOT NULL CHECK (employment_type IN ('PT', 'FT', 'CT', 'FL')),
    job_title TEXT NOT NULL CHECK (length(trim(job_title)) > 0),
    salary INTEGER NOT NULL CHECK (salary >= 0),
    salary_currency TEXT NOT NULL CHECK (length(trim(salary_currency)) >= 3),
    salary_in_usd INTEGER NOT NULL CHECK (salary_in_usd >= 0),
    employee_residence TEXT NOT NULL CHECK (length(trim(employee_residence)) >= 2),
    remote_ratio INTEGER NOT NULL CHECK (remote_ratio IN (0, 50, 100)),
    company_location TEXT NOT NULL CHECK (length(trim(company_location)) >= 2),
    company_size TEXT NOT NULL CHECK (company_size IN ('S', 'M', 'L'))
);

CREATE INDEX IF NOT EXISTS idx_ds_salaries_work_year ON ds_salaries (work_year);
CREATE INDEX IF NOT EXISTS idx_ds_salaries_experience_level ON ds_salaries (experience_level);
CREATE INDEX IF NOT EXISTS idx_ds_salaries_remote_ratio ON ds_salaries (remote_ratio);
CREATE INDEX IF NOT EXISTS idx_ds_salaries_job_title ON ds_salaries (job_title);
