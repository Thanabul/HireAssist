-- Runs once, when the PostgreSQL volume is first created. Integration tests truncate tables,
-- so they get their own database rather than sharing the one the running service uses.
CREATE DATABASE hiring_test OWNER hireassist;
