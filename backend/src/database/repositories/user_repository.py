from .base_repository import BaseRepository
from typing import Optional, List, Any
from sqlalchemy.engine.row import Row
from ...models.user import User
from sqlalchemy import select, update, insert
from datetime import datetime
from ..exceptions import QueryError

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__("users", User)

    def _row_to_model(self, row: Optional[Row]) -> Optional[User]:
        if row is None:
            return None
        return User(**dict(row))

    async def find_by_id(self, id: int) -> Optional[User]:
        query = select(self.table).where(self.table.c.id == id)
        async with self.db.get_session() as session:
            result = await session.execute(query)
            row = result.fetchone()
            return self._row_to_model(row)

    async def create(self, model: User, **kwargs) -> User:
        try:
            # Handle both dict and model input
            if not isinstance(model, (dict, User)):
                raise TypeError(f"Expected dict or User, got {type(model).__name__}")
            
            model_data = model if isinstance(model, dict) else model.__dict__
            
            data = {
                "email": model_data.get("email"),
                "name": model_data.get("name"),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            if not data["email"]:
                raise ValueError("Email is required")
                
            user_model = User(**data)
            return await super().create(user_model)
        except Exception as e:
            raise QueryError(f"Failed to create user: {str(e)}")

    async def find_by_email(self, email: str) -> Optional[User]:
        query = select(self.table).where(self.table.c.email == email)
        async with self.db.get_session() as session:
            result = await session.execute(query)
            row = result.fetchone()
            return self._row_to_model(row)

    async def update_preferences(self, user_id: int, preferences: dict) -> Optional[User]:
        stmt = (
            update(self.table)
            .where(self.table.c.id == user_id)
            .values(
                preferences=preferences,
                updated_at=datetime.now()
            )
            .returning(*self.table.c)
        )
        async with self.db.get_session() as session:
            result = await session.execute(stmt)
            row = result.fetchone()
            return self._row_to_model(row)
