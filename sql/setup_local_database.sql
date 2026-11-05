-- TransitNotice local PostgreSQL setup
-- Run this file from VS Code's PostgreSQL extension while connected to the
-- default "postgres" database as the PostgreSQL administrator you created
-- during PostgreSQL installation.
--
-- Select and run the first block. Then select and run the second block.
-- If PostgreSQL reports that the database already exists, you only need to
-- run the first block once and can continue with the VS Code run task.

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'transitnotice') THEN
    CREATE ROLE transitnotice WITH LOGIN PASSWORD 'transitnotice_dev_only';
  END IF;
END
$$;

-- Run this second command only if the TransitNotice database does not yet exist.
CREATE DATABASE transitnotice OWNER transitnotice;

