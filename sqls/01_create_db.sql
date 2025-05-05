DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_database WHERE datname = 'todo_db'
    ) THEN
        EXECUTE 'CREATE DATABASE todo_db';
    END IF;
END
$$;
