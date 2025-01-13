from .base_repository import BaseRepository
from typing import Optional, List, Union
from sqlalchemy import select, desc, and_
from backend.src.models.interaction import Interaction
from datetime import datetime, timedelta
from ..exceptions import QueryError

class InteractionRepository(BaseRepository[Interaction]):
    def __init__(self):
        super().__init__("interactions", Interaction)

    async def find_by_user_id(self, user_id: int, limit: int = 10) -> List[Interaction]:
        try:
            query = select(self.table).where(
                self.table.c.user_id == user_id
            ).order_by(
                desc(self.table.c.created_at)  # Changed from timestamp to created_at
            ).limit(limit)
            
            async with self.db.get_session() as session:
                result = await session.execute(query)
                rows = result.fetchall()
                return self.filter_none_values([self._row_to_model(row) for row in rows])
        except Exception as e:
            raise QueryError(f"Failed to fetch interactions: {str(e)}")

    async def find_recent_by_agent(self, agent_id: str, hours: int = 24) -> List[Interaction]:
        """Get recent interactions for a specific agent"""
        try:
            time_threshold = datetime.now() - timedelta(hours=hours)
            query = select(self.table).where(
                and_(
                    self.table.c.agent_id == agent_id,
                    self.table.c.created_at >= time_threshold
                )
            ).order_by(desc(self.table.c.created_at))
            
            async with self.db.get_session() as session:
                result = await session.execute(query)
                return self.filter_none_values([self._row_to_model(row) for row in result])
        except Exception as e:
            raise QueryError(f"Failed to fetch agent interactions: {str(e)}")

    def _create_interaction_model(
        self,
        user_id: int,
        message: str,
        interaction_type: str,
        agent_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Interaction:
        now = datetime.now()
        return Interaction(
            user_id=user_id,
            content=message,
            interaction_type=interaction_type,
            agent_id=agent_id,
            data=metadata or {},  # Changed to match model field name
            created_at=now,
            updated_at=now
        )

    async def log_interaction(
        self,
        user_id: int,
        message: str,
        interaction_type: str,
        agent_id: Optional[int] = None,
        metadata: Optional[dict] = None
    ) -> Interaction:
        try:
            model = self._create_interaction_model(
                user_id=user_id,
                message=message,
                interaction_type=interaction_type,
                agent_id=str(agent_id) if agent_id is not None else None,
                metadata=metadata
            )
            return await self.create(model)
        except Exception as e:
            raise QueryError(f"Failed to log interaction: {str(e)}")
