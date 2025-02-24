import os
import mysql.connector
from dotenv import load_dotenv
from contextlib import closing

# Load environment variables from .env file
load_dotenv()

MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")

def get_mysql_connection():
    """Establish a MySQL connection without specifying a database."""
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        port=MYSQL_PORT
    )

def create_database(database_name):
    """Create a MySQL database if it doesn't exist."""
    try:
        with closing(get_mysql_connection()) as conn, closing(conn.cursor()) as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
            print(f"✅ Database '{database_name}' created successfully (or already exists).")
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")

if __name__ == "__main__":
    if not MYSQL_DATABASE:
        print("❌ Error: MYSQL_DATABASE is not set in the .env file.")
    else:
        create_database(MYSQL_DATABASE)
