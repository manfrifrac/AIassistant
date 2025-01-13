import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from backend.src.database.connection import get_connection_string

logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with the schema"""
    try:
        # Get connection string
        conn_string = get_connection_string()
        engine = create_engine(conn_string)
        
        # Read schema file
        schema_path = Path(__file__).parent / 'init_schema.sql'
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            
        # Execute schema
        with engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()
            
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

if __name__ == "__main__":
    init_database()
