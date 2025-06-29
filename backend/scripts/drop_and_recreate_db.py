import os
import psycopg2

DB_NAME = os.getenv('DB_NAME', 'statcast_ai')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5433')

# Connect to the default 'postgres' database
conn = psycopg2.connect(dbname='postgres', user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
conn.autocommit = True
cur = conn.cursor()

try:
    print(f"Terminating all connections to '{DB_NAME}'...")
    cur.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{DB_NAME}' AND pid <> pg_backend_pid();")
    print(f"Dropping database '{DB_NAME}' if it exists...")
    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
    print(f"Creating database '{DB_NAME}'...")
    cur.execute(f"CREATE DATABASE {DB_NAME};")
    print("Database dropped and recreated successfully.")
except Exception as e:
    print(f"[ERROR] {e}")
finally:
    cur.close()
    conn.close() 