-- Title: Init MemGPT Database

-- Fetch the environment variables.
\set db_user ${POSTGRES_USER}
\set db_password ${POSTGRES_PASSWORD}
\set db_name ${POSTGRES_DB}

CREATE USER :"db_user"
    WITH PASSWORD :'db_password'
    NOCREATEDB
    NOCREATEROLE;

CREATE DATABASE :"db_name"
    WITH
    OWNER = :"db_user"
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Set up our schema and extensions in our new database.
\c :"db_name"

CREATE SCHEMA :"db_name"
    AUTHORIZATION :"db_user";

ALTER DATABASE :"db_name"
    SET search_path TO :"db_name";

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA :"db_name";

DROP SCHEMA IF EXISTS public CASCADE;

