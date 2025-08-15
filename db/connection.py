# db/connection.py - Database Connection Manager
import os
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.Session = None
        self._connect()
        
    def _connect(self):
        """Establish database connection"""
        db_host = os.getenv('DB_HOST', 'localhost')
        db_name = os.getenv('DB_NAME', 'rqda_app')
        db_user = os.getenv('DB_USER', 'root')
        db_pass = os.getenv('DB_PASS', '')
        
        connection_string = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}?charset=utf8mb4"
        
        try:
            self.engine = create_engine(connection_string, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
        except Exception as e:
            print(f"Database connection failed: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def execute_query(self, query, params=None):
        """Execute a raw SQL query"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return result.fetchall()
    
    def execute_update(self, query, params=None):
        """Execute an update/insert/delete query"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            conn.commit()
            return result.rowcount
    
    def create_tables(self):
        """Create initial database schema"""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS files (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(255) NOT NULL,
            content TEXT,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            owner VARCHAR(100),
            memo TEXT,
            size INT DEFAULT 0,
            INDEX(name),
            INDEX(date_created)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()
