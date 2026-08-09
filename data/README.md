# Data

Chinook sample database, MIT licence.
Source: https://github.com/lerocha/chinook-database/releases

File used: Chinook_PostgreSql_AutoIncrementPKs.sql

Two notes for anyone reloading from scratch:

1. The first three lines of the downloaded script (DROP DATABASE, CREATE DATABASE
   and the psql meta-command that switches into it) must be removed. The target
   database is created in the Neon console instead and psql connects to it directly.
2. Load it inside a single transaction so a partial load is impossible:

       docker run --rm -v "${PWD}/data:/data" --env-file .env postgres:17 \
         sh -c 'psql "$DATABASE_ADMIN_URL" -v ON_ERROR_STOP=1 --single-transaction \
         -f /data/Chinook_PostgreSql_AutoIncrementPKs.sql'

The .sql file itself is not committed. Download it and place it here.