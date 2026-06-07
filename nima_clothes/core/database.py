"""
Database Manager using SQLAlchemy
Handles database connections and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models.base import Base


class DatabaseManager:
    def __init__(self, db_url="sqlite:///nima_clothes.db"):
        """
        Initialize database manager
        
        Args:
            db_url: Database connection string
                - SQLite: sqlite:///nima_clothes.db
                - PostgreSQL: postgresql://user:password@localhost/nima_clothes
                - MySQL: mysql+pymysql://user:password@localhost/nima_clothes
        """
        self.engine = create_engine(
            db_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True  # Enable connection health checks
        )
        
        # Create session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Scoped session for thread safety
        self.Session = scoped_session(SessionLocal)
    
    def initialize(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def close_session(self):
        """Close the current session"""
        self.Session.remove()
