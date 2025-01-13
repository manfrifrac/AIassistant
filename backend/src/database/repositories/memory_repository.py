from .base_repository import BaseRepository
from typing import Optional, List, Union
from ...models.memory import Memory
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from uuid import UUID
from ..exceptions import QueryError

class MemoryRepository(BaseRepository[Memory]):
    def __init__(self):
        super().__init__("memories", Memory)

    async def find_by_user_id(self, user_id: int) -> List[Memory]:
        query = select(self.table).where(self.table.c.user_id == user_id)
        async with self.db.get_session() as session:
            result = await session.execute(query)
            return [Memory(**row._mapping) for row in result if row is not None]

    async def delete_memory(self, memory_id: UUID) -> None:
        async with self.db.get_session() as session:
            stmt = delete(self.table).where(self.table.c.id == str(memory_id))
            await session.execute(stmt)
            await session.commit()

    async def update_memory(self, memory: Memory) -> Memory:
        try:
            data = memory.dict(exclude={'id'} if memory.id is None else {})
            data['updated_at'] = datetime.now()
            
            stmt = insert(self.table).values(**data)
            stmt = stmt.on_conflict_do_update(
                constraint='memories_user_id_key_unique',
                set_=data
            ).returning(*self.table.c)
            
            async with self.db.get_session() as session:
                result = await session.execute(stmt)
                row = result.fetchone()
                if row is None:
                    raise QueryError("Failed to update memory")
                await session.commit()
                return Memory(**row._mapping)
        except Exception as e:
            raise QueryError(f"Failed to update memory: {str(e)}")

    async def get_by_id(self, id: Union[UUID, str]) -> Optional[Memory]:
        try:
            uuid_str = str(id) if isinstance(id, UUID) else id
            query = select(self.table).where(self.table.c.id == uuid_str)
            async with self.db.get_session() as session:
                result = await session.execute(query)
                row = result.fetchone()
                if row is None:
                    return None
                return Memory(**row._mapping)
        except ValueError as e:
            raise QueryError(f"Invalid UUID format: {str(e)}")

    async def upsert(self, memory_data: dict):
        async with self.db.get_session() as session:
            stmt = insert(self.table).values(memory_data)
            stmt = stmt.on_conflict_do_update(
                constraint='memories_pkey',
                set_=memory_data
            )
            await session.execute(stmt)
            await session.commit()
