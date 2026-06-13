"""
Database Manager using SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models.base import Base
from core.config import ConfigService


class DatabaseManager:
    def __init__(self, config_service: ConfigService = None):
        # اگر کانفیگ پاس داده نشد، یکی می‌سازیم
        self.config = config_service or ConfigService()

        db_url = self.config.db_connection_string

        self.engine = create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True
        )

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        self.Session = scoped_session(SessionLocal)

    def initialize(self):
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        return self.Session()

    def close_session(self):
        self.Session.remove()