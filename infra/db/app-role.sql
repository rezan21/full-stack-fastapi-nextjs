SELECT 'CREATE ROLE app LOGIN' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app')
\gexec
ALTER ROLE app WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'password';
ALTER DATABASE app OWNER TO app;
SELECT format('ALTER TABLE %I.%I OWNER TO app', schemaname, tablename)
FROM pg_tables WHERE schemaname = 'public' AND tableowner <> 'app'
\gexec
