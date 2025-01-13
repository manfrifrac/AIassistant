import sys
import os

# Determina dinamicamente la root del progetto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'C:/Users/utente/Documents/AIassistant'))
sys.path.insert(0, project_root)  # Aggiungi la root all'inizio di sys.path

import unittest
from backend.src.database.database import Database
from backend.src.database.init_db import init_database
import logging
from sqlalchemy import text



logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize database before running tests"""
        success = init_database()
        if not success:
            raise Exception("Failed to initialize database")
        cls.db = Database.get_instance()

    def test_database_connection(self):
        """Test database connection and session creation"""
        try:
            with self.db.get_session() as session:
                # Use text() to properly create an SQL expression
                result = session.execute(text("SELECT 1"))
                self.assertEqual(result.scalar(), 1)
                logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise

    def test_user_creation(self):
        """Test user table creation and insertion"""
        try:
            with self.db.get_session() as session:
                # Use text() for the SQL query and parameters for values
                insert_query = text("""
                    INSERT INTO users (name, email, password_hash)
                    VALUES (:name, :email, :password_hash)
                    RETURNING id
                """)
                result = session.execute(
                    insert_query,
                    {
                        "name": "Test User",
                        "email": "test@example.com",
                        "password_hash": "hash123"
                    }
                )
                user_id = result.scalar()
                self.assertIsNotNone(user_id)
                logger.info("User creation test successful")
        except Exception as e:
            logger.error(f"User creation test failed: {e}")
            raise

if __name__ == '__main__':
    unittest.main()
