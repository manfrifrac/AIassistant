from .base_repository import BaseRepository
from typing import Optional, List
from sqlalchemy import select, update
from ...models.session import Session
from datetime import datetime
from ..exceptions import QueryError

class SessionRepository(BaseRepository[Session]):
    def __init__(self):
        super().__init__("sessions", Session)

    async def find_active_by_user(self, user_id: int) -> List[Session]:
        try:
            query = select(self.table).where(
                self.table.c.user_id == user_id,
                self.table.c.expires_at > datetime.now()
            ).order_by(self.table.c.created_at.desc())
            
            async with self.db.get_session() as session:
                result = await session.execute(query)
                rows = result.fetchall()
                return [session for row in rows 
                       if (session := self._row_to_model(row)) is not None]
        except Exception as e:
            raise QueryError(f"Failed to fetch active sessions: {str(e)}")

    async def invalidate_session(self, session_id: int) -> bool:
        try:
            stmt = (
                update(self.table)
                .where(self.table.c.id == session_id)
                .values(
                    active=False,
                    updated_at=datetime.now(),
                    expires_at=datetime.now()
                )
            )
            async with self.db.get_session() as session:
                await session.execute(stmt)
                await session.commit()
            return True
        except Exception as e:
            raise QueryError(f"Failed to invalidate session: {str(e)}")
