from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String, DateTime, JSON, Boolean, UUID, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import asyncio
from contextlib import contextmanager, asynccontextmanager
import logging
from typing import Generator, Any, AsyncGenerator
from .connection import get_connection_string  # Corrected import path

logger = logging.getLogger(__name__)

class Database:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            # Run sync initialization in the main thread
            cls._instance._init_sync()
        return cls._instance
    
    def __init__(self):
        self._async_engine = None
        self._sync_engine = None
        self._async_session_factory = None
        self._metadata = MetaData()
        
    def _init_sync(self):
        """Initialize synchronous components"""
        conn_string = get_connection_string()
        sync_conn_string = conn_string.replace('postgresql+asyncpg', 'postgresql')
        self._sync_engine = create_engine(sync_conn_string)
        self._define_tables()
        self._create_tables_sync()
        
        # Initialize async engine
        self._async_engine = create_async_engine(conn_string)
        self._async_session_factory = async_sessionmaker(
            self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    def _define_tables(self):
        """Define table schemas"""
        # Define users table (must be first since others reference it)
        self._users = Table(
            'users',
            self._metadata,
            Column('id', UUID, primary_key=True),  # Changed to UUID
            Column('email', String, unique=True),
            Column('name', String),
            Column('preferences', JSON),
            Column('created_at', DateTime),
            Column('updated_at', DateTime)
        )
        
        # Define interactions table
        self._interactions = Table(
            'interactions', 
            self._metadata,
            Column('id', UUID, primary_key=True),  # Changed to UUID
            Column('session_id', UUID),  # Changed to UUID
            Column('type', String),
            Column('content', JSON),
            Column('timestamp', DateTime),
            Column('user_id', UUID, ForeignKey('users.id')),  # Changed to UUID
            Column('agent_id', Integer, nullable=True),
            Column('created_at', DateTime),
            Column('updated_at', DateTime)
        )
        
        # Define sessions table
        self._sessions = Table(
            'sessions',
            self._metadata,
            Column('id', UUID, primary_key=True),  # Changed to UUID
            Column('user_id', UUID, ForeignKey('users.id')),  # Changed to UUID
            Column('active', Boolean, default=True),
            Column('expires_at', DateTime),
            Column('created_at', DateTime),
            Column('updated_at', DateTime)
        )
        
        # Define memories table
        self._memories = Table(
            'memories',
            self._metadata,
            Column('id', UUID, primary_key=True),
            Column('user_id', UUID, ForeignKey('users.id')),  # Changed to UUID
            Column('content', JSON),
            Column('memory_type', String),
            Column('key', String),
            Column('value', JSON),
            Column('timestamp', DateTime),
            Column('created_at', DateTime),
            Column('updated_at', DateTime)
        )
        
        # Define agents table
        self._agents = Table(
            'agents',
            self._metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String, unique=True),
            Column('type', String),
            Column('parameters', JSON),
            Column('active', Boolean, default=True),
            Column('created_at', DateTime),
            Column('updated_at', DateTime)
        )
    
    def _create_tables_sync(self):
        """Create tables using synchronous engine"""
        if self._sync_engine is None:
            raise RuntimeError("Database engine not initialized")
        self._metadata.create_all(bind=self._sync_engine)
        
    @property
    def async_session_factory(self):
        return self._async_session_factory
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session"""
        if self._async_session_factory is None:
            self._init_sync()
        if self._async_session_factory is None:
            raise RuntimeError("Failed to initialize async session factory")
            
        session: AsyncSession = self._async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @property
    def interactions(self) -> Table:
        """Get interactions table"""
        if not hasattr(self, '_interactions'):  # Removed extra parenthesis
            self._define_tables()
        return self._interactions

    @property
    def users(self) -> Table:
        if not hasattr(self, '_users'):  # Removed extra parenthesis
            self._define_tables()
        return self._users

    @property
    def sessions(self) -> Table:
        if not hasattr(self, '_sessions'):  # Removed extra parenthesis
            self._define_tables()
        return self._sessions

    @property
    def memories(self) -> Table:
        if not hasattr(self, '_memories'):  # Removed extra parenthesis
            self._define_tables()
        return self._memories

    @property
    def agents(self) -> Table:
        if not hasattr(self, '_agents'):  # Removed extra parenthesis
            self._define_tables()
        return self._agents
