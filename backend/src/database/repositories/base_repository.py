from typing import Optional, List, Dict, Any, Generic, Type, TypeVar, cast
from sqlalchemy import insert, select, update, delete
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio import AsyncSession
from ...models.base import BaseDbModel
from ..database import Database
from ..exceptions import QueryError

T = TypeVar('T', bound=BaseDbModel)

class BaseRepository(Generic[T]):
    def __init__(self, table_name: str, model_class: Type[T]):
        self.db = Database.get_instance()
        self.model_class = model_class
        self.table = getattr(self.db, table_name)

    def _row_to_model(self, row: Optional[Row]) -> Optional[T]:
        """Convert SQLAlchemy row to model instance"""
        if row is None:
            return None
        return self.model_class(**dict(row))

    async def find_by_id(self, id: int) -> Optional[T]:
        """Find a record by ID, returns None if not found"""
        query = select(self.table).where(self.table.c.id == id)
        async with self.db.get_session() as session:
            result = await session.execute(query)
            row = result.fetchone()
            return self._row_to_model(row)

    async def create(self, model: T) -> T:
        """Create a new record, raises error if fails"""
        if not isinstance(model, self.model_class):
            raise TypeError(f"Expected {self.model_class.__name__}, got {type(model).__name__}")
            
        async with self.db.get_session() as session:
            try:
                data = model.to_dict()
                if model.id is None:
                    data.pop('id', None)
                
                stmt = insert(self.table).values(**data).returning(*self.table.c)
                result = await session.execute(stmt)
                row = result.fetchone()
                if row is None:
                    raise QueryError("Failed to create record")
                await session.commit()
                return cast(T, self._row_to_model(row))
            except Exception as e:
                await session.rollback()
                raise QueryError(f"Database error: {str(e)}")

    async def update(self, id: int, data: Dict[str, Any]) -> T:
        """Update a record, raises error if not found"""
        stmt = update(self.table).where(self.table.c.id == id).values(**data).returning(*self.table.c)
        async with self.db.get_session() as session:
            result = await session.execute(stmt)
            row = result.fetchone()
            if row is None:
                raise QueryError(f"Record {id} not found")
            return cast(T, self._row_to_model(row))

    async def delete(self, id: int) -> bool:
        stmt = delete(self.table).where(self.table.c.id == id)
        async with self.db.get_session() as session:
            result = await session.execute(stmt)
            return result.rowcount > 0

    def filter_none_values(self, items: List[Optional[T]]) -> List[T]:
        return [item for item in items if item is not None]
